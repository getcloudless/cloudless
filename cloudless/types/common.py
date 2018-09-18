# pylint: disable=too-few-public-methods
"""
Common types.

The overall structure is:

    Network
      |- Services
          |- Subnetworks
              |- Instances

The Network object does not contain any Services to avoid circular dependencies.  However, the
Services object and children include all the remaining parts of the heirarchy.

This is because the API only has two entry points: a Network or a Service.  The Service contains
what Network it's in and encapsulates all information about it.  Additional functions to only
extract instances or subnetworks could be layered on top of this.
"""
import attr

@attr.s
class Network:
    """
    Simple container to hold network information.
    """
    name = attr.ib(type=str)
    network_id = attr.ib(type=str)
    cidr_block = attr.ib(type=str, default=None)
    region = attr.ib(type=str, default=None)

@attr.s
class Service:
    """
    Simple container to hold service information.
    """
    network = attr.ib(type=Network)
    name = attr.ib(type=str)
    subnetworks = attr.ib(type=list)

@attr.s
class Subnetwork:
    """
    Simple container to hold subnetwork information.
    """
    subnetwork_id = attr.ib(type=str)
    name = attr.ib(type=str)
    cidr_block = attr.ib(type=str)
    region = attr.ib(type=str)
    availability_zone = attr.ib(type=str)
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
class Path:
    """
    Simple container to hold path information.
    """
    network = attr.ib(type=Network)
    source = attr.ib()
    destination = attr.ib()
    protocol = attr.ib(type=str)
    port = attr.ib(type=int)

@attr.s
class Image:
    """
    Simple container to hold image information.
    """
    name = attr.ib(type=str)
    image_id = attr.ib(type=str)
    created_at = attr.ib(type=str)
