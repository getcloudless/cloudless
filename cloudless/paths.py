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
    Cloudless Paths Client.

    This is the object through which all path related calls are made.  The objects returned by these
    commands are of type `cloudless.types.common.Path` which contain objects of type
    `cloudless.types.common.Service` and `cloudless.types.networking.CidrBlock` depending on whether
    the path is internally or externally facing.

    Usage:

        import cloudless
        client = cloudless.Client(provider, credentials)
        internal_service = client.service.get(network, "internal_service")
        load_balancer = client.service.get(network, "load_balancer")
        internet = cloudless.types.networking.CidrBlock("0.0.0.0/0")
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

        Example:

            service1 = client.service.get(network=client.network.get("example"), name="service1")
            service2 = client.service.get(network=client.network.get("example"), name="service2")
            internet = cloudless.types.networking.CidrBlock("0.0.0.0/0")
            client.paths.add(service1, service2, 443)
            client.paths.add(internet, service1, 80)

        """
        logger.debug('Adding path from %s to %s on port %s', source, destination, port)
        return self.paths.add(source, destination, int(port))

    def remove(self, source, destination, port):
        """
        Ensure the service or cidr block described by "destination" is not accessible from the
        service or cidr block described by "source" on the given port.

        Either "source" or "destination" must be a service object.

        Example:

            service1 = client.service.get(network=client.network.get("example"), name="service1")
            service2 = client.service.get(network=client.network.get("example"), name="service2")
            internet = cloudless.types.networking.CidrBlock("0.0.0.0/0")
            client.paths.remove(service1, service2, 443)
            client.paths.remove(internet, service1, 80)

        """
        logger.debug('Removing path from %s to %s on port %s', source, destination, port)
        return self.paths.remove(source, destination, int(port))

    def list(self):
        """
        List all paths and return a dictionary structure representing a graph.

        Example:

            client.paths.list()

        """
        return self.paths.list()

    def internet_accessible(self, service, port):
        """
        Returns true if the service described by "service" is internet accessible on the given port.

        Example:

            service1 = client.service.get(network=client.network.get("example"), name="service1")
            client.paths.internet_accessible(service1, 443)

        """
        return self.paths.internet_accessible(service, int(port))

    def has_access(self, source, destination, port):
        """
        Returns true if the service or cidr block described by "destination" is accessible from the
        service or cidr block described by "source" on the given port.

        Either "source" or "destination" must be a service object.

        Example:

            service1 = client.service.get(network=client.network.get("example"), name="service1")
            service2 = client.service.get(network=client.network.get("example"), name="service2")
            internet = cloudless.types.networking.CidrBlock("0.0.0.0/0")
            client.paths.has_access(service1, service2, 443)
            client.paths.has_access(internet, service1, 80)

        """
        return self.paths.has_access(source, destination, int(port))
