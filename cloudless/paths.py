"""
Cloudless Paths

This component should allow for intuitive and transparent control over which
instance groups can communicate.  The abstraction it provides is a graph, and it
does the transformation to and from the underlying firewall rules.
"""
from cloudless.log import logger
from cloudless.providers import get_provider
# Importing this just so it's available in this namespace.
# pylint: disable=unused-import
from cloudless.types.networking import CidrBlock


class PathsClient:
    """
    Cloudless Paths Client Object

    This is the object through which all path related calls are made.

    Usage:

        import cloudless
        client = cloudless.Client(provider, credentials)
        internal_service = client.service.get(network, "internal_service")
        load_balancer = client.service.get(network, "load_balancer")
        internet = CidrBlock("0.0.0.0/0")
        client.paths.add(load_balancer, internal_service, 80)
        client.paths.add(internet, load_balancer, 443)
        client.paths.list()
        client.graph()

    The above commands will result in the public internet having access to "load_balancer" on port
    443 and "load_balancer" having access to "internal_service" on port 80.
    """

    def __init__(self, provider, credentials):
        self.paths = get_provider(provider).paths.PathsClient(credentials)

    def add(self, source, destination, port):
        """
        Make the service or cidr block described by "destination" accessible from the service or
        cidr block described by "source" on the given port.

        Either "source" or "destination" must be a service object.
        """
        logger.info('Adding path from %s to %s on port %s', source, destination, port)
        return self.paths.add(source, destination, port)

    def remove(self, source, destination, port):
        """
        Ensure the service or cidr block described by "destination" is not accessible from the
        service or cidr block described by "source" on the given port.

        Either "source" or "destination" must be a service object.
        """
        logger.info('Removing path from %s to %s on port %s', source, destination, port)
        return self.paths.remove(source, destination, port)

    def list(self):
        """
        List all paths and return a dictionary structure representing a graph.
        """
        return self.paths.list()

    def internet_accessible(self, service, port):
        """
        Returns true if the service described by "service" is internet accessible on the given port.
        """
        return self.paths.internet_accessible(service, port)

    def has_access(self, source, destination, port):
        """
        Returns true if the service or cidr block described by "destination" is accessible from the
        service or cidr block described by "source" on the given port.

        Either "source" or "destination" must be a service object.
        """
        return self.paths.has_access(source, destination, port)
