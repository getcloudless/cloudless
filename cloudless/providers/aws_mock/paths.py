"""
Cloudless Paths on AWS

This is a the AWS implmentation for the paths API, a high level interface to add
routes between services, doing the conversion to security groups and firewall
rules.
"""
import boto3
from moto import mock_ec2, mock_autoscaling
import cloudless.providers.aws.impl.paths

@mock_ec2
@mock_autoscaling
class PathsClient:
    """
    Client object to interact with paths between resources.
    """

    # You can set a "profile" in credentials, but that doesn't matter for moto
    # pylint: disable=unused-argument
    def __init__(self, credentials):
        self.paths = cloudless.providers.aws.impl.paths.PathsClient(boto3, mock=True)


    def add(self, source, destination, port):
        """
        Adds a route from "source" to "destination".
        """
        return self.paths.add(source, destination, port)

    def remove(self, source, destination, port):
        """
        Remove a route from "source" to "destination".
        """
        return self.paths.remove(source, destination, port)

    def list(self):
        """
        List all paths and return a dictionary structure representing a graph.
        """
        return self.paths.list()

    def internet_accessible(self, service, port):
        """
        Return true if the given service is accessible on the internet.
        """
        return self.paths.internet_accessible(service, port)

    def has_access(self, source, destination, port):
        """
        Return true if there is a route from "source" to "destination".
        """
        return self.paths.has_access(source, destination, port)
