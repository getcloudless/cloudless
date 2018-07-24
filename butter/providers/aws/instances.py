import time
import logging
import boto3
import dateutil.parser
from botocore.exceptions import ClientError

from butter.util.blueprint import InstancesBlueprint
from butter.util.instance_fitter import InstanceFitter
from butter.util.exceptions import (BadEnvironmentStateException,
                                    OperationTimedOut)
from butter.providers.aws import (subnetwork, network)
from butter.providers.aws.impl.asg import (ASG, AsgName)
from butter.providers.aws.impl.security_groups import SecurityGroups

RETRY_COUNT = int(60)
RETRY_DELAY = float(1.0)

logger = logging.getLogger(__name__)


class InstancesClient(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.subnetwork = subnetwork.SubnetworkClient(credentials)
        self.network = network.NetworkClient(credentials)
        self.asg = ASG(credentials)
        self.security_groups = SecurityGroups(credentials)

    def _canonicalize_auto_scaling_group(self, asg, instances):
        return {"Id": asg["AutoScalingGroupName"],
                "Instances": [
                    {
                        "Id": instance["InstanceId"],
                        "PrivateIp": instance.get("PrivateIpAddress", "N/A"),
                        "PublicIp": instance.get("PublicIpAddress", "N/A"),
                        "State": instance["State"]["Name"]
                    }
                    for reservation in instances["Reservations"]
                    for instance in reservation["Instances"]
                    ]
                }

    def _lookup_ami(self, ami_name):
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

    def create(self, network_name, subnetwork_name, blueprint, count=3):
        subnet_ids = [subnet_info["Id"] for subnet_info
                      in self.subnetwork.create(network_name, subnetwork_name,
                                                blueprint=blueprint)]

        # Security Group
        asg_name = AsgName(network=network_name, subnetwork=subnetwork_name)
        vpc_id = self.network.discover(network_name)["Id"]
        security_group_id = self.security_groups.create(str(asg_name), vpc_id)

        # Launch Configuration
        instances_blueprint = InstancesBlueprint(blueprint)
        ami_id = self._lookup_ami(instances_blueprint.image())
        user_data = instances_blueprint.runtime_scripts()
        associate_public_ip = instances_blueprint.public_ip()
        instance_fitter = InstanceFitter()
        instance_type = instance_fitter.get_fitting_instance("aws", blueprint)
        autoscaling = boto3.client("autoscaling")
        autoscaling.create_launch_configuration(
            LaunchConfigurationName=str(asg_name), ImageId=ami_id,
            SecurityGroups=[security_group_id], UserData=user_data,
            AssociatePublicIpAddress=associate_public_ip,
            InstanceType=instance_type)

        # Auto Scaling Group
        comma_separated_subnets = ",".join(subnet_ids)
        autoscaling.create_auto_scaling_group(
            AutoScalingGroupName=str(asg_name),
            LaunchConfigurationName=str(asg_name), MinSize=count,
            MaxSize=count, DesiredCapacity=count,
            VPCZoneIdentifier=comma_separated_subnets, LoadBalancerNames=[],
            HealthCheckType='ELB', HealthCheckGracePeriod=120)

        return self.discover(network_name, subnetwork_name)

    def list(self):
        autoscaling = boto3.client("autoscaling")
        asgs = autoscaling.describe_auto_scaling_groups()
        services = []
        for asg in asgs["AutoScalingGroups"]:
            asg_name = AsgName(name_string=asg["AutoScalingGroupName"])
            # TODO: Deal with malformed auto scaling group names in a sane way.
            if asg_name.network:
                services.append(self.discover(asg_name.network,
                                              asg_name.subnetwork))
        return services

    def _discover_instances(self, instance_ids):
        """
        Discovers the given set of instances, but make sure to return nothing
        if the list is empty.  The AWS API will return everything otherwise.
        """
        ec2 = boto3.client("ec2")
        logger.debug("Discovering instances: %s", instance_ids)
        if instance_ids:
            return ec2.describe_instances(InstanceIds=instance_ids)
        return {"Reservations": []}

    def _discover_asg(self, network_name, subnetwork_name):
        """
        Discovers an autoscaling group.  This is more complex than you might
        thing, as the command to describe auto scaling groups doesn't take a
        VPC ID.
        """
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

    def _discover(self, network_name, subnetwork_name):
        logger.info("Discovering autoscaling group named %s in network: %s",
                    network_name, subnetwork_name)
        asg = self._discover_asg(network_name, subnetwork_name)
        if not asg:
            return None
        instance_ids = [instance["InstanceId"] for instance
                        in asg["Instances"]]
        instances = self._discover_instances(instance_ids)
        return self._canonicalize_auto_scaling_group(asg, instances)

    def discover(self, network_name, subnetwork_name):
        discovery_retries = 0
        while discovery_retries < RETRY_COUNT:
            try:
                return self._discover(network_name, subnetwork_name)
            except ClientError as e:
                # There is a race between when I discover the autoscaling group
                # itself and when I try to search for the instances inside it,
                # so just retry if this happens.
                logger.info("Recieved exception discovering instance: %s", e)
                if e.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
                    pass
                else:
                    raise e
            discovery_retries = discovery_retries + 1
            logger.info("Instance discovery retry number: %s",
                        discovery_retries)
            if discovery_retries >= RETRY_COUNT:
                raise OperationTimedOut(
                    "Exceeded retries while discovering %s, in network %s" %
                    (subnetwork_name, network_name))
            time.sleep(float(RETRY_DELAY))

    def destroy(self, network_name, subnetwork_name):
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
