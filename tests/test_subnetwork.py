"""
Tests for subnetwork management.
"""
import os
import pytest
from moto import mock_ec2

import butter
from butter.testutils.blueprint_tester import generate_unique_name

EXAMPLE_BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__),
                                      "..",
                                      "example-blueprints")
NETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                 "network", "blueprint.yml")
SUBNETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                    "subnetwork", "blueprint.yml")

def run_subnetwork_test(provider, credentials):
    """
    Test subnetwork management on the given provider.
    """

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # Get a somewhat unique network name
    network_name = generate_unique_name("unittestsubnet")

    # Provision public and private networks
    client.network.create(network_name, blueprint=NETWORK_BLUEPRINT)
    public_subnets = client.subnetwork.create(network_name, "public",
                                              blueprint=SUBNETWORK_BLUEPRINT)
    # GCE doesn't do subnet based availablity zones
    if public_subnets[0]["AvailabilityZone"] == "N/A":
        expected_subnet_count = 1
    else:
        expected_subnet_count = 3
    assert len(public_subnets) == expected_subnet_count
    private_subnets = client.subnetwork.create(network_name, "private",
                                               blueprint=SUBNETWORK_BLUEPRINT)
    assert len(private_subnets) == expected_subnet_count

    # Make sure I can discover them based on service name
    assert len(client.subnetwork.discover(network_name, "public")) == expected_subnet_count
    assert len(client.subnetwork.discover(network_name, "private")) == expected_subnet_count

    # Make sure they show up when I list them
    subnet_info = client.subnetwork.list()
    assert len(subnet_info[network_name]["public"]) == expected_subnet_count
    assert len(subnet_info[network_name]["private"]) == expected_subnet_count

    # Now destroy them and make sure everything gets cleaned up
    client.subnetwork.destroy(network_name, "public")
    public_subnets = client.subnetwork.discover(network_name, "public")
    assert not public_subnets
    assert client.network.discover(network_name)

    client.subnetwork.destroy(network_name, "private")
    private_subnets = client.subnetwork.discover(network_name, "private")
    assert not private_subnets
    client.network.destroy(network_name)
    assert not client.network.discover(network_name)


@mock_ec2
@pytest.mark.mock_aws
def test_subnetwork_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_subnetwork_test(provider="aws", credentials={})

@pytest.mark.aws
def test_subnetwork_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_subnetwork_test(provider="aws", credentials={})

@pytest.mark.gce
def test_subnetwork_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_subnetwork_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
