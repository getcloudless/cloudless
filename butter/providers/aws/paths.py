"""
Butter Paths on AWS

This is a the AWS implmentation for the paths API, a high level interface to add
routes between services, doing the conversion to security groups and firewall
rules.
"""
import ipaddress
import boto3

from butter.util import netgraph
from butter.providers.aws import instances
from butter.providers.aws.impl.asg import ASG
from butter.providers.aws.log import logger
from butter.util.exceptions import BadEnvironmentStateException, DisallowedOperationException
from butter.util.public_blocks import get_public_blocks
from butter.types.networking import Service, CidrBlock


class PathsClient:
    """
    Client object to interact with paths between resources.
    """
    def __init__(self, credentials):
        self.credentials = credentials
        self.instances = instances.InstancesClient(credentials)
        self.asg = ASG(credentials)

    def _extract_service_info(self, source, destination, port):
        """
        Helper to extract the necessary information from the source and destination arguments.
        """

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

        src_ip_permissions = []
        dest_ip_permissions = []
        src_sg_id = None
        dest_sg_id = None
        if isinstance(source, Service):
            src_sg_id = self.asg.get_launch_configuration_security_group(source.network_name,
                                                                         source.service_name)
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
            dest_sg_id = self.asg.get_launch_configuration_security_group(destination.network_name,
                                                                          destination.service_name)
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
                "Destination must be a butter.types.networking.Service object")

        dest_sg_id, _, _, src_ip_permissions = self._extract_service_info(source, destination, port)
        ec2 = boto3.client("ec2")
        ec2.authorize_security_group_ingress(GroupId=dest_sg_id, IpPermissions=src_ip_permissions)
        return True

    def remove(self, source, destination, port):
        """
        Remove a route from "source" to "destination".
        """
        # Currently controlling egress in AWS is not supported.  All egress is always allowed.
        if not isinstance(destination, Service):
            raise DisallowedOperationException(
                "Destination must be a butter.types.networking.Service object")

        ec2 = boto3.client("ec2")
        dest_sg_id, _, _, src_ip_permissions = self._extract_service_info(source, destination, port)
        ec2.revoke_security_group_ingress(GroupId=dest_sg_id, IpPermissions=src_ip_permissions)

    # pylint: disable=too-many-locals
    def list(self):
        """
        List all paths and return a dictionary structure representing a graph.
        """
        ec2 = boto3.client("ec2")
        sg_to_service = {}
        for instance in self.instances.list():
            sg_id = self.asg.get_launch_configuration_security_group(
                instance["Network"], instance["Id"])
            if sg_id in sg_to_service:
                raise BadEnvironmentStateException(
                    "Service %s and %s have same security group: %s" %
                    (sg_to_service[sg_id], instance, sg_id))
            sg_to_service[sg_id] = instance
        security_groups = ec2.describe_security_groups()

        def make_rule(source, rule):
            return {
                "source": source,
                "protocol": rule["IpProtocol"],
                "port": rule.get("FromPort", "N/A"),
                "type": "ingress"
            }

        def get_sg_rules(ip_permissions):
            rules = []
            for ip_range in ip_permissions["IpRanges"]:
                source = ip_range.get("CidrIp", "0.0.0.0/0")
                rules.append(make_rule(source, ip_permissions))
            return rules

        def get_cidr_rules(ip_permissions):
            rules = []
            for group in ip_permissions["UserIdGroupPairs"]:
                service = sg_to_service[group["GroupId"]]
                rules.append(make_rule(service["Id"], ip_permissions))
            return rules

        def get_network(security_group_id):
            return sg_to_service[security_group_id]["Network"]

        fw_info = {}
        network = None
        for security_group in security_groups["SecurityGroups"]:
            if security_group["GroupId"] not in sg_to_service:
                continue
            rules = []
            for ip_permissions in security_group["IpPermissions"]:
                logger.debug("ip_permissions: %s", ip_permissions)
                rules.extend(get_cidr_rules(ip_permissions))
                rules.extend(get_sg_rules(ip_permissions))
            network = get_network(security_group["GroupId"])
            if network not in fw_info:
                fw_info[network] = {}
            service = sg_to_service[security_group["GroupId"]]
            fw_info[network][service["Id"]] = rules
        return {network: netgraph.firewalls_to_net(info)
                for network, info in fw_info.items()}

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
        ec2 = boto3.client("ec2")
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
