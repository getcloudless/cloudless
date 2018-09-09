"""
Schemas of the results returned by various API calls for AWS.
"""
from cloudless.types.common import Network, Subnetwork, Instance
from cloudless.util.storage_size_parser import parse_storage_size

def canonicalize_network_info(name, vpc, region):
    """
    Convert what is returned from AWS into the cloudless standard format.
    """
    return Network(name=name, network_id=vpc["VpcId"], cidr_block=vpc["CidrBlock"], region=region)

def canonicalize_subnetwork_info(name, subnet, instances):
    """
    Convert what is returned from AWS into the cloudless standard format.
    """
    return Subnetwork(name=name, subnetwork_id=subnet["SubnetId"], cidr_block=subnet["CidrBlock"],
                      region=subnet["AvailabilityZone"][:-1],
                      availability_zone=subnet["AvailabilityZone"],
                      instances=instances)

def canonicalize_instance_info(instance):
    """
    Convert what is returned from AWS into the cloudless standard format.
    """
    return Instance(instance_id=instance["InstanceId"],
                    private_ip=instance.get("PrivateIpAddress", "N/A"),
                    public_ip=instance.get("PublicIpAddress", "N/A"),
                    state=instance["State"]["Name"],
                    availability_zone=instance["Placement"]["AvailabilityZone"])

def canonicalize_node_size(node):
    """
    Given an instance description from the AWS API returns the canonical cloudless
    format.
    """
    return {
        "type": node["instanceType"],
        "memory": parse_storage_size(node["memory"]),
        "cpus": float(node["vcpu"]),
        "storage": node["storage"],
        "location": node["location"]
    }
