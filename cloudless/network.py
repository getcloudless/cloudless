"""
Cloudless Network

This component should allow for intuitive and transparent control over networks, which are the top
level containers for services.
"""
from cloudless.log import logger
from cloudless.providers import get_provider
from cloudless.types.common import Network
from cloudless.util.exceptions import DisallowedOperationException

class NetworkClient:
    """
    Cloudless Network Client.

    This is the object through which all network related calls are made.  The objects returned by
    these commands are of type `cloudless.types.common.Network`.

    Usage:

        import cloudless
        client = cloudless.Client(provider, credentials)
        client.network.create("network", blueprint="tests/blueprints/network.yml")
        client.network.get("network")
        client.network.list()
        client.network.destroy(client.network.get("network"))

    The above commands will create and destroy a network named "network".
    """
    def __init__(self, provider, credentials):
        self.network = get_provider(provider).network.NetworkClient(
            credentials)

    def create(self, name, blueprint=None):
        """
        Create new network named "name" with blueprint file at "blueprint".

        Example:

            client.network.create("mynetwork", "network-blueprint.yml")

        """
        logger.debug('Creating network %s with blueprint %s', name, blueprint)
        return self.network.create(name, blueprint)

    def get(self, name):
        """
        Get a network named "name" and return some data about it.

        Example:

            client.network.get("mynetwork")

        """
        logger.debug('Getting network %s', name)
        return self.network.get(name)

    def destroy(self, network):
        """
        Destroy the given network.

        Example:

            client.network.destroy(client.network.get("mynetwork"))

        """
        logger.debug('Destroying network %s', network)
        if not isinstance(network, Network):
            raise DisallowedOperationException(
                "Argument to destroy must be of type cloudless.types.common.Network")
        return self.network.destroy(network)

    def list(self):
        """
        List all networks.

        Example:

            client.network.list()

        """
        logger.debug('Listing networks')
        return self.network.list()
