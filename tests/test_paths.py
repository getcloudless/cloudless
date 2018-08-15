"""
Test for path management.
"""
import os
import pytest
from moto import mock_ec2, mock_autoscaling, mock_elb, mock_route53
import butter
from butter.testutils.blueprint_tester import generate_unique_name

EXAMPLE_BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__),
                                      "..",
                                      "example-blueprints")
NETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                 "network", "blueprint.yml")
SUBNETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                    "subnetwork", "blueprint.yml")

AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                     "aws-nginx", "blueprint.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR,
                                     "gce-apache", "blueprint.yml")

def run_paths_test(provider, credentials):
    """
    Test that the path management works against the given provider.
    """

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # Get a somewhat unique network name
    network_name = generate_unique_name("unittest")

    # Provision all the resources
    client.network.create(network_name, blueprint=NETWORK_BLUEPRINT)
    if provider == "aws":
        client.instances.create(network_name, "web-lb", AWS_SERVICE_BLUEPRINT)
        client.instances.create(network_name, "web", AWS_SERVICE_BLUEPRINT)
    else:
        assert provider == "gce"
        client.instances.create(network_name, "web-lb", GCE_SERVICE_BLUEPRINT)
        client.instances.create(network_name, "web", GCE_SERVICE_BLUEPRINT)

    assert not client.paths.has_access(network_name, "web-lb", "web", 80)
    assert not client.paths.internet_accessible(network_name, "web-lb", 80)

    # Deal with networking
    client.paths.expose(network_name, "web-lb", 80)
    client.paths.add(network_name, "web-lb", "web", 80)
    client.paths.list()
    client.graph()

    assert client.paths.has_access(network_name, "web-lb", "web", 80)
    assert client.paths.internet_accessible(network_name, "web-lb", 80)

    client.paths.remove(network_name, "web-lb", "web", 80)
    assert not client.paths.has_access(network_name, "web-lb", "web", 80)

    client.instances.destroy(network_name, "web-lb")
    client.instances.destroy(network_name, "web")
    client.network.destroy(network_name)

@mock_ec2
@mock_elb
@mock_autoscaling
@mock_route53
@pytest.mark.mock_aws
def test_paths_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_paths_test(provider="aws", credentials={})

@pytest.mark.aws
def test_paths_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_paths_test(provider="aws", credentials={})

@pytest.mark.gce
def test_paths_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_paths_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
