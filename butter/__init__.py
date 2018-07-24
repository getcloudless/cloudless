import logging

from butter import network, subnetwork, instances, paths

logging.basicConfig()


def setLogLevel(level):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)


setLogLevel(logging.INFO)


class Client(object):

    def __init__(self, provider, credentials):
        self.network = network.NetworkClient(provider, credentials)
        self.subnetwork = subnetwork.SubnetworkClient(provider, credentials)
        self.instances = instances.InstancesClient(provider, credentials)
        self.paths = paths.PathsClient(provider, credentials)
