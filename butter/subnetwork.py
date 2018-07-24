import logging

from butter.providers import get_provider

logger = logging.getLogger(__name__)


class SubnetworkClient(object):
    def __init__(self, provider, credentials):
        self.subnetwork = get_provider(provider).subnetwork.SubnetworkClient(
            credentials)

    def create(self, network_name, subnetwork_name, blueprint):
        logger.info('Creating subnetwork %s, %s with blueprint %s',
                    network_name, subnetwork_name, blueprint)
        return self.subnetwork.create(network_name, subnetwork_name, blueprint)

    def discover(self, network_name, subnetwork_name):
        logger.info('Discovering subnetwork %s, %s', network_name,
                    subnetwork_name)
        return self.subnetwork.discover(network_name, subnetwork_name)

    def destroy(self, network_name, subnetwork_name):
        logger.info('Destroying subnetwork %s, %s', network_name,
                    subnetwork_name)
        return self.subnetwork.destroy(network_name, subnetwork_name)

    def list(self):
        logger.info('Listing subnetworks')
        return self.subnetwork.list()
