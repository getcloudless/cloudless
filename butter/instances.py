import logging

from butter.providers import get_provider

logger = logging.getLogger(__name__)


class InstancesClient(object):
    def __init__(self, provider, credentials):
        self.instances = get_provider(provider).instances.InstancesClient(
            credentials)

    def create(self, network_name, subnetwork_name, blueprint):
        logger.info('Creating instances %s in network %s with blueprint %s',
                    subnetwork_name, network_name, blueprint)
        return self.instances.create(network_name, subnetwork_name, blueprint)

    def discover(self, network_name, subnetwork_name):
        logger.info('Discovering instances %s in network %s', subnetwork_name,
                    network_name)
        return self.instances.discover(network_name, subnetwork_name)

    def destroy(self, network_name, subnetwork_name):
        logger.info('Destroying instances %s in network %s', subnetwork_name,
                    network_name)
        return self.instances.destroy(network_name, subnetwork_name)

    def list(self):
        logger.info('Listing instances')
        return self.instances.list()
