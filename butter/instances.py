"""
Butter Instances

This component should allow for intuitive and transparent control over groups of instances, which
must be provisioned within a subnetwork.
"""
from butter.log import logger
from butter.providers import get_provider


class InstancesClient:
    """
    Butter Instances Client Object

    This is the object through which all instance related calls are made.

    Usage:

        import butter
        client = butter.Client(provider, credentials)
        client.instances.create("network", "public",
                                 blueprint="tests/blueprints/service.yml")
        client.instances.discover("network", "public")
        client.instances.list()
        client.instances.destroy("network", "public")

    The above commands will create and destroy a group of instances named "public" in the network
    "network".
    """
    def __init__(self, provider, credentials):
        self.instances = get_provider(provider).instances.InstancesClient(
            credentials)

    def create(self, network_name, subnetwork_name, blueprint,
               template_vars=None):
        """
        Create a group of instances in "network_name" named "subnetwork_name" with blueprint file at
        "blueprint".

        "template_vars" are passed to the initialization scripts as jinja2
        variables.
        """
        logger.info('Creating instances %s in network %s with blueprint %s and '
                    'template_vars %s', subnetwork_name, network_name,
                    blueprint, template_vars)
        return self.instances.create(network_name, subnetwork_name, blueprint,
                                     template_vars)

    def discover(self, network_name, subnetwork_name):
        """
        Discover a group of instances in "network_name" named "subnetwork_name".
        """
        logger.info('Discovering instances %s in network %s', subnetwork_name,
                    network_name)
        return self.instances.discover(network_name, subnetwork_name)

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy a group of instances named "subnetwork_name" in "network_name".
        """
        logger.info('Destroying instances %s in network %s', subnetwork_name,
                    network_name)
        return self.instances.destroy(network_name, subnetwork_name)

    def list(self):
        """
        List all instance groups.
        """
        logger.info('Listing instances')
        return self.instances.list()

    def node_types(self):
        """
        Get mapping of node types to the resources.
        """
        logger.info('Listing node types')
        return self.instances.node_types()
