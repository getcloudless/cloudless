"""
Test for image management.
"""
import logging
import os
import pytest
import cloudless
from cloudless.types.common import Service
from cloudless.testutils.blueprint_tester import generate_unique_name

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
NETWORK_BLUEPRINT = os.path.join(EXAMPLES_DIR, "network", "blueprint.yml")
AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "aws_blueprint.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "gce_blueprint.yml")

# Set debug logging
cloudless.set_level(logging.DEBUG)

# pylint: disable=too-many-locals,too-many-statements
def run_image_test(provider, credentials):
    """
    Test that the instance management works against the given provider.
    """

    # Get the client for this test
    client = cloudless.Client(provider, credentials)

    # Get a somewhat unique network name
    network_name = generate_unique_name("unittest")
    image_name = generate_unique_name("unittest")

    # Provision a service with one instance
    test_network = client.network.create(network_name, blueprint=NETWORK_BLUEPRINT)
    if provider in ["aws", "mock-aws"]:
        service = client.service.create(test_network, "service", AWS_SERVICE_BLUEPRINT, {}, count=1)
    else:
        assert provider == "gce"
        service = client.service.create(test_network, "service", GCE_SERVICE_BLUEPRINT, {}, count=1)

    def validate_service(network, service, count):
        discovered_service = client.service.get(network, service.name)
        assert discovered_service.network == network
        assert discovered_service.name == service.name
        assert discovered_service == service
        assert isinstance(discovered_service, Service)
        assert isinstance(service, Service)
        instances = []
        for subnetwork in discovered_service.subnetworks:
            instances.extend(subnetwork.instances)
        assert len(instances) == count
        assert instances == client.service.get_instances(service)
    validate_service(test_network, service, 1)

    # Create an image from this service
    client.image.create(image_name, service)

    # List images
    images = client.image.list()
    assert images
    for image in client.image.list():
        if image.name == image_name:
            found_image = True
    assert found_image

    # Get image
    assert client.image.get(image_name)

    # Destroy image
    assert client.image.destroy(client.image.get(image_name))

    # Get image
    assert not client.image.get(image_name)
    if provider == "mock-aws":
        assert not client.image.list()

    # Clean up everything else
    client.service.destroy(service)
    client.network.destroy(test_network)

@pytest.mark.mock_aws
def test_image_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_image_test(provider="mock-aws", credentials={})

@pytest.mark.aws
def test_image_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_image_test(provider="aws", credentials={"profile": "aws-cloudless-test"})

@pytest.mark.gce
def test_image_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_image_test(provider="gce", credentials={
        "user_id": os.environ['CLOUDLESS_GCE_USER_ID'],
        "key": os.environ['CLOUDLESS_GCE_CREDENTIALS_PATH'],
        "project": os.environ['CLOUDLESS_GCE_PROJECT_NAME']})
