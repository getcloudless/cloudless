import logging

from libcloud.common.google import ResourceNotFoundError

from butter.providers.gce.driver import get_gce_driver

logger = logging.getLogger(__name__)


class NetworkClient(object):

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)

    def _canonicalize_network_info(self, network):
        """
        Convert what is returned from GCE into the butter standard format.
        """
        cidr_block = network.cidr
        if not cidr_block:
            cidr_block = "N/A"
        return {
            "Name": network.name,
            "Id": network.id,
            "CidrBlock": cidr_block
        }

    # pylint: disable=unused-argument
    def create(self, name, blueprint, inventories=None):
        """
        Create new network named "name" with blueprint file at "blueprint".

        Note that google compute VPCs
        """
        network = self.driver.ex_create_network(name, cidr=None, mode="custom")
        return self._canonicalize_network_info(network)

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
        return self._canonicalize_network_info(network)

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
        # TODO: Turn this return format into something better.  This is a carry
        # over from AWS which can have unnamed VPCs.
        return {"Named": [self._canonicalize_network_info(network) for network
                          in self.driver.ex_list_networks()]}
