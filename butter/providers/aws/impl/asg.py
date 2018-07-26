# pylint: disable=no-self-use,missing-docstring
"""
ASG Impl

Implementation of some common helpers necessary to work with ASGs.
"""

import boto3

from botocore.exceptions import ClientError

from butter.util.exceptions import BadEnvironmentStateException
from butter.providers.aws.logging import logger


# pylint: disable=too-few-public-methods
class AsgName:
    """
    Wrapper to hold the autoscaling group name, because I've refactored a few
    times and this needs to be consistent regardless of what it is.  Someday
    this needs to be carefully rethought, but for now we need to namespace both
    on subnetwork and network because the ASG name is unique and global to the
    account (I think, but this should make it easier to change).
    """
    def __init__(self, network=None, subnetwork=None, name_string=None):
        if not name_string and network and subnetwork:
            self.network = network
            self.subnetwork = subnetwork
        elif name_string and not network and not subnetwork:
            name_split = name_string.split(".")
            if len(name_split) == 2:
                self.network, self.subnetwork = name_string.split(".")
        else:
            raise Exception("Invalid input to AsgName")

    def __str__(self):
        return "%s.%s" % (self.network, self.subnetwork)


class ASG:
    """
    Autoscaling groups helpers class.
    """

    def __init__(self, credentials):
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")

    def _describe_launch_configuration(self, asg_name):
        autoscaling = boto3.client("autoscaling")
        launch_configurations = autoscaling.describe_launch_configurations(
            LaunchConfigurationNames=[str(asg_name)])
        if len(launch_configurations["LaunchConfigurations"]) != 1:
            return None
        return launch_configurations["LaunchConfigurations"][0]

    # pylint: disable=invalid-name
    def get_launch_configuration_security_group(self, network_name,
                                                subnetwork_name):
        logger.debug("Getting security group for launch configuration %s, %s",
                     network_name, subnetwork_name)
        asg_name = AsgName(network=network_name, subnetwork=subnetwork_name)
        launch_configuration = self._describe_launch_configuration(asg_name)
        if not launch_configuration:
            return None
        security_groups = launch_configuration["SecurityGroups"]
        if len(security_groups) != 1:
            raise BadEnvironmentStateException("Expected launch configuration "
                                               "%s to have exactly one "
                                               "security group: %s" %
                                               str(asg_name),
                                               launch_configuration)
        return security_groups[0]

    # pylint: disable=invalid-name
    def destroy_auto_scaling_group_instances(self, asg_name):
        autoscaling = boto3.client("autoscaling")
        try:
            autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=str(asg_name), MinSize=0,
                DesiredCapacity=0)
        except ClientError as client_error:
            logger.debug("Recieved exception scaling autoscaling group: %s",
                         client_error)
            msg = "AutoScalingGroup name not found - null"
            if (client_error.response["Error"]["Code"] == "ValidationError" and
                    client_error.response["Error"]["Message"] == msg):
                logger.debug("Autoscaling group: %s already deleted",
                             str(asg_name))
            else:
                raise client_error

    def destroy_auto_scaling_group(self, asg_name):
        autoscaling = boto3.client("autoscaling")
        try:
            autoscaling.delete_auto_scaling_group(
                AutoScalingGroupName=str(asg_name), ForceDelete=True)
        except ClientError as client_error:
            logger.debug("Recieved exception destroying autoscaling group: %s",
                         client_error)
            msg = "AutoScalingGroup name not found - AutoScalingGroup '%s' not found" % (
                str(asg_name))
            if (client_error.response["Error"]["Code"] == "ValidationError" and
                    client_error.response["Error"]["Message"] == msg):
                logger.debug("Autoscaling group: %s already deleted",
                             str(asg_name))
            else:
                raise client_error

    def destroy_launch_configuration(self, asg_name):
        autoscaling = boto3.client("autoscaling")
        try:
            autoscaling.delete_launch_configuration(
                LaunchConfigurationName=str(asg_name))
        except ClientError as client_error:
            logger.info("Recieved exception destroying launch configuration: %s", client_error)
            msg = "Launch configuration name not found - Launch configuration %s not found" % (
                str(asg_name))
            if (client_error.response["Error"]["Code"] == "ValidationError" and
                    client_error.response["Error"]["Message"] == msg):
                logger.debug("Launch configuration: %s already deleted",
                             str(asg_name))
            else:
                raise client_error
