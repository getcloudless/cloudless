"""
Cloudless Service

This component should allow for intuitive and transparent control over services, which consist of
subnetworks and groups of instances.
"""
from cloudless.log import logger
from cloudless.providers import get_provider
from cloudless.types.common import Network, Service
from cloudless.util.exceptions import DisallowedOperationException

class ServiceClient:
    """
    Cloudless Service Client.

    This is the object through which all service related calls are made.  The objects returned by
    these commands are of type `cloudless.types.common.Service` which contain objects of type
    `cloudless.types.common.Subnetwork`, which themselves contain lists of
    `cloudless.types.common.Instance`.  This is because the service is the logical grouping, but
    behind the scenes they are groups of instances deployed in private subnetworks.

    Usage:

        import cloudless
        client = cloudless.Client(provider, credentials)
        network = client.network.create("network", blueprint="tests/blueprints/network.yml")
        client.service.create(network, "public", blueprint="tests/blueprints/service.yml")
        myservice = client.service.get(mynetwork, "public")
        client.service.list()
        client.service.destroy(myservice)

    The above commands will create and destroy a service named "public" in the network "network".
    """
    def __init__(self, provider, credentials):
        self.service = get_provider(provider).service.ServiceClient(credentials)

    # pylint: disable=too-many-arguments
    def create(self, network, service_name, blueprint, template_vars=None, count=None):
        """
        Create a service in "network" named "service_name" with blueprint file at "blueprint".

        "template_vars" are passed to the initialization scripts as jinja2
        variables.

        Example:

            example_network = client.network.create("example")
            example_service = client.service.create(network=example_network,
                                                    name="example_service",
                                                    blueprint="example-blueprint.yml")

        """
        logger.debug('Creating service %s in network %s with blueprint %s, template_vars %s, '
                     'and count %s', service_name, network, blueprint, template_vars, count)
        if not isinstance(network, Network):
            raise DisallowedOperationException(
                "Network argument to create must be of type cloudless.types.common.Network")
        return self.service.create(network, service_name, blueprint, template_vars, count)

    def get(self, network, service_name):
        """
        Get a service in "network" named "service_name".

        Example:

            example_service = client.service.get(network=client.network.get("example"),
                                                 name="example_service")

        """
        logger.debug('Discovering service %s in network %s', service_name, network)
        if not isinstance(network, Network):
            raise DisallowedOperationException(
                "Network argument to get must be of type cloudless.types.common.Network")
        return self.service.get(network, service_name)

    # pylint: disable=no-self-use
    def get_instances(self, service):
        """
        Helper to return the list of instances given a service object.

        Example:

            example_service = client.service.get(network=client.network.get("example"),
                                                 name="example_service")
            instances = client.service.get_instances(example_service)

        """
        if not isinstance(service, Service):
            raise DisallowedOperationException(
                "Service argument to get_instances must be of type cloudless.types.common.Service")
        return [i for s in service.subnetworks for i in s.instances]

    def destroy(self, service):
        """
        Destroy a service described by the "service" object.

        Example:

            example_service = client.service.get(network=client.network.get("example"),
                                                 name="example_service")
            client.service.destroy(example_service)

        """
        logger.debug('Destroying service %s', service)
        if not isinstance(service, Service):
            raise DisallowedOperationException(
                "Service argument to destroy must be of type cloudless.types.common.Service")
        return self.service.destroy(service)

    def list(self):
        """
        List all services.

        Example:

            client.service.list()

        """
        logger.debug('Listing services')
        return self.service.list()

    def node_types(self):
        """
        Get mapping of node types to the resources.

        Example:

            client.service.node_types()

        """
        logger.debug('Listing node types')
        return self.service.node_types()
