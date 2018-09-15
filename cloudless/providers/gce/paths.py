"""
Cloudless Paths on GCE

This is a the GCE implmentation for the paths API, a high level interface to add routes between
services, doing the conversion to firewalls and firewall rules.
"""
import ipaddress
from libcloud.common.google import ResourceNotFoundError
from cloudless.providers.gce.driver import get_gce_driver
from cloudless.providers.gce.log import logger
from cloudless.types.networking import CidrBlock
from cloudless.util.exceptions import DisallowedOperationException, BadEnvironmentStateException
from cloudless.util.public_blocks import get_public_blocks
from cloudless.providers.gce.service import ServiceClient
from cloudless.types.common import Path, Subnetwork, Service


class PathsClient:
    """
    Client object to interact with paths between resources.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)
        self.service = ServiceClient(credentials)

    # pylint: disable=no-self-use
    def _validate_args(self, source, destination):
        if (not isinstance(source, Service) and not isinstance(destination, Service) and
                not isinstance(source, CidrBlock) and not isinstance(destination, CidrBlock)):
            raise DisallowedOperationException(
                "Source and destination can only be a cloudless.types.networking.Service object or "
                "a cloudless.types.networking.CidrBlock object")

        if not isinstance(destination, Service) and not isinstance(source, Service):
            raise DisallowedOperationException(
                "Either destination or source must be a cloudless.types.networking.Service object")

        if (isinstance(source, Service) and isinstance(destination, Service) and
                source.network != destination.network):
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
            src_tags.append("%s-%s" % (source.network.name, source.name))
        if isinstance(source, CidrBlock):
            src_ranges.append(str(source.cidr_block))
        if isinstance(destination, Service):
            dest_tags.append("%s-%s" % (destination.network.name, destination.name))
        if isinstance(destination, CidrBlock):
            dest_ranges.append(str(destination.cidr_block))
        return src_tags, dest_tags, src_ranges, dest_ranges

    def add(self, source, destination, port):
        """
        Add path between two services on a given port.
        """
        logger.debug('Adding path from %s to %s on port %s', source, destination, port)
        rules = [{"IPProtocol": "tcp", "ports": [int(port)]}]
        src_tags, dest_tags, src_ranges, _ = self._extract_service_info(
            source, destination)
        firewall_name = "bu-%s-%s-%s" % (destination.network.name, destination.name, port)
        try:
            firewall = self.driver.ex_get_firewall(firewall_name)
            if isinstance(source, CidrBlock):
                if not firewall.source_ranges:
                    firewall.source_ranges = []
                firewall.source_ranges.append(str(source.cidr_block))
                logger.debug(firewall.source_ranges)
            if isinstance(source, Service):
                if not firewall.source_tags:
                    firewall.source_tags = []
                source_tag = "%s-%s" % (source.network.name, source.name)
                firewall.source_tags.append(source_tag)
                logger.debug(firewall.source_tags)
            firewall = self.driver.ex_update_firewall(firewall)
        except ResourceNotFoundError:
            logger.debug("Firewall %s not found, creating.", firewall_name)
            firewall = self.driver.ex_create_firewall(firewall_name, allowed=rules,
                                                      network=destination.network.name,
                                                      source_ranges=src_ranges,
                                                      source_tags=src_tags,
                                                      target_tags=dest_tags)
        return Path(destination.network, source, destination, "tcp", port)

    def remove(self, source, destination, port):
        """
        Remove path between two services on a given port.
        """
        logger.debug('Removing path from %s to %s on port %s',
                     source, destination, port)

        firewall_name = "bu-%s-%s-%s" % (destination.network.name, destination.name, port)

        def remove_from_ranges(to_remove, address_ranges):
            logger.debug("Removing %s from %s", to_remove, address_ranges)
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
            logger.debug("New ranges: %s", resulting_ranges)
            return resulting_ranges

        try:
            firewall = self.driver.ex_get_firewall(firewall_name)
            if isinstance(source, CidrBlock):
                firewall.source_ranges = remove_from_ranges(source.cidr_block,
                                                            firewall.source_ranges)
            else:
                source_tag = "%s-%s" % (source.network.name, source.name)
                if firewall.source_tags:
                    firewall.source_tags = [tag for tag in firewall.source_tags
                                            if tag != source_tag]
        except ResourceNotFoundError:
            logger.debug("Firewall %s doesn't exist", firewall_name)
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

        tag_to_service = {}
        for service in self.service.list():
            service_tag = "%s-%s" % (service.network.name, service.name)
            if service_tag in tag_to_service:
                raise BadEnvironmentStateException(
                    "Service %s and %s have same service tag: %s" %
                    (tag_to_service[service_tag], service, service_tag))
            tag_to_service[service_tag] = service

        def make_paths(destination, source, firewall):
            paths = []
            for rule in firewall.allowed:
                for port in rule["ports"]:
                    paths.append(Path(destination.network, source, destination, "tcp", port))
            return paths

        def handle_sources(tag_to_service, destination, firewall):
            paths = []
            if hasattr(firewall, "source_tags") and firewall.source_tags:
                for source_tag in firewall.source_tags:
                    if source_tag in tag_to_service:
                        paths.extend(make_paths(destination, tag_to_service[source_tag], firewall))
            if hasattr(firewall, "source_ranges") and firewall.source_ranges:
                subnets = []
                for source_range in firewall.source_ranges:
                    subnets.append(Subnetwork(subnetwork_id=None, name=None,
                                              cidr_block=source_range, region=None,
                                              availability_zone=None, instances=[]))
                # We treat an explicit CIDR block as a special case of a service with no name.
                if subnets:
                    source = Service(network=None, name=None, subnetworks=subnets)
                    paths.extend(make_paths(destination, source, firewall))
            return paths

        def handle_targets(tag_to_service, firewall):
            paths = []
            if hasattr(firewall, "target_tags") and firewall.target_tags:
                for target_tag in firewall.target_tags:
                    if target_tag in tag_to_service:
                        paths.extend(handle_sources(tag_to_service, tag_to_service[target_tag],
                                                    firewall))
            if hasattr(firewall, "target_ranges") and firewall.target_ranges:
                raise BadEnvironmentStateException(
                    "Found target ranges %s in firewall %s but they are not supported" %
                    (firewall.target_ranges, firewall))
            return paths

        paths = []
        for firewall in firewalls:
            paths.extend(handle_targets(tag_to_service, firewall))
        return paths

    def internet_accessible(self, service, port):
        """
        Return true if the given network is internet accessible.
        """
        paths = self.list()
        for public_block in get_public_blocks():
            source = CidrBlock(public_block)
            self._validate_args(source, service)
            if self._has_access(paths, source, service, port):
                return True
        return False

    def _has_access(self, paths, source, destination, port):
        def cidr_block_access(path, source, destination, port):
            cidr_block = str(source.cidr_block)
            for subnet in path.source.subnetworks:
                if (ipaddress.IPv4Network(subnet.cidr_block).overlaps(
                        ipaddress.IPv4Network(cidr_block)) and
                        path.destination == destination and
                        int(path.port) == port and
                        path.protocol == "tcp"):
                    return True
            return False

        def service_access(path, source, destination, port):
            if (path.source == source and path.destination == destination and int(path.port) == port
                    and path.protocol == "tcp"):
                return True
            return False

        for path in paths:
            if (isinstance(source, Service) and service_access(path, source, destination, port)):
                return True
            if (isinstance(source, CidrBlock) and cidr_block_access(path, source, destination,
                                                                    port)):
                return True
        return False

    def has_access(self, source, destination, port):
        """
        Return true if there's a path between the services.
        """
        logger.debug('Looking for path from %s to %s on port %s', source, destination, 80)
        self._validate_args(source, destination)
        paths = self.list()
        logger.debug('Found paths %s', paths)
        return self._has_access(paths, source, destination, port)
