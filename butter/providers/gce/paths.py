"""
Butter Paths on GCE

This is a the GCE implmentation for the paths API, a high level interface to add routes between
services, doing the conversion to firewalls and firewall rules.
"""
import ipaddress
from libcloud.common.google import ResourceNotFoundError
from butter.providers.gce.driver import get_gce_driver
from butter.providers.gce.log import logger
from butter.types.networking import Service, CidrBlock
from butter.util.exceptions import DisallowedOperationException
from butter.util.public_blocks import get_public_blocks


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

    # pylint: disable=no-self-use
    def _validate_args(self, source, destination):
        if (not isinstance(source, Service) and not isinstance(destination, Service) and
                not isinstance(source, CidrBlock) and not isinstance(destination, CidrBlock)):
            raise DisallowedOperationException(
                "Source and destination can only be a butter.types.networking.Service object or a "
                "butter.types.networking.CidrBlock object")

        if not isinstance(destination, Service) and not isinstance(source, Service):
            raise DisallowedOperationException(
                "Either destination or source must be a butter.types.networking.Service object")

        if (isinstance(source, Service) and isinstance(destination, Service) and
                source.network_name != destination.network_name):
            raise DisallowedOperationException(
                "Destination and source must be in the same network if specified as services")

    def _extract_service_info(self, source, destination):
        """
        Helper to extract the necessary information from the source and destination arguments.
        """
        self._validate_args(source, destination)
        src_tags = []
        dest_tags = []
        src_ranges = []
        dest_ranges = []
        if isinstance(source, Service):
            src_tags.append("%s-%s" % (source.network_name, source.service_name))
        if isinstance(source, CidrBlock):
            src_ranges.append(str(source.cidr_block))
        if isinstance(destination, Service):
            dest_tags.append("%s-%s" % (destination.network_name, destination.service_name))
        if isinstance(destination, CidrBlock):
            dest_ranges.append(str(destination.cidr_block))
        return src_tags, dest_tags, src_ranges, dest_ranges

    def add(self, source, destination, port):
        """
        Add path between two services on a given port.
        """
        logger.info('Adding path from %s to %s on port %s', source, destination, port)
        rules = [{"IPProtocol": "tcp", "ports": [port]}]
        src_tags, dest_tags, src_ranges, _ = self._extract_service_info(
            source, destination)
        firewall_name = "bu-%s-%s-%s" % (destination.network_name, destination.service_name, port)
        try:
            firewall = self.driver.ex_get_firewall(firewall_name)
            if isinstance(source, CidrBlock):
                if not firewall.source_ranges:
                    firewall.source_ranges = []
                firewall.source_ranges.append(str(source.cidr_block))
                logger.info(firewall.source_ranges)
            if isinstance(source, Service):
                if not firewall.source_tags:
                    firewall.source_tags = []
                source_tag = "%s-%s" % (source.network_name, source.service_name)
                firewall.source_tags.append(source_tag)
                logger.info(firewall.source_tags)
            return self.driver.ex_update_firewall(firewall)
        except ResourceNotFoundError:
            logger.info("Firewall %s not found, creating.", firewall_name)
            return self.driver.ex_create_firewall(firewall_name, allowed=rules,
                                                  network=destination.network_name,
                                                  source_ranges=src_ranges,
                                                  source_tags=src_tags,
                                                  target_tags=dest_tags)

    def remove(self, source, destination, port):
        """
        Remove path between two services on a given port.
        """
        logger.info('Removing path from %s to %s on port %s',
                    source, destination, port)

        firewall_name = "bu-%s-%s-%s" % (destination.network_name, destination.service_name, port)

        def remove_from_ranges(to_remove, address_ranges):
            logger.info("Removing %s from %s", to_remove, address_ranges)
            resulting_ranges = []
            if not address_ranges:
                return None
            for address_range in address_ranges:
                remove_net = ipaddress.IPv4Network(to_remove)
                address_range_network = ipaddress.IPv4Network(address_range)
                if remove_net.overlaps(address_range_network):
                    if remove_net.prefixlen > address_range_network.prefixlen:
                        new_range_networks = address_range_network.address_exclude(remove_net)
                        resulting_ranges.extend([str(new_range_network) for new_range_network
                                                 in new_range_networks])
                else:
                    resulting_ranges.extend([str(address_range_network)])
            logger.info("New ranges: %s", resulting_ranges)
            return resulting_ranges

        try:
            firewall = self.driver.ex_get_firewall(firewall_name)
            if isinstance(source, CidrBlock):
                firewall.source_ranges = remove_from_ranges(source.cidr_block,
                                                            firewall.source_ranges)
            else:
                source_tag = "%s-%s" % (source.network_name, source.service_name)
                if firewall.source_tags:
                    firewall.source_tags = [tag for tag in firewall.source_tags
                                            if tag != source_tag]
        except ResourceNotFoundError:
            logger.info("Firewall %s doesn't exist", firewall_name)
            return None

        # We need this because the default is to add "0.0.0.0/0" if these aren't set, which is bad.
        if not firewall.source_tags and not firewall.source_ranges:
            return self.driver.ex_destroy_firewall(firewall)
        return self.driver.ex_update_firewall(firewall)

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

    def internet_accessible(self, service, port):
        """
        Return true if the given network is internet accessible.
        """
        for public_block in get_public_blocks():
            if self.has_access(CidrBlock(public_block), service, port):
                return True
        return False

    def has_access(self, source, destination, port):
        """
        Return true if there's a path between the services.
        """
        logger.info('Looking for path from %s to %s on port %s', source, destination, 80)
        self._validate_args(source, destination)
        paths = self.list()
        logger.info('Found paths %s', paths)

        def cidr_block_access(source, network_name, destination_name, paths):
            cidr_block = str(source.cidr_block)
            for allowed_cidr, destination_info in paths[network_name].items():

                try:
                    ipaddress.IPv4Network(allowed_cidr)
                except ipaddress.AddressValueError as address_value_error:
                    logger.debug('Cannot parse source as CIDR block: %s', address_value_error)
                    continue

                if (ipaddress.IPv4Network(cidr_block).overlaps(
                        ipaddress.IPv4Network(allowed_cidr))):
                    if destination_name in destination_info:
                        for path in destination_info[destination_name]:
                            if int(path["port"]) == int(port):
                                return True
            return False

        def service_access(source, network_name, destination_name, paths):
            source_name = source.service_name
            if source_name in paths[network_name]:
                if destination_name in paths[network_name][source_name]:
                    for path in paths[network_name][source_name][destination_name]:
                        if int(path["port"]) == int(port):
                            return True
            return False


        destination_name = destination.service_name
        network_name = destination.network_name
        if network_name in paths:
            if (isinstance(source, Service) and
                    service_access(source, network_name, destination_name, paths)):
                return True
            if (isinstance(source, CidrBlock) and
                    cidr_block_access(source, network_name, destination_name, paths)):
                return True
        return False
