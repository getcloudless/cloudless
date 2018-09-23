"""
Cloudless Network on AWS

This component should allow for intuitive and transparent control over networks, which are the top
level containers for groups of instances/services.  This is the AWS implementation.
"""
import time

from cloudless.util.blueprint import NetworkBlueprint
from cloudless.util.subnet_generator import generate_subnets
from cloudless.util.exceptions import (BadEnvironmentStateException,
                                       DisallowedOperationException,
                                       OperationTimedOut,
                                       NotEnoughIPSpaceException)
from cloudless.providers.aws.impl.internet_gateways import InternetGateways
from cloudless.providers.aws.schemas import canonicalize_network_info
from cloudless.providers.aws.log import logger

RETRY_COUNT = int(60)
RETRY_DELAY = float(1.0)

class NetworkClient:
    """
    Cloudless Network Client Object for AWS

    This is the object through which all network related calls are made for AWS.
    """

    def __init__(self, driver, credentials, mock=False):
        self.driver = driver
        self.credentials = credentials
        self.mock = mock
        self.internet_gateways = InternetGateways(driver, credentials)

    def create(self, name, blueprint):
        """
        Create new network named "name" with blueprint file at "blueprint".
        """
        ec2 = self.driver.client("ec2")
        if self.get(name):
            raise DisallowedOperationException(
                "Found existing VPC named: %s" % name)
        if blueprint:
            network_blueprint = NetworkBlueprint.from_file(blueprint)
        else:
            network_blueprint = NetworkBlueprint("")
        allocation_blocks = network_blueprint.get_allowed_private_cidr()
        def get_cidr(prefix, address_range_includes, address_range_excludes):
            for address_range_include in address_range_includes:
                for cidr in generate_subnets(address_range_include, address_range_excludes, prefix,
                                             count=1):
                    return str(cidr)
            raise NotEnoughIPSpaceException("Could not allocate network of size "
                                            "%s in %s, excluding %s" %
                                            (prefix, address_range_includes,
                                             address_range_includes))

        vpc = ec2.create_vpc(CidrBlock=get_cidr(
            network_blueprint.get_prefix(), [allocation_blocks], []))
        vpc_id = vpc["Vpc"]["VpcId"]
        try:
            creation_retries = 0
            while creation_retries < RETRY_COUNT:
                try:
                    ec2.create_tags(Resources=[vpc_id],
                                    Tags=[{"Key": "Name",
                                           "Value": name}])
                    if not self.get(name):
                        time.sleep(float(RETRY_DELAY))
                    else:
                        break
                except ec2.exceptions.ClientError as client_error:
                    logger.debug("Received exception tagging VPC: %s", client_error)
                    time.sleep(float(RETRY_DELAY))
                    creation_retries = creation_retries + 1
                    if creation_retries >= RETRY_COUNT:
                        raise OperationTimedOut(
                            "Cannot find created VPC: %s" % vpc_id)
        except OperationTimedOut as exception:
            ec2.delete_vpc(VpcId=vpc_id)
            raise exception
        return canonicalize_network_info(name, vpc["Vpc"],
                                         self.driver.session.Session().region_name)

    # pylint: disable=no-self-use
    def get(self, name):
        """
        Get a network named "name" and return some data about it.
        """
        ec2 = self.driver.client("ec2")
        deployment_filter = {'Name': "tag:Name",
                             'Values': [name]}
        vpcs = ec2.describe_vpcs(Filters=[deployment_filter])
        if len(vpcs["Vpcs"]) > 1:
            raise BadEnvironmentStateException(
                "Expected to find at most one VPC named: %s, "
                "output: %s" % (name, vpcs))
        elif not vpcs["Vpcs"]:
            return None
        else:
            return canonicalize_network_info(name, vpcs["Vpcs"][0],
                                             self.driver.session.Session().region_name)

    # pylint: disable=no-self-use
    def destroy(self, network):
        """
        Destroy a network given the provided network object.
        """
        ec2 = self.driver.client("ec2")

        # Check to see if we have any subnets, otherwise bail out
        subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id',
                                                 'Values': [network.network_id]}])
        if subnets["Subnets"]:
            message = "Found subnets in network, cannot delete: %s" % subnets
            logger.error(message)
            raise DisallowedOperationException(message)

        # Delete internet gateway if it's no longer referenced
        igw = ec2.describe_internet_gateways(
            Filters=[{'Name': 'attachment.vpc-id',
                      'Values': [network.network_id]}])
        igw_id = None
        if len(igw["InternetGateways"]) == 1:
            igw_id = igw["InternetGateways"][0]["InternetGatewayId"]
        elif len(igw["InternetGateways"]) > 1:
            raise Exception(
                "Invalid response from describe_internet_gateways: %s" %
                igw)
        if igw_id and not self.internet_gateways.route_count(network.network_id,
                                                             igw_id):
            ec2.detach_internet_gateway(InternetGatewayId=igw_id,
                                        VpcId=network.network_id)
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)

        # Since we check above that there are no subnets, and therefore nothing
        # deployed in this VPC, for now assume it is safe to delete.
        security_groups = ec2.describe_security_groups(
            Filters=[{'Name': 'vpc-id', 'Values': [network.network_id]}])
        for security_group in security_groups["SecurityGroups"]:
            if security_group["GroupName"] == "default":
                continue
            logger.info("Deleting security group: %s",
                        security_group["GroupName"])
            ec2.delete_security_group(GroupId=security_group["GroupId"])

        # Delete internet gateway, also safe because our subnets are gone.
        igws = ec2.describe_internet_gateways(
            Filters=[{'Name': 'attachment.vpc-id', 'Values': [network.network_id]}])
        logger.info("Deleting internet gateways: %s", igws)
        for igw in igws["InternetGateways"]:
            logger.info("Deleting internet gateway: %s", igw)
            igw_id = igw["InternetGatewayId"]
            ec2.detach_internet_gateway(InternetGatewayId=igw_id,
                                        VpcId=network.network_id)
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)

        # Now, actually delete the VPC
        try:
            deletion_result = ec2.delete_vpc(VpcId=network.network_id)
        except ec2.exceptions.ClientError as client_error:
            if client_error.response['Error']['Code'] == 'DependencyViolation':
                logger.info("Dependency violation deleting VPC: %s", client_error)
            raise client_error
        return deletion_result

    # pylint: disable=no-self-use
    def list(self):
        """
        List all networks.
        """
        ec2 = self.driver.client("ec2")

        def get_deployment_tag(vpc):
            if "Tags" not in vpc:
                return None
            for tag in vpc["Tags"]:
                if tag["Key"] == "Name":
                    return tag["Value"]
            return None

        vpcs = ec2.describe_vpcs()
        result = []
        for vpc in vpcs["Vpcs"]:
            name = get_deployment_tag(vpc)
            result.append(canonicalize_network_info(name, vpc,
                                                    self.driver.session.Session().region_name))
        return result
