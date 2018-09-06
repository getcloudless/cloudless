"""
Cloudless Paths on AWS

This is a the AWS implmentation for the paths API, a high level interface to add
routes between services, doing the conversion to security groups and firewall
rules.
"""
import ipaddress

import cloudless.providers.aws.service
from cloudless.providers.aws.impl.asg import ASG
from cloudless.providers.aws.log import logger
from cloudless.util.exceptions import BadEnvironmentStateException, DisallowedOperationException
from cloudless.util.public_blocks import get_public_blocks
from cloudless.types.common import Service, Path, Subnetwork
from cloudless.types.networking import CidrBlock


class PathsClient:
    """
    Client object to interact with paths between resources.
    """
    def __init__(self, driver, credentials, mock=False):
        self.driver = driver
        self.credentials = credentials
        self.mock = mock
        self.service = cloudless.providers.aws.impl.service.ServiceClient(driver, credentials, mock)
        self.asg = ASG(driver, credentials)

    def _extract_service_info(self, source, destination, port):
        """
        Helper to extract the necessary information from the source and destination arguments.
        """

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

        src_ip_permissions = []
        dest_ip_permissions = []
        src_sg_id = None
        dest_sg_id = None
        if isinstance(source, Service):
            src_sg_id = self.asg.get_launch_configuration_security_group(source.network.name,
                                                                         source.name)
            src_ip_permissions.append({
                'FromPort': port,
                'ToPort': port,
                'IpProtocol': 'tcp',
                'UserIdGroupPairs': [
                    {'GroupId': src_sg_id}
                    ]
                })
        if isinstance(source, CidrBlock):
            src_ip_permissions.append({
                'FromPort': port,
                'ToPort': port,
                'IpProtocol': 'tcp',
                'IpRanges': [{
                    'CidrIp': str(source.cidr_block)
                    }]
                })
        if isinstance(destination, Service):
            dest_sg_id = self.asg.get_launch_configuration_security_group(destination.network.name,
                                                                          destination.name)
            dest_ip_permissions.append({
                'FromPort': port,
                'ToPort': port,
                'IpProtocol': 'tcp',
                'UserIdGroupPairs': [
                    {'GroupId': dest_sg_id}
                    ]
                })
        if isinstance(destination, CidrBlock):
            dest_ip_permissions.append({
                'FromPort': port,
                'ToPort': port,
                'IpProtocol': 'tcp',
                'IpRanges': [{
                    'CidrIp': str(destination.cidr_block)
                    }]
                })
        return dest_sg_id, src_sg_id, dest_ip_permissions, src_ip_permissions

    def add(self, source, destination, port):
        """
        Adds a route from "source" to "destination".
        """
        logger.debug("Adding path from %s to %s", source, destination)
        if self.has_access(source, destination, port):
            logger.info("Service %s already has access to %s on port: %s", source, destination,
                        port)
            return True

        # Currently controlling egress in AWS is not supported.  All egress is always allowed.
        if not isinstance(destination, Service):
            raise DisallowedOperationException(
                "Destination must be a cloudless.types.networking.Service object")

        dest_sg_id, _, _, src_ip_permissions = self._extract_service_info(source, destination, port)
        ec2 = self.driver.client("ec2")
        ec2.authorize_security_group_ingress(GroupId=dest_sg_id, IpPermissions=src_ip_permissions)
        return Path(destination.network, source, destination, "tcp", port)

    def remove(self, source, destination, port):
        """
        Remove a route from "source" to "destination".
        """
        # Currently controlling egress in AWS is not supported.  All egress is always allowed.
        if not isinstance(destination, Service):
            raise DisallowedOperationException(
                "Destination must be a cloudless.types.networking.Service object")

        ec2 = self.driver.client("ec2")
        dest_sg_id, _, _, src_ip_permissions = self._extract_service_info(source, destination, port)
        ec2.revoke_security_group_ingress(GroupId=dest_sg_id, IpPermissions=src_ip_permissions)

    # pylint: disable=too-many-locals
    def list(self):
        """
        List all paths and return a dictionary structure representing a graph.
        """
        ec2 = self.driver.client("ec2")
        sg_to_service = {}
        for service in self.service.list():
            sg_id = self.asg.get_launch_configuration_security_group(
                service.network.name, service.name)
            if sg_id in sg_to_service:
                raise BadEnvironmentStateException(
                    "Service %s and %s have same security group: %s" %
                    (sg_to_service[sg_id], service, sg_id))
            sg_to_service[sg_id] = service
        security_groups = ec2.describe_security_groups()

        def make_path(destination, source, rule):
            return Path(destination.network, source, destination, rule["IpProtocol"],
                        rule.get("FromPort", "N/A"))

        def get_cidr_paths(destination, ip_permissions):
            subnets = []
            for ip_range in ip_permissions["IpRanges"]:
                subnets.append(Subnetwork(subnetwork_id=None, name=None,
                                          cidr_block=ip_range["CidrIp"],
                                          region=None, availability_zone=None, instances=[]))
            # We treat an explicit CIDR block as a special case of a service with no name.
            paths = []
            if subnets:
                source = Service(network=None, name=None, subnetworks=subnets)
                paths.append(make_path(destination, source, ip_permissions))
            return paths

        def get_sg_paths(destination, ip_permissions):
            paths = []
            for group in ip_permissions["UserIdGroupPairs"]:
                service = sg_to_service[group["GroupId"]]
                paths.append(make_path(destination, service, ip_permissions))
            return paths

        paths = []
        for security_group in security_groups["SecurityGroups"]:

            if security_group["GroupId"] not in sg_to_service:
                logger.debug("Security group %s is apparently not attached to a service.  Skipping",
                             security_group["GroupId"])
                continue

            service = sg_to_service[security_group["GroupId"]]
            for ip_permissions in security_group["IpPermissions"]:
                logger.debug("ip_permissions: %s", ip_permissions)
                paths.extend(get_cidr_paths(service, ip_permissions))
                paths.extend(get_sg_paths(service, ip_permissions))

        return paths

    def internet_accessible(self, service, port):
        """
        Return true if the given service is accessible on the internet.
        """
        for public_block in get_public_blocks():
            if self.has_access(CidrBlock(public_block), service, port):
                return True
        return False

    def has_access(self, source, destination, port):
        """
        Return true if there is a route from "source" to "destination".
        """
        ec2 = self.driver.client("ec2")
        dest_sg_id, src_sg_id, _, src_ip_permissions = self._extract_service_info(
            source, destination, port)
        security_group = ec2.describe_security_groups(GroupIds=[dest_sg_id])

        def extract_cidr_port(ip_permissions):
            cidr_port_list = []
            for ip_permission in ip_permissions:
                if "IpRanges" in ip_permission:
                    for ip_range in ip_permission["IpRanges"]:
                        cidr_port_list.append({"port": ip_permission["FromPort"],
                                               "cidr": ip_range["CidrIp"]})
            return cidr_port_list

        def sg_allowed(ip_permissions, sg_id, port):
            for ip_permission in ip_permissions:
                if (ip_permission["UserIdGroupPairs"] and
                        ip_permission["FromPort"] == port):
                    for pair in ip_permission["UserIdGroupPairs"]:
                        if "GroupId" in pair and pair["GroupId"] == sg_id:
                            return True
            return False

        ip_permissions = security_group["SecurityGroups"][0]["IpPermissions"]
        logger.debug("ip_permissions: %s", ip_permissions)
        if src_sg_id and sg_allowed(ip_permissions, src_sg_id, port):
            return True

        src_cidr_port_info = extract_cidr_port(src_ip_permissions)
        cidr_port_info = extract_cidr_port(ip_permissions)
        for cidr_port in cidr_port_info:
            if cidr_port["port"] != port:
                continue
            for src_cidr_port in src_cidr_port_info:
                if (ipaddress.IPv4Network(src_cidr_port["cidr"]).overlaps(
                        ipaddress.IPv4Network(cidr_port["cidr"]))):
                    return True
        return False
