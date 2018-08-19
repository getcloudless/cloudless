# pylint: disable=no-self-use,missing-docstring
"""
Internet Gateway Impl

Implementation of some common helpers necessary to work with Internet Gateways.
"""


class InternetGateways:
    """
    Internet Gateways helpers class.
    """

    def __init__(self, driver, credentials):
        self.driver = driver
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")

    def route_count(self, vpc_id, igw_id):
        """
        Returns the number of routes that go through the given internet gateway
        in the given VPC.
        """
        ec2 = self.driver.client("ec2")
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
        ec2 = self.driver.client("ec2")
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
