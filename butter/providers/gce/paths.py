"""
Butter Paths on GCE

This is a the GCE implmentation for the paths API, a high level interface to add routes between
services, doing the conversion to firewalls and firewall rules.
"""
from butter.providers.gce.driver import get_gce_driver
from butter.providers.gce.log import logger


class PathsClient:
    """
    Client object to interact with paths between resources.
    """

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

        def add_rule(fw_info, network, source, dest, rule):
            # Need to come up with a better way to get the actual service name.
            # Should probably tag the firewalls rules.
            source_service = source.replace("%s-" % network, "")
            dest_service = dest.replace("%s-" % network, "")
            if source_service not in fw_info:
                fw_info[source_service] = {}
            if dest_service not in fw_info[source_service]:
                fw_info[source_service][dest_service] = []
            fw_info[source_service][dest_service].append(rule)

        def handle_target(fw_info, port, target, firewall):
            logger.debug('Found target %s in firewall', target)
            if hasattr(firewall, "source_tags") and firewall.source_tags:
                for source_tag in firewall.source_tags:
                    add_rule(fw_info, firewall.network.name, source_tag, target,
                             {"protocol": "tcp", "port": port})
            if hasattr(firewall, "source_ranges") and firewall.source_ranges:
                for source_range in firewall.source_ranges:
                    add_rule(fw_info, firewall.network.name, source_range,
                             target, {"protocol": "tcp", "port": port})

        fw_info = {}
        for firewall in firewalls:
            if firewall.network.name not in fw_info:
                fw_info[firewall.network.name] = {}

            logger.debug('Found firewall %s', firewall)
            for rule in firewall.allowed:
                for port in rule["ports"]:
                    logger.debug('Found allowed port %s in firewall', port)
                    if hasattr(firewall, "target_tags") and firewall.target_tags:
                        for target_tag in firewall.target_tags:
                            handle_target(fw_info[firewall.network.name], port,
                                          target_tag, firewall)
                    if hasattr(firewall, "target_ranges") and firewall.target_ranges:
                        for target_range in firewall.target_ranges:
                            handle_target(fw_info[firewall.network.name], port,
                                          target_range, firewall)
        return fw_info

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
