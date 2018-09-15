"""
Schemas of the results returned by various API calls for GCE.
"""
import re
from cloudless.types.common import Network, Subnetwork, Instance

def canonicalize_network_info(network):
    """
    Convert what is returned from GCE into the cloudless standard format.
    """
    return Network(name=network.name, network_id=network.id, cidr_block=network.cidr)

def canonicalize_subnetwork_info(subnetwork):
    """
    Convert what is returned from GCE into the cloudless standard format.
    """
    return Subnetwork(
        subnetwork_id=subnetwork.id,
        name=subnetwork.name,
        cidr_block=subnetwork.cidr,
        region=subnetwork.region.name,
        availability_zone=None,
        instances=[])

def canonicalize_instance_info(node):
    """
    Convert what is returned from GCE into the cloudless standard format.
    """
    # This is ugly, but so far it's the only way I've found to get the availability zone from the
    # libcloud API.
    zone_regex = re.search((r'https://www.googleapis.com/compute/v1/projects/.*/zones/(.*)/'
                            'instances/.*$'),
                           node.extra['selfLink'])
    return Instance(
        instance_id=node.uuid,
        public_ip=node.public_ips[0],
        private_ip=node.private_ips[0],
        state=node.state,
        availability_zone=zone_regex.group(1))

def canonicalize_node_size(node):
    """
    Given a node description from the GCE API returns the canonical cloudless
    format.
    """
    return {
        "type": node.name,
        # Memory is returned in "MB"
        "memory": int(node.ram * 1000 * 1000),
        "cpus": float(node.extra["guestCpus"]),
        "storage": node.disk * 1024,
        "location": node.extra["zone"].name
    }
