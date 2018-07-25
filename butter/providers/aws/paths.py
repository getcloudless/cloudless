"""
Butter Paths

This is a high level interface to add routes between services, busting holes in
security groups and firewall rules.

For now this calls directly into butter, but eventually I might find a way to
decouple it.
"""

import logging
import boto3

from butter.util import netgraph
from butter.providers.aws import instances
from butter.providers.aws.impl.asg import (ASG, AsgName)

logger = logging.getLogger(__name__)


class PathsClient(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.instances = instances.InstancesClient(credentials)
        self.asg = ASG(credentials)

    def expose(self, network_name, subnetwork_name, port):
        """
        Make this launch configuration open to the internet.

        This involves opening up the security group and exposing the network
        layer which will route through the internet gateway.
        """
        ec2 = boto3.client("ec2")
        security_group_id = self.asg.get_launch_configuration_security_group(
            network_name, subnetwork_name)
        ec2.authorize_security_group_ingress(GroupId=security_group_id,
                                             IpPermissions=[{
                                                 'FromPort': port,
                                                 'ToPort': port,
                                                 'IpProtocol': 'tcp',
                                                 'IpRanges': [{
                                                     'CidrIp': '0.0.0.0/0'
                                                 }]
                                             }]
                                             )

    def add(self, network, from_name, to_name, port):
        """
        Adds a route from "from_name" to "to_name".
        """
        ec2 = boto3.client("ec2")
        to_sg_id = self.asg.get_launch_configuration_security_group(network,
                                                                    to_name)
        from_sg_id = self.asg.get_launch_configuration_security_group(
            network, from_name)
        ec2.authorize_security_group_ingress(GroupId=to_sg_id,
                                             IpPermissions=[{
                                                 'FromPort': port,
                                                 'ToPort': port,
                                                 'IpProtocol': 'tcp',
                                                 'UserIdGroupPairs': [
                                                     {'GroupId': from_sg_id}
                                                 ]
                                             }]
                                             )

    def remove(self, network, from_name, to_name, port):
        """
        Remove a route from "from_name" to "to_name".
        """
        ec2 = boto3.client("ec2")
        to_sg_id = self.asg.get_launch_configuration_security_group(network,
                                                                    to_name)
        from_sg_id = self.asg.get_launch_configuration_security_group(
            network, from_name)
        ec2.revoke_security_group_ingress(GroupId=to_sg_id,
                                          IpPermissions=[{
                                              'FromPort': port,
                                              'ToPort': port,
                                              'IpProtocol': 'tcp',
                                              'UserIdGroupPairs': [
                                                  {'GroupId': from_sg_id}
                                              ]
                                          }]
                                          )

    def list(self):
        ec2 = boto3.client("ec2")
        sg_to_service = {}
        for instance in self.instances.list():
            asg_name = AsgName(name_string=instance["Id"])
            sg_id = self.asg.get_launch_configuration_security_group(
                asg_name.network, asg_name.subnetwork)
            if sg_id not in sg_to_service:
                sg_to_service[sg_id] = [instance["Id"]]
            else:
                sg_to_service[sg_id].append(instance["Id"])
        security_groups = ec2.describe_security_groups()
        fw_info = {}
        for security_group in security_groups["SecurityGroups"]:
            if security_group["GroupId"] not in sg_to_service:
                continue
            rules = []
            for rule in security_group["IpPermissions"]:
                if rule["IpRanges"]:
                    source = rule["IpRanges"][0].get("CidrIp", "0.0.0.0/0")
                elif rule["UserIdGroupPairs"]:
                    group_id = rule["UserIdGroupPairs"][0]["GroupId"]
                    source = sg_to_service[group_id][0]
                else:
                    source = "0.0.0.0/0"
                rules.append({
                    "source": source,
                    "protocol": rule["IpProtocol"],
                    "port": rule.get("FromPort", "N/A"),
                    "type": "ingress"
                })
            fw_info[sg_to_service[security_group["GroupId"]][0]] = rules
        return netgraph.firewalls_to_net(fw_info)

    def graph(self):
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
        ec2 = boto3.client("ec2")
        security_group_id = self.asg.get_launch_configuration_security_group(
            network_name, subnetwork_name)
        # TODO: Actually do something real here.  Right now this is half
        # implemented so this is just to get the end to end test passing with
        # the basic skeleton.
        security_group = ec2.describe_security_groups(
            GroupIds=[security_group_id])
        ip_permissions = security_group["SecurityGroups"][0]["IpPermissions"]
        for ip_permission in ip_permissions:
            if (ip_permission["IpRanges"] and
                    ip_permission["FromPort"] == port):
                return True
        return False

    def has_access(self, network, from_name, to_name, port):
        ec2 = boto3.client("ec2")
        to_group_id = self.asg.get_launch_configuration_security_group(
            network, to_name)
        from_group_id = self.asg.get_launch_configuration_security_group(
            network, from_name)
        # TODO: Actually do something real here.  Right now this is half
        # implemented so this is just to get the end to end test passing with
        # the basic skeleton.
        security_group = ec2.describe_security_groups(GroupIds=[to_group_id])
        ip_permissions = security_group["SecurityGroups"][0]["IpPermissions"]
        logger.debug("ip_permissions: %s", ip_permissions)
        for ip_permission in ip_permissions:
            if (ip_permission["UserIdGroupPairs"] and
                    ip_permission["FromPort"] == port):
                for pair in ip_permission["UserIdGroupPairs"]:
                    if "GroupId" in pair and pair["GroupId"] == from_group_id:
                        return True
        return False
