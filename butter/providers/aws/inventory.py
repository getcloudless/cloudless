import boto3


def native():
    """
    The native inventory treats the entire AWS account as the inventory, so
    this will result in networks getting deployed that don't overlap any
    others.
    """
    ec2 = boto3.client("ec2")
    vpcs = ec2.describe_vpcs()
    cidr_blocks = []
    for vpc in vpcs["Vpcs"]:
        cidr_blocks.append(vpc["CidrBlock"])
    return cidr_blocks
