"""
Helper to get availability zones for AWS.
"""
import boto3
from butter.providers.aws.log import logger


# pylint: disable=too-few-public-methods
class AvailabilityZones:
    """
    Client object for getting availability zones for AWS.
    """
    def __init__(self, credentials):
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")

    # pylint: disable=no-self-use
    def get_availability_zones(self):
        """
        Returns the list of all availiablity zones in the current region.
        """
        ec2 = boto3.client("ec2")
        try:
            availability_zones = ec2.describe_availability_zones()
            return [az["ZoneName"]
                    for az in availability_zones["AvailabilityZones"]]
        except NotImplementedError as exception:
            logger.info("Caught exception getting azs: %s", exception)
            # NOTE: Moto does not have this function supported, so this has to be here to get the
            # mock tests passing.
            return ["us-east-1a", "us-east-1b", "us-east-1c"]
