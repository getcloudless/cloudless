"""
Test for path management.
"""
import os
import pytest
import cloudless
from cloudless.types.common import Path
from cloudless.testutils.blueprint_tester import generate_unique_name

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
NETWORK_BLUEPRINT = os.path.join(EXAMPLES_DIR, "network", "blueprint.yml")
AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "aws_blueprint.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "gce_blueprint.yml")


def run_paths_test(provider, credentials):
    """
    Test that the path management works against the given provider.
    """

    # Get the client for this test
    client = cloudless.Client(provider, credentials)

    # Get a somewhat unique network name
    network_name = generate_unique_name("unittest")

    # Provision all the resources
    test_network = client.network.create(network_name, blueprint=NETWORK_BLUEPRINT)
    if provider in ["aws", "mock-aws"]:
        lb_service = client.service.create(test_network, "web-lb", AWS_SERVICE_BLUEPRINT, {})
        web_service = client.service.create(test_network, "web", AWS_SERVICE_BLUEPRINT, {})
    else:
        assert provider == "gce"
        lb_service = client.service.create(test_network, "web-lb", GCE_SERVICE_BLUEPRINT, {})
        web_service = client.service.create(test_network, "web", GCE_SERVICE_BLUEPRINT, {})

    # Create CIDR block object for the paths API
    internet = cloudless.paths.CidrBlock("0.0.0.0/0")

    assert not client.paths.has_access(lb_service, web_service, 80)
    assert not client.paths.internet_accessible(lb_service, 80)

    client.paths.add(lb_service, web_service, 80)
    client.paths.add(internet, lb_service, 80)
    for path in client.paths.list():
        assert isinstance(path, Path)
    client.graph()

    assert client.paths.has_access(lb_service, web_service, 80)
    assert client.paths.internet_accessible(lb_service, 80)

    client.paths.remove(lb_service, web_service, 80)
    assert not client.paths.has_access(lb_service, web_service, 80)

    client.paths.remove(internet, lb_service, 80)
    assert not client.paths.internet_accessible(lb_service, 80)

    client.service.destroy(lb_service)
    client.service.destroy(web_service)
    client.network.destroy(test_network)

@pytest.mark.mock_aws
def test_paths_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_paths_test(provider="mock-aws", credentials={})

@pytest.mark.aws
def test_paths_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_paths_test(provider="aws", credentials={"profile": "aws-cloudless-test"})

@pytest.mark.gce
def test_paths_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_paths_test(provider="gce", credentials={
        "user_id": os.environ['CLOUDLESS_GCE_USER_ID'],
        "key": os.environ['CLOUDLESS_GCE_CREDENTIALS_PATH'],
        "project": os.environ['CLOUDLESS_GCE_PROJECT_NAME']})
