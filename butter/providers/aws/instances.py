"""
Butter Instances on AWS

This is the AWS implmentation for the instances API, a high level interface to manage groups of
instances.
"""
import time
import boto3
import dateutil.parser
from botocore.exceptions import ClientError

from butter.util.blueprint import InstancesBlueprint
from butter.util.instance_fitter import get_fitting_instance
from butter.util.exceptions import (BadEnvironmentStateException,
                                    OperationTimedOut)
from butter.providers.aws import (subnetwork, network)
from butter.providers.aws.impl.asg import (ASG, AsgName)
from butter.providers.aws.impl.security_groups import SecurityGroups
from butter.providers.aws.log import logger
from butter.providers.aws.schemas import canonicalize_instances_info

RETRY_COUNT = int(60)
RETRY_DELAY = float(1.0)


class InstancesClient:
    """
    Client object to manage instances.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.subnetwork = subnetwork.SubnetworkClient(credentials)
        self.network = network.NetworkClient(credentials)
        self.asg = ASG(credentials)
        self.security_groups = SecurityGroups(credentials)

    def create(self, network_name, subnetwork_name, blueprint, count=3):
        """
        Create a group of instances in "network_name" named "subnetwork_name" with blueprint file at
        "blueprint".
        """
        subnet_ids = [subnet_info["Id"] for subnet_info
                      in self.subnetwork.create(network_name, subnetwork_name,
                                                blueprint=blueprint)]

        # Security Group
        asg_name = AsgName(network=network_name, subnetwork=subnetwork_name)
        vpc_id = self.network.discover(network_name)["Id"]
        security_group_id = self.security_groups.create(str(asg_name), vpc_id)

        # Launch Configuration
        def lookup_ami(ami_name):
            ec2 = boto3.client("ec2")
            images = ec2.describe_images(Filters=[{"Name": "name",
                                                   "Values": [ami_name]}])
            result_image = None
            for image in images["Images"]:
                if not result_image:
                    result_image = image
                if (dateutil.parser.parse(image["CreationDate"]) >
                        dateutil.parser.parse(result_image["CreationDate"])):
                    result_image = image
            return result_image["ImageId"]

        def create_launch_configuration(asg_name, blueprint):
            instances_blueprint = InstancesBlueprint(blueprint)
            ami_id = lookup_ami(instances_blueprint.image())
            user_data = instances_blueprint.runtime_scripts()
            associate_public_ip = instances_blueprint.public_ip()
            instance_type = get_fitting_instance("aws", blueprint)
            autoscaling = boto3.client("autoscaling")
            autoscaling.create_launch_configuration(
                LaunchConfigurationName=str(asg_name), ImageId=ami_id,
                SecurityGroups=[security_group_id], UserData=user_data,
                AssociatePublicIpAddress=associate_public_ip,
                InstanceType=instance_type)
        create_launch_configuration(asg_name, blueprint)

        # Auto Scaling Group
        comma_separated_subnets = ",".join(subnet_ids)
        autoscaling = boto3.client("autoscaling")
        autoscaling.create_auto_scaling_group(
            AutoScalingGroupName=str(asg_name),
            LaunchConfigurationName=str(asg_name), MinSize=count,
            MaxSize=count, DesiredCapacity=count,
            VPCZoneIdentifier=comma_separated_subnets, LoadBalancerNames=[],
            HealthCheckType='ELB', HealthCheckGracePeriod=120)

        return self.discover(network_name, subnetwork_name)

    def list(self):
        """
        List all instance groups.
        """
        autoscaling = boto3.client("autoscaling")
        asgs = autoscaling.describe_auto_scaling_groups()
        services = []
        for asg in asgs["AutoScalingGroups"]:
            asg_name = AsgName(name_string=asg["AutoScalingGroupName"])
            if asg_name.network:
                services.append(self.discover(asg_name.network,
                                              asg_name.subnetwork))
        return services

    # pylint: disable=no-self-use
    def discover(self, network_name, subnetwork_name):
        """
        Discover a group of subnetworks in "network_name" named "subnetwork_name".
        """
        logger.info("Discovering autoscaling group named %s in network: %s",
                    network_name, subnetwork_name)

        def discover_asg(network_name, subnetwork_name):
            autoscaling = boto3.client("autoscaling")
            logger.debug("Discovering auto scaling groups with name: %s",
                         subnetwork_name)
            asg_name = AsgName(network=network_name, subnetwork=subnetwork_name)
            asgs = autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[str(asg_name)])
            logger.debug("Found asgs: %s", asgs)
            if len(asgs["AutoScalingGroups"]) > 1:
                raise BadEnvironmentStateException(
                    "Expected to find at most one auto scaling group "
                    "named: %s, output: %s" % (str(asg_name), asgs))
            if not asgs["AutoScalingGroups"]:
                return None
            return asgs["AutoScalingGroups"][0]

        def discover_instances(instance_ids):
            ec2 = boto3.client("ec2")
            logger.debug("Discovering instances: %s", instance_ids)
            if instance_ids:
                return ec2.describe_instances(InstanceIds=instance_ids)
            return {"Reservations": []}

        discovery_retries = 0
        while discovery_retries < RETRY_COUNT:
            try:
                asg = discover_asg(network_name, subnetwork_name)
                if not asg:
                    return None
                instance_ids = [instance["InstanceId"] for instance
                                in asg["Instances"]]
                instances = discover_instances(instance_ids)
                return canonicalize_instances_info(asg, instances)
            except ClientError as client_error:
                # There is a race between when I discover the autoscaling group
                # itself and when I try to search for the instances inside it,
                # so just retry if this happens.
                logger.info("Recieved exception discovering instance: %s", client_error)
                if client_error.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
                    pass
                else:
                    raise client_error
            discovery_retries = discovery_retries + 1
            logger.info("Instance discovery retry number: %s",
                        discovery_retries)
            if discovery_retries >= RETRY_COUNT:
                raise OperationTimedOut(
                    "Exceeded retries while discovering %s, in network %s" %
                    (subnetwork_name, network_name))
            time.sleep(float(RETRY_DELAY))

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy a group of instances named "subnetwork_name" in "network_name".
        """
        logger.debug("Attempting to destroy: %s, %s", network_name,
                     subnetwork_name)
        asg_name = AsgName(network=network_name, subnetwork=subnetwork_name)

        self.asg.destroy_auto_scaling_group_instances(asg_name)

        # Wait for instances to be gone.  Need to do this before we can delete
        # the actual ASG otherwise it will error.
        asg = self.discover(network_name, subnetwork_name)
        retries = 0
        while [instance for instance in asg["Instances"]
               if instance["State"] != "terminated"]:
            logger.info("Waiting for instance termination in asg: %s", asg)
            asg = self.discover(network_name, subnetwork_name)
            retries = retries + 1
            if retries > 60:
                raise OperationTimedOut("Timed out waiting for ASG scale down")
            time.sleep(float(10))

        self.asg.destroy_auto_scaling_group(asg_name)

        # Wait for ASG to be gone.  Need to wait for this because it's a
        # dependency of the launch configuration.
        asg = self.discover(network_name, subnetwork_name)
        retries = 0
        while asg:
            logger.info("Waiting for asg deletion: %s", asg)
            asg = self.discover(network_name, subnetwork_name)
            retries = retries + 1
            if retries > 60:
                raise OperationTimedOut("Timed out waiting for ASG deletion")
            time.sleep(float(10))

        vpc_id = self.network.discover(network_name)["Id"]
        lc_security_group = self.asg.get_launch_configuration_security_group(
            network_name, subnetwork_name)
        self.asg.destroy_launch_configuration(asg_name)
        if lc_security_group:
            self.security_groups.delete_referencing_rules(vpc_id,
                                                          lc_security_group)
            self.security_groups.delete_with_retries(lc_security_group,
                                                     RETRY_COUNT, RETRY_DELAY)
        self.subnetwork.destroy(network_name, subnetwork_name)
