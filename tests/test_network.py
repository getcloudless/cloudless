"""
Tests for network management.
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


def run_network_test(provider, credentials):
    """
    Test network management on the given provider.
    """

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # Get somewhat unique network names
    network1 = generate_unique_name("network1")
    network2 = generate_unique_name("network2")

    # Create two private cloud networks
    network1_id = client.network.create(name=network1,
                                        blueprint=NETWORK_BLUEPRINT)["Id"]
    network2_id = client.network.create(name=network2,
                                        blueprint=NETWORK_BLUEPRINT)["Id"]
    assert network2_id != network1_id

    # Make sure we can discover them again
    assert client.network.discover(network1)["Id"] == network1_id
    assert client.network.discover(network2)["Id"] == network2_id

    # Destroy them and make sure they no longer exist
    client.network.destroy(network1)
    client.network.destroy(network2)
    assert not client.network.discover(network1)
    assert not client.network.discover(network2)


@mock_ec2
@pytest.mark.mock_aws
def test_network_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_network_test(provider="aws", credentials={})


@pytest.mark.aws
def test_network_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_network_test(provider="aws", credentials={})


@pytest.mark.gce
def test_network_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_network_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
