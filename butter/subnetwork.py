"""
Butter Subnetwork

This component should allow for intuitive and transparent control over subnetworks, which are
provisioned inside networks and are where instances are provisioned.
"""
from butter.log import logger
from butter.providers import get_provider


class SubnetworkClient:
    """
    Butter Subnetwork Client Object

    This is the object through which all subnetwork related calls are made.

    Usage:

        import butter
        client = butter.Client(provider, credentials)
        client.subnetwork.create("network", "subnetwork",
                                 blueprint="tests/blueprints/subnetwork.yml")
        client.subnetwork.discover("network", "subnetwork")
        client.subnetwork.list()
        client.subnetwork.destroy("network", "subnetwork")

    The above commands will create and destroy a subnetwork named "subnetwork" in the network
    "network".
    """
    def __init__(self, provider, credentials):
        self.subnetwork = get_provider(provider).subnetwork.SubnetworkClient(
            credentials)

    def create(self, network_name, subnetwork_name, blueprint):
        """
        Create a group of subnetworks in "network_name" named "subnetwork_name"
        with blueprint file at "blueprint".
        """
        logger.info('Creating subnetwork %s, %s with blueprint %s',
                    network_name, subnetwork_name, blueprint)
        return self.subnetwork.create(network_name, subnetwork_name, blueprint)

    def discover(self, network_name, subnetwork_name):
        """
        Discover a group of subnetworks in "network_name" named "subnetwork_name".
        """
        logger.info('Discovering subnetwork %s, %s', network_name,
                    subnetwork_name)
        return self.subnetwork.discover(network_name, subnetwork_name)

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy a group of subnetworks named "subnetwork_name" in "network_name".
        """
        logger.info('Destroying subnetwork %s, %s', network_name,
                    subnetwork_name)
        return self.subnetwork.destroy(network_name, subnetwork_name)

    def list(self):
        """
        List all subnetworks.
        """
        logger.info('Listing subnetworks')
        return self.subnetwork.list()
