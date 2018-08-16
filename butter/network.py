"""
Butter Network

This component should allow for intuitive and transparent control over networks, which are the top
level containers for groups of instances/services.
"""
from butter.log import logger
from butter.providers import get_provider


class NetworkClient:
    """
    Butter Network Client Object

    This is the object through which all network related calls are made.

    Usage:

        import butter
        client = butter.Client(provider, credentials)
        client.network.create("network", blueprint="tests/blueprints/network.yml")
        client.network.discover("network")
        client.network.list()
        client.network.destroy("network")

    The above commands will create and destroy a network named "network".
    """
    def __init__(self, provider, credentials):
        self.network = get_provider(provider).network.NetworkClient(
            credentials)

    def create(self, name, blueprint):
        """
        Create new network named "name" with blueprint file at "blueprint".

        Example:

            client.network.create("mynetwork", "network-blueprint.yml")

        """
        logger.info('Creating network %s with blueprint %s', name, blueprint)
        return self.network.create(name, blueprint)

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
