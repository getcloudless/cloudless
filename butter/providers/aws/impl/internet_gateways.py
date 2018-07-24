"""
Internet Gateway Impl

Implementation of some common helpers necessary to work with Internet Gateways.
"""

import logging
import boto3

logger = logging.getLogger(__name__)


class InternetGateways(object):
    """
    Internet Gateways helpers class.
    """

    def __init__(self, credentials):
        # TODO: Actually use credentials instead of only relying on boto3's
        # default behavior of loading them from the environment.
        pass

    def route_count(self, vpc_id, igw_id):
        """
        Returns the number of routes that go through the given internet gateway
        in the given VPC.
        """
        ec2 = boto3.client("ec2")
        count = 0
        route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id',
                                                           'Values':
                                                           [vpc_id]}])
        for route_table in route_tables["RouteTables"]:
            for route in route_table["Routes"]:
                if "GatewayId" in route and route["GatewayId"] == igw_id:
                    count = count + 1
        return count

    def get_internet_gateway(self, vpc_id):
        """
        Get the internet gateway for the VPC, creating it if necessary.
        """
        ec2 = boto3.client("ec2")
        igw = ec2.describe_internet_gateways(Filters=[{'Name':
                                                       'attachment.vpc-id',
                                                       'Values': [vpc_id]}])
        if len(igw["InternetGateways"]) == 1:
            igw_id = igw["InternetGateways"][0]["InternetGatewayId"]
        elif not igw["InternetGateways"]:
            igw = ec2.create_internet_gateway()
            igw_id = igw["InternetGateway"]["InternetGatewayId"]
            ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
        else:
            raise Exception(
                "Found more than one internet gateway attached to VPC: %s"
                % igw)
        return igw_id
