"""
Schemas of the results returned by various API calls for AWS.
"""

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

def canonicalize_instances_info(asg, instances):
    """
    Convert what is returned from AWS into the butter standard format.
    """
    return {"Id": asg["AutoScalingGroupName"],
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
