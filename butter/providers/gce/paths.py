import logging

from butter.providers.gce.driver import get_gce_driver

logger = logging.getLogger(__name__)


class PathsClient(object):

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)

    def expose(self, network_name, subnetwork_name, port):
        """
        Makes a service internet accessible on a given port.
        """
        logger.info('Exposing service %s in network %s on port %s',
                    subnetwork_name, network_name, port)
        rules = [{"IPProtocol": "tcp", "ports": [port]}]
        firewall_name = "bu-%s-%s-%s" % (network_name, subnetwork_name, port)
        target_tag = "%s-%s" % (network_name, subnetwork_name)
        return self.driver.ex_create_firewall(firewall_name, allowed=rules,
                                              network=network_name,
                                              source_ranges=["0.0.0.0/0"],
                                              target_tags=[target_tag])

    def add(self, network, from_name, to_name, port):
        """
        Add path between two services on a given port.
        """
        logger.info('Adding path from %s to %s in network %s on port %s',
                    from_name, to_name, network, port)
        rules = [{"IPProtocol": "tcp", "ports": [port]}]
        firewall_name = "bu-%s-%s-%s-%s" % (network, from_name, to_name, port)
        source_tag = "%s-%s" % (network, from_name)
        target_tag = "%s-%s" % (network, to_name)
        return self.driver.ex_create_firewall(firewall_name, allowed=rules,
                                              network=network,
                                              source_tags=[source_tag],
                                              target_tags=[target_tag])

    def remove(self, network, from_name, to_name, port):
        """
        Remove path between two services on a given port.
        """
        logger.info('Removing path from %s to %s in network %s on port %s',
                    from_name, to_name, network, port)
        firewall_name = "bu-%s-%s-%s-%s" % (network, from_name, to_name, port)
        return self.driver.ex_destroy_firewall(
            self.driver.ex_get_firewall(firewall_name))

    def list(self):
        """
        List all paths in a dictionary structure.
        """
        firewalls = self.driver.ex_list_firewalls()
        fw_info = {}

        def add_rule(fw_info, source, dest, rule):
            if source not in fw_info:
                fw_info[source] = {}
            if dest not in fw_info[source]:
                fw_info[source][dest] = []
            fw_info[source][dest].append(rule)

        for firewall in firewalls:
            # TODO: This is for a poc, I need to find a real way to find what's
            # provisioned by butter.
            if not firewall.name.startswith("bu-"):
                continue
            for rule in firewall.allowed:
                for port in rule["ports"]:
                    logger.debug('Found allowed port %s in firewall', port)
                    for target_tag in firewall.target_tags:
                        logger.debug('Found target %s in firewall', target_tag)
                        if not firewall.source_tags:
                            add_rule(fw_info, "0.0.0.0/0", target_tag,
                                     {"protocol": "tcp", "port": port})
                            continue
                        for source_tag in firewall.source_tags:
                            add_rule(fw_info, source_tag, target_tag,
                                     {"protocol": "tcp", "port": port})
        return fw_info

    def graph(self):
        """
        List all paths in a graph string.
        """
        paths = self.list()
        graph_string = "\n"
        for from_node, to_info in paths.items():
            for to_node, path_info, in to_info.items():
                for path in path_info:
                    graph_string += ("%s -(%s:%s)-> %s\n" %
                                     (from_node,
                                      path["protocol"],
                                      path["port"],
                                      to_node))
        return graph_string

    def internet_accessible(self, network_name, subnetwork_name, port):
        """
        Return true if the given network is internet accessible.
        """
        paths = self.list()
        if "0.0.0.0/0" in paths:
            target_tag = "%s-%s" % (network_name, subnetwork_name)
            if target_tag in paths["0.0.0.0/0"]:
                for path in paths["0.0.0.0/0"][target_tag]:
                    if int(path["port"]) == int(port):
                        return True
        return False

    def has_access(self, network, from_name, to_name, port):
        """
        Return true if there's a path between the services.
        """
        target_tag = "%s-%s" % (network, to_name)
        source_tag = "%s-%s" % (network, from_name)
        logger.info('Looking for path from %s to %s on port %s', source_tag,
                    target_tag, 80)
        paths = self.list()
        logger.info('Found paths %s', paths)
        if source_tag in paths:
            if target_tag in paths[source_tag]:
                for path in paths[source_tag][target_tag]:
                    if int(path["port"]) == int(port):
                        return True
        return False
