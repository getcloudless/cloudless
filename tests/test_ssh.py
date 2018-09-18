"""
Test for temporary SSH key setup.
"""
import os
from io import StringIO
import pytest
from moto import mock_ec2, mock_autoscaling, mock_elb, mock_route53
import paramiko
import cloudless
from cloudless.types.common import Service
from cloudless.types.networking import CidrBlock
from cloudless.testutils.blueprint_tester import generate_unique_name, call_with_retries
from cloudless.testutils.ssh import generate_ssh_keypair

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
NETWORK_BLUEPRINT = os.path.join(EXAMPLES_DIR, "network", "blueprint.yml")
AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "aws_blueprint.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "gce_blueprint.yml")

# pylint: disable=too-many-locals,too-many-statements
def run_ssh_test(provider, credentials):
    """
    Test that the instance management works against the given provider.
    """

    # Get the client for this test
    client = cloudless.Client(provider, credentials)

    # Get a somewhat unique network name
    network_name = generate_unique_name("unittest")

    # Get a somewhat unique service name
    service_name = generate_unique_name("unittest")

    # Get a keypair to use
    key_pair = generate_ssh_keypair()

    # Provision all the resources
    test_network = client.network.create(network_name, blueprint=NETWORK_BLUEPRINT)
    if provider in ["aws", "mock-aws"]:
        test_service = client.service.create(test_network, service_name, AWS_SERVICE_BLUEPRINT,
                                             template_vars={"cloudless_image_build_ssh_key":
                                                            key_pair.public_key,
                                                            "cloudless_image_build_ssh_username":
                                                            "cloudless"},
                                             count=1)
    else:
        assert provider == "gce"
        test_service = client.service.create(test_network, service_name, GCE_SERVICE_BLUEPRINT,
                                             template_vars={"cloudless_image_build_ssh_key":
                                                            key_pair.public_key,
                                                            "cloudless_image_build_ssh_username":
                                                            "cloudless"},
                                             count=1)

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

    # Check that our service is provisioned properly
    validate_service(test_network, test_service, 1)

    # Add a path for SSH
    internet = CidrBlock("0.0.0.0/0")
    client.paths.add(internet, test_service, 22)

    if provider != "mock-aws":
        # Test that we can connect with the given key
        def attempt_connection():
            ssh = paramiko.SSHClient()
            ssh_key = paramiko.RSAKey(file_obj=StringIO(key_pair.private_key))
            public_ip = [i.public_ip for i in client.service.get_instances(test_service)][0]
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=public_ip, username="cloudless", pkey=ssh_key)
            return ssh
        call_with_retries(attempt_connection, int(10), float(1.0))
        ssh = attempt_connection()
        _, ssh_stdout, ssh_stderr = ssh.exec_command("whoami")
        assert ssh_stdout.read().decode().strip() == "cloudless"
        assert ssh_stderr.read().decode().strip() == ""

    # Make sure they are gone when I destroy them
    client.service.destroy(test_service)

    # Clean up the VPC
    client.network.destroy(test_network)

# Despite the fact that the mock-aws provider uses moto, we must also annotate it here since the
# test uses the AWS client directly to verify that things were created as expected.
@mock_ec2
@mock_elb
@mock_autoscaling
@mock_route53
@pytest.mark.mock_aws
def test_ssh_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_ssh_test(provider="mock-aws", credentials={})

@pytest.mark.aws
def test_ssh_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_ssh_test(provider="aws", credentials={})

@pytest.mark.gce
def test_ssh_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_ssh_test(provider="gce", credentials={
        "user_id": os.environ['CLOUDLESS_GCE_USER_ID'],
        "key": os.environ['CLOUDLESS_GCE_CREDENTIALS_PATH'],
        "project": os.environ['CLOUDLESS_GCE_PROJECT_NAME']})
