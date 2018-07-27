"""
Butter Network on GCE

This component should allow for intuitive and transparent control over networks, which are the top
level containers for groups of instances/services.  This is the GCE implementation.
"""
from libcloud.common.google import ResourceNotFoundError

from butter.providers.gce.driver import get_gce_driver
from butter.providers.gce.log import logger
from butter.providers.gce.schemas import canonicalize_network_info


class NetworkClient:
    """
    Butter Network Client Object for GCE

    This is the object through which all network related calls are made for GCE.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)

    # pylint: disable=unused-argument
    def create(self, name, blueprint, inventories=None):
        """
        Create new network named "name" with blueprint file at "blueprint".

        Note that google compute networks do not actually have a network block.  They are merely a
        container for subnets, which do.
        """
        network = self.driver.ex_create_network(name, cidr=None, mode="custom")
        return canonicalize_network_info(network)

    def discover(self, name):
        """
        Discover a network named "name" and return some data about it.
        """
        try:
            network = self.driver.ex_get_network(name)
        except ResourceNotFoundError as not_found:
            logger.info("Caught exception trying to discover network: %s",
                        not_found)
            return None
        return canonicalize_network_info(network)

    def destroy(self, name):
        """
        Destroy a network named "name".
        """
        try:
            network = self.driver.ex_get_network(name)
        except ResourceNotFoundError as not_found:
            logger.info("Caught exception destroying network, ignoring: %s",
                        not_found)
            return None
        return self.driver.ex_destroy_network(network)

    def list(self):
        """
        List all networks.
        """
        return {"Named": [canonicalize_network_info(network) for network
                          in self.driver.ex_list_networks()]}
