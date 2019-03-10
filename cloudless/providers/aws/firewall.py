"""
Cloudless Firewall Model on AWS
"""
import time
import boto3
from botocore.exceptions import ClientError
import cloudless.model
from cloudless.providers.aws.log import logger
from cloudless.types.common import Firewall
import cloudless.providers.aws.impl.network
from cloudless.util.exceptions import (OperationTimedOut,
                                       BadEnvironmentStateException,
                                       DisallowedOperationException)

class FirewallResourceDriver(cloudless.model.ResourceDriver):
    """
    This class is what gets called when the user is trying to interact with a "Firewall" resource.

    By the time it gets called to interact with "Firewall" resources, it should be fully initialized
    and prepared to interact with the backing provider, because that is all configured up front.

    The way this should work is:

    - Create will create a firewall with the given (required!) name.  It will create it and add all
      the proper firewall rules.  Targets for these rules can be selected by TODO.
    - Apply will attempt to find ONE rule by name and update it.  If that fails it will error, and
      you'll have to pass the ID.
    - Delete will attempt to find ONE rule by name and delete it.  If that fails it will error, and
      you'll have to pass the ID.
    - Get will return all the rules that match the provided resource definition.
    - Flags will return flags that describe any provider specific behavior that the user might care
      about (TODO when we get to GCE).  One will probably be "NATIVE_LABEL_SELECTORS" which will
      mean that the labels when applied to GCE will update when new matchin instances are created,
      but not in AWS.

    Note that the way these rules will actually get "applied" behind the scenes is by attaching them
    to instances.  For now I'm only going to do ingress, so it's always just going to be attached to
    all the destination targets specified (TODO: how to specify?).
    """
    def __init__(self, provider, credentials):
        self.provider = provider
        self.credentials = credentials
        super(FirewallResourceDriver, self).__init__(provider, credentials)
        if "profile" in credentials:
            boto3.setup_default_session(profile_name=credentials["profile"])
        self.driver = boto3
        # Should remove this when I actually have a real model for the network.
        # e.g. model.get("Network", "etc...")
        self.network = cloudless.providers.aws.impl.network.NetworkClient(boto3, mock=False)

    def create(self, resource_definition):
        firewall = resource_definition
        logger.info("Creating firewall: %s", firewall)
        ec2 = self.driver.client("ec2")
        network = self.network.get(firewall.network.name)
        group = ec2.create_security_group(
            VpcId=network.network_id,
            GroupName=firewall.name,
            Description="Firewall:%s created by Cloudless" % firewall.name)
        new_firewall = Firewall(version=firewall.version, name=firewall.name, id=group["GroupId"],
                                network=firewall.network)
        return new_firewall

    def _delete_referencing_rules(self, vpc_id, security_group_id):
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

    def _delete_by_name(self, vpc_id, security_group_name, retries, retry_delay):
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
        self._delete_referencing_rules(vpc_id, security_group_id)
        return self._delete_with_retries(security_group_id, retries, retry_delay)

    def _delete_with_retries(self, security_group_id, retries, retry_delay):
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

    def apply(self, resource_definition):
        firewalls = self.get(resource_definition)
        if len(firewalls) != 1:
            raise DisallowedOperationException(
                "Cannot apply, matched more than one firewall!: %s" % firewalls)
        logger.info("Applying firewall: %s", firewalls[0])
        return firewalls[0]

    def delete(self, resource_definition):
        firewall = resource_definition
        logger.info("Deleting firewall: %s", firewall)
        network = self.network.get(firewall.network.name)
        return self._delete_by_name(network.network_id, firewall.name, 10, 5)

    def get(self, resource_definition):
        ec2 = self.driver.client("ec2")
        firewall = resource_definition
        logger.info("Getting firewall: %s", firewall)
        network = self.network.get(firewall.network.name)
        search_filters = []
        if not firewall.network or not firewall.network.name:
            raise DisallowedOperationException("Network selector required when getting firewall")
        network = self.network.get(firewall.network.name)
        search_filters.append(
            {'Name': 'vpc-id', 'Values': [network.network_id]})
        search_filters.append(
            {'Name': 'group-name', 'Values': [firewall.name]})
        security_groups = ec2.describe_security_groups(Filters=search_filters)
        if len(security_groups["SecurityGroups"]) > 1:
            raise BadEnvironmentStateException(
                "Found multiple security groups with name %s, in vpc %s: %s" %
                (firewall.name, network.network_id, security_groups))
        return [Firewall(version=firewall.version, name=sg["GroupName"], network=firewall.network,
                         id=sg["GroupId"])
                for sg in security_groups["SecurityGroups"]]

    def flags(self, resource_definition):
        return []
