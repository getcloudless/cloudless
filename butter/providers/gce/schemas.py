"""
Schemas of the results returned by various API calls for GCE.
"""
from butter.types.common import Network, Subnetwork, Instance

def canonicalize_network_info(network):
    """
    Convert what is returned from GCE into the butter standard format.
    """
    return Network(name=network.name, network_id=network.id, cidr_block=network.cidr)

def canonicalize_subnetwork_info(subnetwork):
    """
    Convert what is returned from GCE into the butter standard format.
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
    Convert what is returned from GCE into the butter standard format.
    """
    return Instance(
        instance_id=node.uuid,
        public_ip=node.public_ips[0],
        private_ip=node.private_ips[0],
        state=node.state)

def canonicalize_node_size(node):
    """
    Given a node description from the GCE API returns the canonical butter
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
