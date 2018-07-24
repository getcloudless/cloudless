import logging

from butter.providers import get_provider

logger = logging.getLogger(__name__)


class NetworkClient(object):
    def __init__(self, provider, credentials):
        self.network = get_provider(provider).network.NetworkClient(
            credentials)

    def create(self, name, blueprint, inventories=None):
        """
        Create new network named "name" with blueprint file at "blueprint".

        Example:

            client.network.create("mynetwork", "network-blueprint.yml")

        """
        logger.info('Creating network %s with blueprint %s', name, blueprint)
        return self.network.create(name, blueprint, inventories)

    def discover(self, name):
        """
        Discover a network named "name" and return some data about it.

        Example:

            client.network.discover("mynetwork")

        """
        logger.info('Discovering network %s', name)
        return self.network.discover(name)

    def destroy(self, name):
        """
        Destroy a network named "name".

        Example:

            client.network.destroy("mynetwork")

        """
        logger.info('Destroying network %s', name)
        return self.network.destroy(name)

    def list(self):
        """
        List all networks.

        Example:

            client.network.list()

        """
        logger.info('Listing networks')
        return self.network.list()
