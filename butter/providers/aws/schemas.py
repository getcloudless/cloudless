"""
Schemas of the results returned by various API calls for AWS.
"""
from butter.util.storage_size_parser import parse_storage_size

def canonicalize_network_info(name, vpc):
    """
    Convert what is returned from AWS into the butter standard format.
    """
    return {
        "Name": name,
        "Id": vpc["VpcId"],
        "CidrBlock": vpc["CidrBlock"]
    }

def canonicalize_subnetwork_info(subnet):
    """
    Convert what is returned from AWS into the butter standard format.
    """
    return {
        "Id": subnet["SubnetId"],
        "CidrBlock": subnet["CidrBlock"],
        "Region": subnet["AvailabilityZone"][:-1],
        "AvailabilityZone": subnet["AvailabilityZone"]
    }

def canonicalize_instances_info(network_name, subnetwork_name, instances):
    """
    Convert what is returned from AWS into the butter standard format.
    """
    return {"Id": subnetwork_name,
            "Network": network_name,
            "Instances": [
                {
                    "Id": instance["InstanceId"],
                    "PrivateIp": instance.get("PrivateIpAddress", "N/A"),
                    "PublicIp": instance.get("PublicIpAddress", "N/A"),
                    "State": instance["State"]["Name"]
                }
                for reservation in instances["Reservations"]
                for instance in reservation["Instances"]
                ]
            }

def canonicalize_node_size(node):
    """
    Given an instance description from the AWS API returns the canonical butter
    format.
    """
    return {
        "type": node["instanceType"],
        "memory": parse_storage_size(node["memory"]),
        "cpus": float(node["vcpu"]),
        "storage": node["storage"],
        "location": node["location"]
    }
