"""
Tests for model management.
"""
import os
import pytest
import cloudless
from cloudless.testutils.blueprint_tester import generate_unique_name
from cloudless.types.common import Firewall, NetworkModel

EXAMPLE_BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__),
                                      "..", "examples")
NETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                 "network", "blueprint.yml")

def run_model_test(profile=None, provider=None, credentials=None):
    """
    Test model management on the given provider.
    """
    client = cloudless.Client(profile, provider, credentials)

    # Get a unique "namespace" for testing
    network_name = generate_unique_name("network")

    # Create our models
    network = NetworkModel.fromdict({"name": network_name, "version": "0.0.0"})
    firewall = Firewall.fromdict({"name": network_name, "version": "0.0.0",
                                  "network": {"name": network_name}})

    # Make sure our models are registered
    assert "Firewall" in client.model.resources()
    assert "Network" in client.model.resources()

    # Create a network and do some sanity checks
    network_create = client.model.create("Network", network)

    network_get = client.model.get("Network", network)
    assert len(network_get) == 1
    assert network_get[0] == network_create
    assert network_get[0].name == network.name

    # Create a firewall and do some sanity checks
    firewall_create = client.model.create("Firewall", firewall)

    firewall_get = client.model.get("Firewall", firewall)
    assert len(firewall_get) == 1
    assert firewall_get[0] == firewall_create
    assert firewall_get[0].name == firewall.name

    # Delete the firewall
    firewall_delete = client.model.delete("Firewall", firewall)
    assert not firewall_delete

    firewall_get = client.model.get("Firewall", firewall)
    assert not firewall_get

    # Delete the network
    network_delete = client.model.delete("Network", network)
    assert not network_delete

    network_get = client.model.get("Network", network)
    assert not network_get


@pytest.mark.mock_aws
def test_model_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_model_test(provider="mock-aws", credentials={})


# Disabling anything besides mock AWS as this API is still in flux
#@pytest.mark.aws
#def test_model_aws():
#    """
#    Run tests against real AWS (using global configuration).
#    """
#    run_model_test(profile="aws-cloudless-test")
#
#
#@pytest.mark.gce
#def test_model_gce():
#    """
#    Run tests against real GCE (environment variables below must be set).
#    """
#    run_model_test(profile="gce-cloudless-test")
