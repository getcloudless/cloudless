# pylint: disable=no-self-use,missing-docstring
"""
Security Groups Impl

Implementation of some common helpers necessary to work with security groups.
"""

import time
from botocore.exceptions import ClientError
from cloudless.util.exceptions import (OperationTimedOut,
                                       BadEnvironmentStateException)
from cloudless.providers.aws.log import logger


class SecurityGroups:
    """
    Security Groups helpers class.
    """

    def __init__(self, driver, credentials):
        self.driver = driver
        if credentials:
            # Currently only using the global defaults is supported
            raise NotImplementedError("Passing credentials not implemented")

    def create(self, name, vpc_id):
        ec2 = self.driver.client("ec2")
        group = ec2.create_security_group(VpcId=vpc_id, GroupName=name,
                                          Description=name)
        return group["GroupId"]

    def delete_referencing_rules(self, vpc_id, security_group_id):
        """
        Removes all rules referencing the given security group in the given
        VPC, so it can be safely deleted.
        """
        ec2 = self.driver.client("ec2")
        logger.info("Deleting rules referencing %s in %s", security_group_id,
                    vpc_id)
        security_groups = ec2.describe_security_groups(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        for security_group in security_groups["SecurityGroups"]:
            logger.info("Checking security group: %s", security_group_id)
            for rule in security_group["IpPermissions"]:
                for uigp in rule["UserIdGroupPairs"]:
                    if "GroupId" not in uigp:
                        continue
                    if uigp["GroupId"] != security_group_id:
                        continue
                    rule_to_remove = {}
                    rule_to_remove["FromPort"] = rule["FromPort"]
                    rule_to_remove["ToPort"] = rule["ToPort"]
                    rule_to_remove["IpProtocol"] = rule["IpProtocol"]
                    rule_to_remove["UserIdGroupPairs"] = [{"GroupId":
                                                           uigp["GroupId"]}]
                    logger.info("Revoking rule: %s in security group %s",
                                rule_to_remove, security_group)
                    ec2.revoke_security_group_ingress(
                        GroupId=security_group["GroupId"],
                        IpPermissions=[rule_to_remove])

    def delete_by_name(self, vpc_id, security_group_name, retries, retry_delay):
        ec2 = self.driver.client("ec2")
        logger.info("Deleting security group %s in %s", security_group_name,
                    vpc_id)
        security_groups = ec2.describe_security_groups(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'group-name', 'Values': [security_group_name]}
                ])
        if not security_groups["SecurityGroups"]:
            return True
        if len(security_groups["SecurityGroups"]) > 1:
            raise BadEnvironmentStateException(
                "Found multiple security groups with name %s, in vpc %s: %s" %
                (security_group_name, vpc_id, security_groups))
        security_group_id = security_groups["SecurityGroups"][0]["GroupId"]
        self.delete_referencing_rules(vpc_id, security_group_id)
        return self.delete_with_retries(security_group_id, retries, retry_delay)

    def delete_with_retries(self, security_group_id, retries, retry_delay):
        ec2 = self.driver.client("ec2")

        def attempt_delete_security_group(security_group_id):
            try:
                ec2.delete_security_group(GroupId=security_group_id)
                return True
            except ClientError as client_error:
                logger.info("Recieved exception destroying security group: %s",
                            client_error)
                if (client_error.response["Error"]["Code"] ==
                        "DependencyViolation"):
                    return False
                raise client_error

        deletion_retries = 0
        while deletion_retries < retries:
            if attempt_delete_security_group(security_group_id):
                break
            deletion_retries = deletion_retries + 1
            if deletion_retries >= retries:
                raise OperationTimedOut(
                    "Exceeded max retries while deleting security group: %s"
                    % security_group_id)
            time.sleep(float(retry_delay))
