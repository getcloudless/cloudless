"""
Butter Network on Mock AWS
"""
import boto3
from moto import mock_ec2
import butter.providers.aws.impl.network

@mock_ec2
class NetworkClient:
    """
    Butter Network Client Object for AWS

    This is the object through which all network related calls are made for AWS.
    """

    def __init__(self, credentials):
        self.network = butter.providers.aws.impl.network.NetworkClient(boto3, credentials,
                                                                       mock=False)

    def create(self, name, blueprint):
        """
        Create new network named "name" with blueprint file at "blueprint".
        """
        return self.network.create(name, blueprint)

    # pylint: disable=no-self-use
    def get(self, name):
        """
        Get a network named "name" and return some data about it.
        """
        return self.network.get(name)

    # pylint: disable=no-self-use
    def destroy(self, network):
        """
        Destroy a network given the provided network object.
        """
        return self.network.destroy(network)

    # pylint: disable=no-self-use
    def list(self):
        """
        List all networks.
        """
        return self.network.list()
