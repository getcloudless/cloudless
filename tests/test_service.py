"""
Test for instance management.
"""
import logging
import ipaddress
import os
import pytest
import boto3
from moto import mock_ec2, mock_autoscaling, mock_elb, mock_route53
import cloudless
from cloudless.types.common import Service
from cloudless.testutils.blueprint_tester import generate_unique_name

EXAMPLE_BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "..", "example-blueprints")
NETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR, "network", "blueprint.yml")
AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR, "aws-nginx", "blueprint.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR, "gce-apache", "blueprint.yml")

# Set debug logging
cloudless.set_level(logging.DEBUG)

# pylint: disable=too-many-locals,too-many-statements
def run_instances_test(provider, credentials):
    """
    Test that the instance management works against the given provider.
    """

    # Get the client for this test
    client = cloudless.Client(provider, credentials)

    # Get a somewhat unique network name
    network_name = generate_unique_name("unittest")

    # Provision all the resources
    test_network = client.network.create(network_name, blueprint=NETWORK_BLUEPRINT)
    if provider in ["aws", "mock-aws"]:
        lb_service = client.service.create(test_network, "web-lb", AWS_SERVICE_BLUEPRINT, {})
        web_service = client.service.create(test_network, "web", AWS_SERVICE_BLUEPRINT, {}, count=6)
    else:
        assert provider == "gce"
        lb_service = client.service.create(test_network, "web-lb", GCE_SERVICE_BLUEPRINT, {})
        web_service = client.service.create(test_network, "web", GCE_SERVICE_BLUEPRINT, {}, count=6)

    def validate_service(network, service, count):
        discovered_service = client.service.get(network, service.name)
        assert discovered_service.network == network
        assert discovered_service.name == service.name
        assert discovered_service == service
        assert isinstance(discovered_service, Service)
        assert isinstance(service, Service)
        instances = []
        for subnetwork in discovered_service.subnetworks:
            assert subnetwork.instances
            instances.extend(subnetwork.instances)
        assert len(instances) == count
        assert instances == client.service.get_instances(service)

    validate_service(test_network, lb_service, 3)
    validate_service(test_network, web_service, 6)

    if provider in ["aws", "mock-aws"]:
        # Networking
        ec2 = boto3.client("ec2")
        dc_id = client.network.get(network_name).network_id
        subnets = ec2.describe_subnets(Filters=[{
            'Name': 'vpc-id',
            'Values': [dc_id]}])
        route_tables = ec2.describe_route_tables(Filters=[{
            'Name': 'vpc-id',
            'Values': [dc_id]}])
        assert len(route_tables["RouteTables"]) == 7
        assert len(subnets["Subnets"]) == 6

        # AutoScalingGroup
        autoscaling = boto3.client("autoscaling")
        web_asgs = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=["%s.web" % network_name])
        assert len(web_asgs["AutoScalingGroups"]) == 1
        web_asg = web_asgs["AutoScalingGroups"][0]
        assert web_asg["AutoScalingGroupName"] == "%s.web" % network_name
        assert web_asg["LaunchConfigurationName"] == "%s.web" % network_name
        web_lb_asgs = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=["%s.web-lb" % network_name])
        assert len(web_lb_asgs["AutoScalingGroups"]) == 1
        web_lb_asg = web_lb_asgs["AutoScalingGroups"][0]
        assert web_lb_asg["AutoScalingGroupName"] == "%s.web-lb" % network_name
        assert web_lb_asg["LaunchConfigurationName"] == "%s.web-lb" % network_name

        # Make sure subnets don't overlap
        web_asg = web_asgs["AutoScalingGroups"][0]
        web_asg_subnet_ids = web_asg["VPCZoneIdentifier"].split(",")
        assert len(web_asg_subnet_ids) == 3

        web_lb_asg = web_lb_asgs["AutoScalingGroups"][0]
        web_lb_asg_subnet_ids = web_lb_asg["VPCZoneIdentifier"].split(",")
        assert len(web_lb_asg_subnet_ids) == 3

        web_asg_subnets = ec2.describe_subnets(SubnetIds=web_asg_subnet_ids)
        assert len(web_asg_subnets["Subnets"]) == 3

        web_lb_asg_subnets = ec2.describe_subnets(SubnetIds=web_lb_asg_subnet_ids)
        assert len(web_lb_asg_subnets["Subnets"]) == 3

        for web_asg_subnet in web_asg_subnets["Subnets"]:
            web_asg_cidr = ipaddress.ip_network(str(web_asg_subnet["CidrBlock"]))
            for web_lb_asg_subnet in web_lb_asg_subnets["Subnets"]:
                web_lb_asg_cidr = ipaddress.ip_network(
                    str(web_lb_asg_subnet["CidrBlock"]))
                assert not web_asg_cidr.overlaps(web_lb_asg_cidr)

        # Make sure they got allocated in the same VPC
        web_asg_vpc_id = None
        for web_asg_subnet in web_asg_subnets["Subnets"]:
            if not web_asg_vpc_id:
                web_asg_vpc_id = web_asg_subnet["VpcId"]
            assert web_asg_subnet["VpcId"] == web_asg_vpc_id

        web_lb_asg_vpc_id = None
        for web_lb_asg_subnet in web_lb_asg_subnets["Subnets"]:
            if not web_lb_asg_vpc_id:
                web_lb_asg_vpc_id = web_lb_asg_subnet["VpcId"]
            assert web_lb_asg_subnet["VpcId"] == web_lb_asg_vpc_id

        assert web_asg_vpc_id == web_lb_asg_vpc_id

    # Make sure they are gone when I destroy them
    client.service.destroy(lb_service)

    if provider in ["aws", "mock-aws"]:
        # Networking
        ec2 = boto3.client("ec2")
        subnets = ec2.describe_subnets(Filters=[{
            'Name': 'vpc-id',
            'Values': [dc_id]}])
        route_tables = ec2.describe_route_tables(Filters=[{
            'Name': 'vpc-id',
            'Values': [dc_id]}])
        assert len(route_tables["RouteTables"]) == 4
        assert len(subnets["Subnets"]) == 3

        # AutoScalingGroup
        autoscaling = boto3.client("autoscaling")
        asgs = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=["%s.web" % network_name])
        assert len(asgs["AutoScalingGroups"]) == 1
        asg = asgs["AutoScalingGroups"][0]
        assert asg["AutoScalingGroupName"] == "%s.web" % network_name
        assert asg["LaunchConfigurationName"] == "%s.web" % network_name

    # Now destroy the rest
    client.service.destroy(web_service)

    if provider in ["aws", "mock-aws"]:
        # AutoScalingGroups
        autoscaling = boto3.client("autoscaling")
        asgs = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=["%s.web" % network_name])
        assert not asgs["AutoScalingGroups"]
        asgs = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=["%s.web-lb" % network_name])
        assert not asgs["AutoScalingGroups"]

    # Clean up the VPC
    client.network.destroy(test_network)

# Despite the fact that the mock-aws provider uses moto, we must also annotate it here since the
# test uses the AWS client directly to verify that things were created as expected.
@mock_ec2
@mock_elb
@mock_autoscaling
@mock_route53
@pytest.mark.mock_aws
def test_instances_mock():
    """
    Run tests using the mock aws driver (moto).
    """
    run_instances_test(provider="mock-aws", credentials={})

@pytest.mark.aws
def test_instances_aws():
    """
    Run tests against real AWS (using global configuration).
    """
    run_instances_test(provider="aws", credentials={})

@pytest.mark.gce
def test_instances_gce():
    """
    Run tests against real GCE (environment variables below must be set).
    """
    run_instances_test(provider="gce", credentials={
        "user_id": os.environ['CLOUDLESS_GCE_USER_ID'],
        "key": os.environ['CLOUDLESS_GCE_CREDENTIALS_PATH'],
        "project": os.environ['CLOUDLESS_GCE_PROJECT_NAME']})
