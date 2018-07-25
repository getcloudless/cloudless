import boto3
import time
import pytest
from moto import mock_ec2, mock_autoscaling, mock_elb, mock_route53
import butter
import ipaddress
import os

# Get the blueprint locations relative to the test script
blueprints_dir = os.path.join(os.path.dirname(__file__), "blueprints")
NETWORK_BLUEPRINT = os.path.join(blueprints_dir, "network.yml")
SUBNETWORK_BLUEPRINT = os.path.join(blueprints_dir, "subnetwork.yml")

# TODO: Find a way to consolidate these.  The main issue is that the base
# images have different names in different providers.
AWS_SERVICE_BLUEPRINT = os.path.join(blueprints_dir, "service.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(blueprints_dir, "service-ubuntu.yml")

def run_paths_test(provider, credentials):

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # Provision all the resources
    client.network.create("unittest", blueprint=NETWORK_BLUEPRINT)
    if provider == "aws":
        client.instances.create("unittest", "web-lb", AWS_SERVICE_BLUEPRINT)
        client.instances.create("unittest", "web", AWS_SERVICE_BLUEPRINT)
    else:
        assert provider == "gce"
        client.instances.create("unittest", "web-lb", GCE_SERVICE_BLUEPRINT)
        client.instances.create("unittest", "web", GCE_SERVICE_BLUEPRINT)

    assert not client.paths.has_access("unittest", "web-lb", "web", 80)
    assert not client.paths.internet_accessible("unittest", "web-lb", 80)

    # Deal with networking
    client.paths.expose("unittest", "web-lb", 80)
    client.paths.add("unittest", "web-lb", "web", 80)
    client.paths.list()
    client.paths.graph()

    assert client.paths.has_access("unittest", "web-lb", "web", 80)
    assert client.paths.internet_accessible("unittest", "web-lb", 80)

    client.paths.remove("unittest", "web-lb", "web", 80)
    assert not client.paths.has_access("unittest", "web-lb", "web", 80)

    client.instances.destroy("unittest", "web-lb")
    client.instances.destroy("unittest", "web")
    client.network.destroy("unittest")

@mock_ec2
@mock_elb
@mock_autoscaling
@mock_route53
@pytest.mark.mock_aws
def test_paths_mock():
    run_paths_test(provider="aws", credentials={})

@pytest.mark.aws
def test_paths_aws():
    run_paths_test(provider="aws", credentials={})

@pytest.mark.gce
def test_paths_gce():
    run_paths_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
