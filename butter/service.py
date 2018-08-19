"""
Butter Service

This component should allow for intuitive and transparent control over services, which consist of
subnetworks and groups of instances.
"""
from butter.log import logger
from butter.providers import get_provider
from butter.types.common import Network, Service
from butter.util.exceptions import DisallowedOperationException


class ServiceClient:
    """
    Butter Service Client Object

    This is the object through which all service related calls are made.

    Usage:

        import butter
        client = butter.Client(provider, credentials)
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
        """
        logger.info('Creating service %s in network %s with blueprint %s, template_vars %s, '
                    'and count %s', service_name, network, blueprint, template_vars, count)
        if not isinstance(network, Network):
            raise DisallowedOperationException(
                "Network argument to create must be of type butter.types.common.Network")
        return self.service.create(network, service_name, blueprint, template_vars, count)

    def get(self, network, service_name):
        """
        Get a service in "network" named "service_name".
        """
        logger.info('Discovering service %s in network %s', service_name, network)
        if not isinstance(network, Network):
            raise DisallowedOperationException(
                "Network argument to get must be of type butter.types.common.Network")
        return self.service.get(network, service_name)

    def destroy(self, service):
        """
        Destroy a service described by the "service" object.
        """
        logger.info('Destroying service %s', service)
        if not isinstance(service, Service):
            raise DisallowedOperationException(
                "Service argument to destroy must be of type butter.types.common.Service")
        return self.service.destroy(service)

    def list(self):
        """
        List all services.
        """
        logger.info('Listing services')
        return self.service.list()

    def node_types(self):
        """
        Get mapping of node types to the resources.
        """
        logger.info('Listing node types')
        return self.service.node_types()
