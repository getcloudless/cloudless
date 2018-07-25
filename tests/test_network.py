import pytest
from moto import mock_ec2

import butter
import ipaddress
import os

# Get the blueprint locations relative to the test script
blueprints_dir = os.path.join(os.path.dirname(__file__), "blueprints")
NETWORK_BLUEPRINT = os.path.join(blueprints_dir, "network.yml")


def run_network_test(provider, credentials):

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # Create two private cloud networks
    original_count = len(client.network.list()["Named"])
    network1_id = client.network.create(name="network1",
                                        blueprint=NETWORK_BLUEPRINT)["Id"]
    assert len(client.network.list()["Named"]) == original_count + 1
    # TODO: this is an AWS specific concept, figure out a more generic way to
    # deal with this.
    inventories = [butter.providers.aws.inventory.native]
    network2_id = client.network.create(name="network2",
                                        blueprint=NETWORK_BLUEPRINT,
                                        inventories=inventories
                                        )["Id"]
    assert len(client.network.list()["Named"]) == original_count + 2
    assert network2_id != network1_id

    # Make sure we can discover them again
    assert client.network.discover("network1")["Id"] == network1_id
    assert client.network.discover("network2")["Id"] == network2_id

    # Make sure the CIDR blocks do not overlap
    network1_cidr_raw = client.network.discover("network1")["CidrBlock"]
    network2_cidr_raw = client.network.discover("network2")["CidrBlock"]
    # Skip this if the CIDR blocks are "N/A", since google compute does not
    # have the concept of CIDRs for VPCs.
    if network1_cidr_raw == "N/A":
        assert network2_cidr_raw == "N/A"
    else:
        network1_cidr = ipaddress.ip_network(str(network1_cidr_raw))
        network2_cidr = ipaddress.ip_network(str(network2_cidr_raw))
        assert not network1_cidr.overlaps(network2_cidr)

    # Destroy them and make sure they no longer exist
    client.network.destroy("network1")
    assert len(client.network.list()["Named"]) == original_count + 1
    client.network.destroy("network2")
    assert len(client.network.list()["Named"]) == original_count + 0
    assert not client.network.discover("network1")
    assert not client.network.discover("network2")


@mock_ec2
@pytest.mark.mock_aws
def test_network_mock():
    run_network_test(provider="aws", credentials={})


@pytest.mark.aws
def test_network_aws():
    run_network_test(provider="aws", credentials={})


@pytest.mark.gce
def test_network_gce():
    run_network_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
