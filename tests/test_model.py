"""
Tests for model management.
"""
import pytest
import cloudless
from cloudless.testutils.blueprint_tester import generate_unique_name
from cloudless.types.common import Firewall, NetworkModel, ImageModel, SubnetModel

def run_firewall_model_test(profile=None, provider=None, credentials=None):
    """
    Test model management on the given provider.
    """
    client = cloudless.Client(profile, provider, credentials)

    # Get a unique "namespace" for testing
    network_name = generate_unique_name("network")

    # Create our models
    network_dict = {"name": network_name, "version": "0.0.0"}
    network = NetworkModel.fromdict(network_dict)
    firewall = Firewall.fromdict({"name": network_name, "version": "0.0.0",
                                  "network": {"name": network.name}})

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

def run_image_model_test(profile=None, provider=None, credentials=None):
    """
    Test image model on the given provider.
    """
    client = cloudless.Client(profile, provider, credentials)

    # Create Image model
    image = ImageModel.fromdict({"name": "*ubuntu*xenial*", "version": "0.0.0",
                                 "creation_date": "latest"})

    # Make sure the image model is registered
    assert "Image" in client.model.resources()

    image_get = client.model.get("Image", image)
    assert len(image_get) == 1
    assert "ubuntu" in image_get[0].name

def run_subnet_model_test(profile=None, provider=None, credentials=None):
    """
    Test model management on the given provider.
    """
    client = cloudless.Client(profile, provider, credentials)

    # Get a unique "namespace" for testing
    network_name = generate_unique_name("network")

    # Create our models
    network_dict = {"name": network_name, "version": "0.0.0"}
    network = NetworkModel.fromdict(network_dict)
    subnet = SubnetModel.fromdict({"name": network_name, "version": "0.0.0",
                                   "network": network_dict, "size": 256})

    # Make sure our models are registered
    assert "Subnet" in client.model.resources()
    assert "Network" in client.model.resources()

    # Create a network and do some sanity checks
    network_create = client.model.create("Network", network)

    network_get = client.model.get("Network", network)
    assert len(network_get) == 1
    assert network_get[0] == network_create
    assert network_get[0].name == network.name

    # Create an subnet and do some sanity checks
    subnet_create = client.model.create("Subnet", subnet)

    subnet_get = client.model.get("Subnet", subnet)
    assert len(subnet_get) == 1
    assert subnet_get[0] == subnet_create
    assert subnet_get[0].name == subnet.name

    # Delete the subnet
    subnet_delete = client.model.delete("Subnet", subnet)
    assert not subnet_delete

    subnet_get = client.model.get("Subnet", subnet)
    assert not subnet_get

    # Delete the network
    network_delete = client.model.delete("Network", network)
    assert not network_delete

    network_get = client.model.get("Network", network)
    assert not network_get

@pytest.mark.mock_aws
def test_firewall_model_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_firewall_model_test(provider="mock-aws", credentials={})

@pytest.mark.mock_aws
def test_image_model_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_image_model_test(provider="mock-aws", credentials={})

@pytest.mark.mock_aws
def test_subnet_model_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_subnet_model_test(provider="mock-aws", credentials={})

# Disabling anything besides mock AWS as this API is still in flux
#@pytest.mark.aws
#def test_firewall_model_aws():
#    """
#    Run tests against real AWS (using global configuration).
#    """
#    run_firewall_model_test(profile="aws-cloudless-test")
#
#
#@pytest.mark.gce
#def test_firewall_model_gce():
#    """
#    Run tests against real GCE (environment variables below must be set).
#    """
#    run_firewall_model_test(profile="gce-cloudless-test")
