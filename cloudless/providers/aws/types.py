# pylint: disable=too-few-public-methods
"""
AWS types.

The overall structure is:

    VPC
        |- Subnets
            |- Instance Groups
        |- Security Groups

This is simplified, but it's designed to kind of capture the state of an AWS environment.  There are
some invariants that must be true, like a subnetwork must have a route table or a VPC must have an
internet gateway for example.
"""
import attr

@attr.s
class VPC:
    """
    Simple container to hold VPC information.
    """
    vpc_id = attr.ib(type=str)
    cidr_block = attr.ib(type=str, default=None)
    region = attr.ib(type=str, default=None)

@attr.s
class Subnet:
    """
    Simple container to hold subnetwork information.
    """
    subnetwork_id = attr.ib(type=str)
    vpc_id = attr.ib(type=str)
    name = attr.ib(type=str)
    cidr_block = attr.ib(type=str)
    region = attr.ib(type=str)
    availability_zone = attr.ib(type=str)
    route_table_id = attr.ib(type=str)
    routes = attr.ib(type=list)
    instances = attr.ib(type=list)

@attr.s
class Instance:
    """
    Simple container to hold instance information.
    """
    instance_id = attr.ib(type=str)
    public_ip = attr.ib(type=str)
    private_ip = attr.ib(type=str)
    state = attr.ib(type=str)
    availability_zone = attr.ib(type=str)

@attr.s
class SecurityGroup:
    """
    Simple container to hold security group information.
    """
    security_group_id = attr.ib(type=str)
    ip_permissions = attr.ib(type=list)
