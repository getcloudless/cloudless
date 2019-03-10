"""
Cloudless Network Model on AWS
"""
import boto3
import cloudless.model
from cloudless.types.common import NetworkModel
import cloudless.providers.aws.impl.network

class NetworkResourceDriver(cloudless.model.ResourceDriver):
    """
    This class is what gets called when the user is trying to interact with a "Network" resource.
    """
    def __init__(self, provider, credentials):
        self.provider = provider
        self.credentials = credentials
        super(NetworkResourceDriver, self).__init__(provider, credentials)
        if "profile" in credentials:
            boto3.setup_default_session(profile_name=credentials["profile"])
        self.driver = boto3
        # Should remove this when I actually have a real model for the network.  e.g.
        # model.get("Network", "etc...")
        self.network = cloudless.providers.aws.impl.network.NetworkClient(boto3, mock=False)

    def create(self, resource_definition):
        network = resource_definition
        # Get rid of this when I reimplement here, now just for compatibility/testing.
        # Also do not pass the blueprint.
        old_network = self.network.create(network.name, None)
        return NetworkModel(version=network.version, name=old_network.name)

    def apply(self, resource_definition):
        network = resource_definition
        # Get rid of this when I reimplement here, now just for compatibility/testing.
        # Also do not pass the blueprint.
        old_network = self.network.get(network.name)
        return NetworkModel(version=network.version, name=old_network.name)

    def delete(self, resource_definition):
        network = resource_definition
        # Get rid of this when I reimplement here, now just for compatibility/testing.
        # Also do not pass the blueprint.
        old_network = self.network.get(network.name)
        if old_network:
            self.network.destroy(old_network)

    def get(self, resource_definition):
        network = resource_definition
        # Get rid of this when I reimplement here, now just for compatibility/testing.
        # Also do not pass the blueprint.
        old_network = self.network.get(network.name)
        if old_network:
            return [NetworkModel(version=network.version, name=old_network.name)]
        return None

    def flags(self, resource_definition):
        return []
