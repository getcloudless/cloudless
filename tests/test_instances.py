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

def run_instances_test(provider, credentials):

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

    # Wait for at least one instance to start provisioning in each group
    while len(client.instances.discover("unittest", "web-lb")["Instances"]) == 0:
        time.sleep(1)
    while len(client.instances.discover("unittest", "web")["Instances"]) == 0:
        time.sleep(1)

    if provider == "aws":
        # Networking
        ec2 = boto3.client("ec2")
        dc_id = client.network.discover("unittest")["Id"]
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
                AutoScalingGroupNames=["unittest.web"])
        assert len(web_asgs["AutoScalingGroups"]) == 1
        web_asg = web_asgs["AutoScalingGroups"][0]
        assert web_asg["AutoScalingGroupName"] == "unittest.web"
        assert web_asg["LaunchConfigurationName"] == "unittest.web"
        assert client.instances.discover("unittest", "web")["Id"] == "unittest.web"
        web_lb_asgs = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=["unittest.web-lb"])
        assert len(web_lb_asgs["AutoScalingGroups"]) == 1
        web_lb_asg = web_lb_asgs["AutoScalingGroups"][0]
        assert web_lb_asg["AutoScalingGroupName"] == "unittest.web-lb"
        assert web_lb_asg["LaunchConfigurationName"] == "unittest.web-lb"
        assert client.instances.discover("unittest", "web-lb")["Id"] == "unittest.web-lb"

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
    client.instances.destroy("unittest", "web-lb")

    if provider == "aws":
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
                AutoScalingGroupNames=["unittest.web"])
        assert len(asgs["AutoScalingGroups"]) == 1
        asg = asgs["AutoScalingGroups"][0]
        assert asg["AutoScalingGroupName"] == "unittest.web"
        assert asg["LaunchConfigurationName"] == "unittest.web"

    # Now destroy the rest
    client.instances.destroy("unittest", "web")

    if provider == "aws":
        # AutoScalingGroups
        autoscaling = boto3.client("autoscaling")
        asgs = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=["unittest.web"])
        assert len(asgs["AutoScalingGroups"]) == 0
        asgs = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=["unittest.web-lb"])
        assert len(asgs["AutoScalingGroups"]) == 0

    # Clean up the VPC
    client.network.destroy("unittest")


@mock_ec2
@mock_elb
@mock_autoscaling
@mock_route53
@pytest.mark.mock_aws
def test_instances_mock():
    run_instances_test(provider="aws", credentials={})

@pytest.mark.aws
def test_instances_aws():
    run_instances_test(provider="aws", credentials={})

@pytest.mark.gce
def test_instances_gce():
    run_instances_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
