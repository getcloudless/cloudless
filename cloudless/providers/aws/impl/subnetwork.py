"""
Cloudless Subnetwork on AWS

This is a the AWS implmentation for the subnetwork API, a high level interface to manage groups of
subnets.  This is mainly for internal use, as the instances API is the real high level interface.

This is also in flux because of the differences between how cloud providers manage subnetworks, so
it might go away.
"""
import math
import time

from cloudless.util.blueprint import ServiceBlueprint
from cloudless.util.exceptions import BadEnvironmentStateException
import cloudless.providers.aws.impl.network
from cloudless.providers.aws.impl.internet_gateways import InternetGateways
from cloudless.providers.aws.impl.subnets import Subnets
from cloudless.providers.aws.impl.availability_zones import AvailabilityZones
from cloudless.providers.aws.log import logger
from cloudless.providers.aws.schemas import canonicalize_subnetwork_info

RETRY_COUNT = int(60)
RETRY_DELAY = float(1.0)


class SubnetworkClient:
    """
    Client object to manage subnetworks.
    """

    def __init__(self, driver, credentials, mock=False):
        self.driver = driver
        self.credentials = credentials
        self.network = cloudless.providers.aws.impl.network.NetworkClient(driver, credentials, mock)
        self.internet_gateways = InternetGateways(driver, credentials)
        self.subnets = Subnets(driver, credentials)
        self.availability_zones = AvailabilityZones(driver, credentials, mock)

    def create(self, network, subnetwork_name, blueprint):
        """
        Provision the subnets with AWS.
        """
        # 1. Create subnets across availability zones.
        subnets_info = []
        instances_blueprint = ServiceBlueprint.from_file(blueprint)
        az_count = instances_blueprint.availability_zone_count()
        max_count = instances_blueprint.max_count()
        prefix = 32 - int(math.log(max_count / az_count, 2))
        cidr_az_list = zip(self.subnets.carve_subnets(network.network_id, network.cidr_block,
                                                      prefix, az_count),
                           self.availability_zones.get_availability_zones())
        for subnet_cidr, availability_zone in cidr_az_list:
            subnet_info = canonicalize_subnetwork_info(
                None,
                self.subnets.create(subnetwork_name, subnet_cidr, availability_zone,
                                    network.network_id, RETRY_COUNT, RETRY_DELAY), [])
            subnets_info.append(subnet_info)

        # 2. Make sure we have a route to the internet.
        self._make_internet_routable(network, subnetwork_name)

        return subnets_info

    def _make_internet_routable(self, network, subnetwork_name):
        """
        Create an internet gateway for this network and add routes to it for
        all subnets.

        Steps:

        1. Discover current VPC.
        2. Create and attach internet gateway only if it doesn't exist.
        4. Add route to it from all subnets.
        """
        ec2 = self.driver.client("ec2")

        # 1. Get the internet gateway for this VPC.
        igw_id = self.internet_gateways.get_internet_gateway(network.network_id)

        # 2. Add route to it from all subnets.
        subnet_ids = [subnet_info.subnetwork_id for subnet_info
                      in self.get(network, subnetwork_name)]
        for subnet_id in subnet_ids:
            subnet_filter = {'Name': 'association.subnet-id', 'Values': [subnet_id]}
            route_tables = ec2.describe_route_tables(Filters=[subnet_filter])
            if len(route_tables["RouteTables"]) != 1:
                raise Exception("Expected to find exactly one route table: %s"
                                % route_tables)
            route_table = route_tables["RouteTables"][0]
            ec2.create_route(RouteTableId=route_table["RouteTableId"],
                             GatewayId=igw_id,
                             DestinationCidrBlock="0.0.0.0/0")

    def get(self, network, subnetwork_name):
        """
        Get a subnetwork group in "network" named "subnetwork_name".
        """
        logger.debug("Getting subnet %s in network %s", subnetwork_name, network)
        subnetworks = self.list()
        for network_name, subnetwork_info in subnetworks.items():
            if network_name != network.name:
                continue
            if subnetwork_name in subnetwork_info["subnetworks"]:
                return subnetwork_info["subnetworks"][subnetwork_name]
        return None

    def destroy(self, network, subnetwork_name):
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
        ec2 = self.driver.client("ec2")
        subnet_ids = [subnet_info.subnetwork_id for subnet_info
                      in self.get(network, subnetwork_name)]

        # 1. Discover the current VPC.
        dc_id = network.network_id

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
        """
        Return a list of all subnetworks.
        """
        ec2 = self.driver.client("ec2")

        def get_name(tagged_resource):
            if "Tags" not in tagged_resource:
                return None
            for tag in tagged_resource["Tags"]:
                if tag["Key"] == "Name":
                    return tag["Value"]
            return None

        # 1. List all VPCs and subnets
        subnet_info = {}
        subnets = ec2.describe_subnets()
        networks = self.network.list()
        networks_by_id = {}

        # 2. Key networks by ID
        for network in networks:
            networks_by_id[network.network_id] = network

        # 3. Group subnets by network
        for subnet in subnets["Subnets"]:

            # 3.a. Get the network for this subnet
            if subnet["VpcId"] not in networks_by_id:
                raise BadEnvironmentStateException(
                    "Found subnet with VPC ID %s not in %s" % (subnet["VpcId"], networks_by_id))
            network = networks_by_id[subnet["VpcId"]]

            # 3.b. Add this network to the result hash if it's not there
            if network.name not in subnet_info:
                subnet_info[network.name] = {"network":network, "subnetworks":{}}

            # 3.c. Get subnetwork group name and add empty list if this is the first
            subnet_name = get_name(subnet)
            if not subnet_name:
                continue
            if subnet_name not in subnet_info[network.name]["subnetworks"]:
                subnet_info[network.name]["subnetworks"][subnet_name] = []

            # 3.d. Add this subnetwork to the subnetwork group
            subnet_info[network.name]["subnetworks"][subnet_name].append(
                canonicalize_subnetwork_info(subnet_name, subnet, []))

        logger.debug("Returning subnet_info: %s", subnet_info)
        return subnet_info
