import math
import time
import logging
import boto3

from butter.util.blueprint import InstancesBlueprint
from butter.util.exceptions import BadEnvironmentStateException
from butter.providers.aws import network
from butter.providers.aws.impl.internet_gateways import InternetGateways
from butter.providers.aws.impl.subnets import Subnets

logger = logging.getLogger(__name__)

RETRY_COUNT = int(60)
RETRY_DELAY = float(1.0)


class SubnetworkClient(object):
    def __init__(self, credentials):
        self.credentials = credentials
        self.network = network.NetworkClient(credentials)
        self.internet_gateways = InternetGateways(credentials)
        self.subnets = Subnets(credentials)

    def _canonicalize_subnet_info(self, subnet):
        return {
            "Id": subnet["SubnetId"],
            "CidrBlock": subnet["CidrBlock"],
            "Region": subnet["AvailabilityZone"][:-1],
            "AvailabilityZone": subnet["AvailabilityZone"]
        }

    def _get_availability_zones(self):
        ec2 = boto3.client("ec2")
        try:
            availability_zones = ec2.describe_availability_zones()
            return [az["ZoneName"]
                    for az in availability_zones["AvailabilityZones"]]
        except Exception as exception:
            logger.info("Caught exception getting azs: %s", exception)
            # TODO: XXX: Moto does not have this function supported...  So I
            # need to fix that before this code can be reasonable again,
            # because otherwise it just fails.
            return ["us-east-1a", "us-east-1b", "us-east-1c"]

    def create(self, network_name, subnetwork_name, blueprint):
        """
        Provision the subnets with AWS.

        This actually has a few steps.

        1. Get ID of VPC to provision subnets in, or create if nonexistent.
        2. Create subnets across availability zones.
        """
        # 1. Get ID ov VPC to provision subnets in.
        dc_info = self.network.discover(network_name)
        if not dc_info:
            raise BadEnvironmentStateException("Network %s not found" %
                                               network_name)

        # 2. Create subnets across availability zones.
        subnets_info = []
        availability_zones = self._get_availability_zones()
        instances_blueprint = InstancesBlueprint(blueprint)
        az_count = instances_blueprint.availability_zone_count()
        max_count = instances_blueprint.max_count()
        prefix = 32 - int(math.log(max_count / az_count, 2))
        cidr_az_list = zip(self.subnets.carve_subnets(dc_info["Id"],
                                                      dc_info["CidrBlock"],
                                                      prefix, az_count),
                           availability_zones)
        for subnet_cidr, availability_zone in cidr_az_list:
            subnet_info = self._canonicalize_subnet_info(
                self.subnets.create(subnetwork_name, subnet_cidr,
                                    availability_zone, dc_info["Id"],
                                    RETRY_COUNT, RETRY_DELAY))
            subnets_info.append(subnet_info)

        # 3. Make sure we have a route to the internet.
        # TODO: Make this configurable.
        self._make_internet_routable(network_name, subnetwork_name)

        return subnets_info

    def _make_internet_routable(self, network_name, subnetwork_name):
        """
        Create an internet gateway for this network and add routes to it for
        all subnets.

        Steps:

        1. Discover current VPC.
        2. Create and attach internet gateway only if it doesn't exist.
        4. Add route to it from all subnets.
        """
        ec2 = boto3.client("ec2")

        # 1. Discover current VPC.
        vpc_id = self.network.discover(network_name)["Id"]

        # 2. Get the internet gateway for this VPC.
        igw_id = self.internet_gateways.get_internet_gateway(vpc_id)

        # 3. Add route to it from all subnets.
        subnet_ids = [subnet_info["Id"] for subnet_info
                      in self.discover(network_name, subnetwork_name)]
        for subnet_id in subnet_ids:
            subnet_filter = {'Name': 'association.subnet-id',
                             'Values': [subnet_id]}
            route_tables = ec2.describe_route_tables(Filters=[subnet_filter])
            if len(route_tables["RouteTables"]) != 1:
                raise Exception("Expected to find exactly one route table: %s"
                                % route_tables)
            route_table = route_tables["RouteTables"][0]
            ec2.create_route(RouteTableId=route_table["RouteTableId"],
                             GatewayId=igw_id,
                             DestinationCidrBlock="0.0.0.0/0")

    def discover(self, network_name, subnetwork_name):
        ec2 = boto3.client("ec2")
        dc_id = self.network.discover(network_name)["Id"]
        subnets = ec2.describe_subnets(Filters=[{'Name': "vpc-id",
                                                 'Values': [dc_id]},
                                                {'Name': "tag:Name",
                                                 'Values': [subnetwork_name]}])
        return [self._canonicalize_subnet_info(subnet)
                for subnet in subnets["Subnets"]]

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy all networks represented by this object.  Also destroys the
        underlying VPC if it's empty.

        Steps:

        1. Discover the current VPC.
        2. Destroy route tables.
            2.a. Disassociate and delete route table.
            2.b. Delete non referenced internet gateways.
        3. Delete all subnets.
        4. Wait until subnets are deleted.
        """
        ec2 = boto3.client("ec2")
        subnet_ids = [subnet_info["Id"] for subnet_info
                      in self.discover(network_name, subnetwork_name)]

        # 1. Discover the current VPC.
        dc_id = self.network.discover(network_name)["Id"]

        # 2. Destroy route tables.
        def delete_route_table(route_table):
            # 2.a. Disassociate and delete route table.
            associations = route_table["Associations"]
            for association in associations:
                ec2.disassociate_route_table(
                    AssociationId=association["RouteTableAssociationId"])
            ec2.delete_route_table(
                RouteTableId=route_table["RouteTableId"])
            # 2.b. Delete non referenced internet gateways.
            routes = route_table["Routes"]
            for route in routes:
                if "GatewayId" in route and route["GatewayId"] != "local":
                    igw_id = route["GatewayId"]
                    if not self.internet_gateways.route_count(dc_id, igw_id):
                        ec2.detach_internet_gateway(InternetGatewayId=igw_id,
                                                    VpcId=dc_id)
                        ec2.delete_internet_gateway(InternetGatewayId=igw_id)

        for subnet_id in subnet_ids:
            subnet_filter = {'Name': 'association.subnet-id',
                             'Values': [subnet_id]}
            route_tables = ec2.describe_route_tables(Filters=[subnet_filter])
            if len(route_tables["RouteTables"]) > 1:
                raise BadEnvironmentStateException(
                    "Expected to find at most one route table associated "
                    "with: %s, output: %s" % (subnet_id, route_tables))
            if len(route_tables["RouteTables"]) == 1:
                delete_route_table(route_tables["RouteTables"][0])

        # 3. Delete all subnets.
        for subnet_id in subnet_ids:
            self.subnets.delete(subnet_id, RETRY_COUNT, RETRY_DELAY)

        # 4. Wait until subnets are deleted.
        remaining_subnets = ec2.describe_subnets(
            Filters=[{'Name': 'vpc-id',
                      'Values': [dc_id]}])
        remaining_subnet_ids = [subnet["SubnetId"] for subnet
                                in remaining_subnets["Subnets"]]
        retries = 0
        while (any(i in subnet_ids for i in remaining_subnet_ids)
               and retries < 720):
            logger.info("Found remaining subnets: %s", remaining_subnet_ids)
            remaining_subnets = ec2.describe_subnets(
                Filters=[{'Name': 'vpc-id',
                          'Values': [dc_id]}])
            remaining_subnet_ids = [subnet["SubnetId"] for subnet
                                    in remaining_subnets["Subnets"]]
            retries = retries + 1
            time.sleep(1)

    def list(self):
        ec2 = boto3.client("ec2")

        def get_name(tagged_resource):
            if "Tags" not in tagged_resource:
                return None
            for tag in tagged_resource["Tags"]:
                if tag["Key"] == "Name":
                    return tag["Value"]
            return None

        subnet_info = {}
        subnets = ec2.describe_subnets()
        for subnet in subnets["Subnets"]:
            vpcs = ec2.describe_vpcs(VpcIds=[subnet["VpcId"]])
            vpc_name = get_name(vpcs["Vpcs"][0])
            subnet_name = get_name(subnet)
            if vpc_name not in subnet_info:
                subnet_info[vpc_name] = {}
            if subnet_name not in subnet_info[vpc_name]:
                subnet_info[vpc_name][subnet_name] = []
            subnet_info[vpc_name][subnet_name].append(
                self._canonicalize_subnet_info(subnet))
        return subnet_info
