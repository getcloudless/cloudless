"""
Helper to get availability zones for AWS.
"""
from cloudless.providers.aws.log import logger


# pylint: disable=too-few-public-methods
class AvailabilityZones:
    """
    Client object for getting availability zones for AWS.
    """
    def __init__(self, driver, credentials, mock=False):
        self.driver = driver
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")
        self.mock = mock

    def get_availability_zones(self):
        """
        Returns the list of all availiablity zones in the current region.
        """
        ec2 = self.driver.client("ec2")
        if self.mock:
            # NOTE: Moto does not have this function supported, so this has to be here to get the
            # mock tests passing.
            logger.info("Returning hard coded azs for mock AWS provider")
            return ["us-east-1a", "us-east-1b", "us-east-1c"]
        availability_zones = ec2.describe_availability_zones()
        return [az["ZoneName"]
                for az in availability_zones["AvailabilityZones"]]
