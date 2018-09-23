# pylint: disable=no-self-use,missing-docstring
"""
ASG Impl

Implementation of some common helpers necessary to work with ASGs.
"""

from botocore.exceptions import ClientError
from retrying import retry
from cloudless.util.exceptions import (BadEnvironmentStateException, IncompleteOperationException)
from cloudless.providers.aws.log import logger

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

def retry_if_still_waiting(exception):
    """
    Checks if this exception is just because we haven't converged yet.
    """
    return isinstance(exception, IncompleteOperationException)

class ASG:
    """
    Autoscaling groups helpers class.
    """

    def __init__(self, driver, credentials):
        self.driver = driver
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")

    def _describe_launch_configuration(self, asg_name):
        autoscaling = self.driver.client("autoscaling")
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
        autoscaling = self.driver.client("autoscaling")
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
        autoscaling = self.driver.client("autoscaling")
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
        autoscaling = self.driver.client("autoscaling")
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

    @retry(wait_fixed=5000, stop_max_attempt_number=36, retry_on_exception=retry_if_still_waiting)
    def wait_for_in_service(self, asg_name, instance_id):
        logger.debug("Waiting for %s in %s to be in service", instance_id, asg_name)
        autoscaling = self.driver.client("autoscaling")
        asgs = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
        if len(asgs["AutoScalingGroups"]) != 1:
            raise BadEnvironmentStateException(
                "Found multiple asgs for name %s: %s" % (asg_name, asgs))
        for instance in asgs["AutoScalingGroups"][0]["Instances"]:
            if instance["InstanceId"] == instance_id:
                if instance["LifecycleState"] == "InService":
                    return True
                logger.debug("Still waiting for %s in %s to be in service", instance_id,
                             asg_name)
                raise IncompleteOperationException("Still waiting for in service")
        raise BadEnvironmentStateException(
            "Could not find instance %s in asg: %s" % (instance_id, asgs))
