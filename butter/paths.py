import logging

from butter.providers import get_provider

logger = logging.getLogger(__name__)


class PathsClient(object):

    def __init__(self, provider, credentials):
        self.paths = get_provider(provider).paths.PathsClient(credentials)

    def expose(self, network_name, subnetwork_name, port):
        logger.info('Exposing service %s in network %s on port %s',
                    subnetwork_name, network_name, port)
        return self.paths.expose(network_name, subnetwork_name, port)

    def add(self, network, from_name, to_name, port):
        logger.info('Adding path from %s to %s in network %s on port %s',
                    from_name, to_name, network, port)
        return self.paths.add(network, from_name, to_name, port)

    def remove(self, network, from_name, to_name, port):
        logger.info('Removing path from %s to %s in network %s on port %s',
                    from_name, to_name, network, port)
        return self.paths.remove(network, from_name, to_name, port)

    def list(self):
        return self.paths.list()

    def graph(self):
        return self.paths.graph()

    def internet_accessible(self, network_name, subnetwork_name, port):
        return self.paths.internet_accessible(network_name, subnetwork_name,
                                              port)

    def has_access(self, network, from_name, to_name, port):
        return self.paths.has_access(network, from_name, to_name, port)
