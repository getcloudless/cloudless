# pylint: disable=no-self-use,missing-docstring
"""
Subnets Impl

Implementation of some common helpers necessary to work with AWS subnets.
"""

import time

from cloudless.util.subnet_generator import generate_subnets
from cloudless.util.exceptions import (NotEnoughIPSpaceException,
                                       OperationTimedOut)
from cloudless.providers.aws.log import logger


class Subnets:
    """
    Subnets helpers class.
    """

    def __init__(self, driver, credentials):
        self.driver = driver
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")

    def carve_subnets(self, vpc_id, vpc_cidr, prefix=28, count=3):
        ec2 = self.driver.client("ec2")

        # Get existing subnets, to make sure we don't overlap CIDR blocks
        existing_subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id',
                                                          'Values': [vpc_id]}])
        existing_cidrs = [subnet["CidrBlock"]
                          for subnet in existing_subnets["Subnets"]]

        # Finally, iterate the list of all subnets of the given prefix that can
        # fit in the given VPC
        subnets = generate_subnets(vpc_cidr, existing_cidrs, prefix, count)
        if len(subnets) < count:
            raise NotEnoughIPSpaceException("Could not allocate %s subnets with "
                                            "prefix %s in vpc %s" %
                                            (count, prefix, vpc_id))
        return subnets

    def delete(self, subnet_id, retry_count, retry_delay):
        ec2 = self.driver.client("ec2")
        deletion_retries = 0
        while deletion_retries < retry_count:
            try:
                ec2.delete_subnet(SubnetId=subnet_id)
            except ec2.exceptions.ClientError as client_error:
                if (client_error.response['Error']['Code'] ==
                        'DependencyViolation'):
                    # A dependency violation might be transient if
                    # something is being actively deleted by AWS, so sleep
                    # and retry if we get this specific error.
                    time.sleep(float(retry_delay))
                elif (client_error.response['Error']['Code'] ==
                      'InvalidSubnetID.NotFound'):
                    # Just return successfully if the subnet is already gone
                    # for some reason.
                    return
                else:
                    raise client_error
                deletion_retries = deletion_retries + 1
                if deletion_retries >= retry_count:
                    raise OperationTimedOut(
                        "Failed to delete subnet: %s" % str(client_error))

    # pylint: disable=too-many-arguments,too-many-locals
    def create(self, subnetwork_name, subnet_cidr,
               availability_zone, dc_id, retry_count, retry_delay):
        """
        Provision a single subnet with a route table and the proper tags.
        """
        ec2 = self.driver.client("ec2")
        created_subnet = ec2.create_subnet(CidrBlock=subnet_cidr,
                                           AvailabilityZone=availability_zone,
                                           VpcId=dc_id)
        subnet_id = created_subnet["Subnet"]["SubnetId"]
        route_table = ec2.create_route_table(VpcId=dc_id)
        route_table_id = route_table["RouteTable"]["RouteTableId"]
        ec2.associate_route_table(RouteTableId=route_table_id,
                                  SubnetId=subnet_id)
        creation_retries = 0
        while creation_retries < retry_count:
            try:
                ec2.create_tags(Resources=[subnet_id],
                                Tags=[{"Key": "Name",
                                       "Value": subnetwork_name}])
                subnets = ec2.describe_subnets(
                    Filters=[{'Name': "vpc-id",
                              'Values': [dc_id]},
                             {'Name': "tag:Name",
                              'Values': [subnetwork_name]}])
                subnet_ids = [subnet["SubnetId"] for subnet
                              in subnets["Subnets"]]
                if subnet_id not in subnet_ids:
                    time.sleep(float(retry_delay))
                else:
                    break
            except ec2.exceptions.ClientError as client_error:
                logger.info("Caught exception creating tags: %s", client_error)
                time.sleep(float(retry_delay))
                creation_retries = creation_retries + 1
                if creation_retries >= retry_count:
                    raise OperationTimedOut(
                        "Cannot find created Subnet: %s" % subnet_id)
        return created_subnet["Subnet"]
