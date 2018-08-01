"""
Butter Paths

This component should allow for intuitive and transparent control over which
instance groups can communicate.  The abstraction it provides is a graph, and it
does the transformation to and from the underlying firewall rules.
"""
from butter.log import logger
from butter.providers import get_provider


class PathsClient:
    """
    Butter Paths Client Object

    This is the object through which all path related calls are made.

    Usage:

        import butter
        client = butter.Client(provider, credentials)
        client.paths.expose("network", "external-service", 443)
        client.paths.add("network", "external-service", "internal-service, 80)
        client.paths.list()
        client.paths.graph()

    The above commands will result in the public internet having access to
    "external-service" on port 443 and "external-service" having access to
    "internal-service" on port 80.
    """

    def __init__(self, provider, credentials):
        self.paths = get_provider(provider).paths.PathsClient(credentials)

    def expose(self, network_name, subnetwork_name, port):
        """
        Make the service described by "network_name" and "subnetwork_name"
        internet accessible on the given port.
        """
        logger.info('Exposing service %s in network %s on port %s',
                    subnetwork_name, network_name, port)
        return self.paths.expose(network_name, subnetwork_name, port)

    def add(self, network, from_name, to_name, port):
        """
        Make the service described by "network" and "to_name" accessible from
        the service described by "network" and "from_name" on the given port.
        """
        logger.info('Adding path from %s to %s in network %s on port %s',
                    from_name, to_name, network, port)
        return self.paths.add(network, from_name, to_name, port)

    def remove(self, network, from_name, to_name, port):
        """
        Ensure the service described by "network" and "to_name" is not
        accessible from the service described by "network" and "from_name" on
        the given port.
        """
        logger.info('Removing path from %s to %s in network %s on port %s',
                    from_name, to_name, network, port)
        return self.paths.remove(network, from_name, to_name, port)

    def list(self):
        """
        List all paths and return a dictionary structure representing a graph.
        """
        return self.paths.list()

    def internet_accessible(self, network_name, subnetwork_name, port):
        """
        Returns true if the service described by "network_name" and
        "subnetwork_name" is internet accessible on the given port.
        """
        return self.paths.internet_accessible(network_name, subnetwork_name,
                                              port)

    def has_access(self, network, from_name, to_name, port):
        """
        Returns true if the service described by "network" and "to_name" is
        accessible from the service described by "network" and "from_name" on
        the given port.

        Note, this can only take service names, not CIDR blocks.  See
        https://github.com/sverch/butter/issues/3 for details.
        """
        return self.paths.has_access(network, from_name, to_name, port)
