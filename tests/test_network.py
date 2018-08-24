"""
Tests for network management.
"""
import os
import pytest

import butter
from butter.types.common import Network
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
    network1_name = generate_unique_name("network1")
    network2_name = generate_unique_name("network2")

    # Create two private cloud networks
    network1 = client.network.create(name=network1_name, blueprint=NETWORK_BLUEPRINT)
    network2 = client.network.create(name=network2_name)
    assert isinstance(network1, Network)
    assert isinstance(network2, Network)
    assert network2 != network1
    # pylint: disable=comparison-with-itself
    assert network1 == network1
    # pylint: disable=comparison-with-itself
    assert network2 == network2

    # Make sure we can discover them again
    assert client.network.get(network1_name) == network1
    assert client.network.get(network2_name) == network2

    # Destroy them and make sure they no longer exist
    client.network.destroy(network1)
    client.network.destroy(network2)
    assert not client.network.get(network1_name)
    assert not client.network.get(network2_name)


@pytest.mark.mock_aws
def test_network_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_network_test(provider="mock-aws", credentials={})


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
