"""
AWS Cloudless Model

DECISION:
    - To implement the plan I do NOT NEED any of this for the cloud providers.  I should stick with
      my abstracted models for as long as I can.  I can still do the fancy transactions/commit
      behavior.  This is a new way of structuring things and I need to start with the abstract way
      first.
    - ALSO, the TECHNICAL DEBT with this is best fixed as a real step, not combined with a complete
      model change.  I just need to go through smartly and encapsulate things better.
"""
from collections import OrderedDict
import difflib
import yaml
from cloudless.providers.aws.types import VPC, Subnet, Instance, SecurityGroup
from cloudless.util.exceptions import DisallowedOperationException
from cloudless.util.yaml_representer import represent_ordereddict

class AWSProjectModel:
    """
    The abstract state of an AWS Project.  This is actually just a set of graphs with services as
    nodes and paths as edges.  Each network is a single graph.

    This will not have a commit method.  That must be implemented by the provider.
    """

    # pylint:disable=too-many-instance-attributes
    def __init__(self, vpcs, subnets, instances, security_groups):
        self.vpcs = vpcs
        self.subnets = subnets
        self.instances = instances
        self.security_groups = security_groups
        self.new_vpcs = []
        self.new_subnets = []
        self.new_instances = []
        self.new_security_groups = []

    def to_yaml(self, include_new=False):
        """
        Dump this network as YAML.
        """
        yaml.add_representer(OrderedDict, represent_ordereddict)

        def instance_info(instance):
            return OrderedDict([
                ('id', instance.instance_id),
                ('public_ip', instance.public_ip),
                ('private_ip', instance.private_ip),
                ('state', instance.state),
                ('availability_zone', instance.availability_zone)])

        def subnet_info(subnet):
            return OrderedDict([
                ('name', subnet.name),
                ('id', subnet.subnetwork_id),
                ('block', subnet.cidr_block),
                ('region', subnet.region),
                ('availability_zone', subnet.availability_zone),
                ('instances', [instance_info(instance) for instance in subnet.instances])])

        def vpc_info(vpc):
            subnets = list(self.subnets)
            if include_new:
                subnets.extend(self.new_subnets)
            subnets = [subnet for subnet in subnets if subnet.vpc_id == vpc.vpc_id]
            return OrderedDict([
                ('vpc_id', vpc.vpc_id),
                ('vpc_cidr_block', vpc.cidr_block),
                ('vpc_region', vpc.region),
                ('subnets', [subnet_info(subnet) for subnet in subnets])])

        vpcs = list(self.vpcs)
        if include_new:
            vpcs.extend(self.new_vpcs)

        return yaml.dump([vpc_info(vpc) for vpc in vpcs], default_flow_style=False)

    def add_vpc(self, vpc):
        """
        Add a vpc to this model.  This will show up in various output commands, but is not yet
        committed.
        """
        if not isinstance(vpc, VPC):
            raise DisallowedOperationException(
                "Argument to add_vpc must be of type cloudless.providers.aws.types.VPC")
        if self.new_vpcs or self.new_subnets or self.new_instances or self.new_security_groups:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_vpcs.append(vpc)

    def add_subnet(self, subnet):
        """
        Add a subnet to this model.  This will show up in various output commands, but is not yet
        committed.
        """
        if not isinstance(subnet, Subnet):
            raise DisallowedOperationException(
                "Argument to add_vpc must be of type cloudless.providers.aws.types.Subnet")
        if self.new_vpcs or self.new_subnets or self.new_instances or self.new_security_groups:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_subnets.append(subnet)

    def add_instance(self, instance):
        """
        Add a instance to this model.  This will show up in various output commands, but is not yet
        committed.
        """
        if not isinstance(instance, Instance):
            raise DisallowedOperationException(
                "Argument to add_vpc must be of type cloudless.providers.aws.types.Instance")
        if self.new_vpcs or self.new_instances or self.new_instances or self.new_security_groups:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_instances.append(instance)

    def add_security_group(self, security_group):
        """
        Add a security_group to this model.  This will show up in various output commands, but is
        not yet committed.
        """
        if not isinstance(security_group, SecurityGroup):
            raise DisallowedOperationException(
                "Argument to add_vpc must be of type cloudless.providers.aws.types.SecurityGroup")
        if self.new_vpcs or self.new_subnets or self.new_instances or self.new_security_groups:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_security_groups.append(security_group)

    def to_yaml_diff(self):
        """
        Print a diff between old and new to show what changed.
        """
        old_yaml = self.to_yaml().split("\n")
        new_yaml = self.to_yaml(include_new=True).split("\n")
        return "\n".join(difflib.ndiff(old_yaml, new_yaml))
