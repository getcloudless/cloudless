import os
import pytest
from moto import mock_ec2

import butter

EXAMPLE_BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__),
                                      "..",
                                      "example-blueprints")
NETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                 "network", "blueprint.yml")
SUBNETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                    "subnetwork", "blueprint.yml")

def run_subnetwork_test(provider, credentials):

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # Provision public and private networks
    client.network.create("unittestsubnet", blueprint=NETWORK_BLUEPRINT)
    public_subnets = client.subnetwork.create("unittestsubnet", "public",
                                              blueprint=SUBNETWORK_BLUEPRINT)
    # GCE doesn't do subnet based availablity zones
    if public_subnets[0]["AvailabilityZone"] == "N/A":
        expected_subnet_count = 1
    else:
        expected_subnet_count = 3
    assert len(public_subnets) == expected_subnet_count
    private_subnets = client.subnetwork.create("unittestsubnet", "private",
                                               blueprint=SUBNETWORK_BLUEPRINT)
    assert len(private_subnets) == expected_subnet_count

    # Make sure I can discover them based on service name
    assert len(client.subnetwork.discover("unittestsubnet", "public")) == expected_subnet_count
    assert len(client.subnetwork.discover("unittestsubnet", "private")) == expected_subnet_count

    # Make sure they show up when I list them
    subnet_info = client.subnetwork.list()
    assert len(subnet_info["unittestsubnet"]["public"]) == expected_subnet_count
    assert len(subnet_info["unittestsubnet"]["private"]) == expected_subnet_count

    # Now destroy them and make sure everything gets cleaned up
    client.subnetwork.destroy("unittestsubnet", "public")
    public_subnets = client.subnetwork.discover("unittestsubnet", "public")
    assert not public_subnets
    assert client.network.discover("unittestsubnet")

    client.subnetwork.destroy("unittestsubnet", "private")
    private_subnets = client.subnetwork.discover("unittestsubnet", "private")
    assert not private_subnets
    client.network.destroy("unittestsubnet")
    assert not client.network.discover("unittestsubnet")


@mock_ec2
@pytest.mark.mock_aws
def test_subnetwork_mock():
    run_subnetwork_test(provider="aws", credentials={})

@pytest.mark.aws
def test_subnetwork_aws():
    run_subnetwork_test(provider="aws", credentials={})

@pytest.mark.gce
def test_subnetwork_gce():
    run_subnetwork_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
