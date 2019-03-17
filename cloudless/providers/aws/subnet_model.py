"""
Cloudless Subnet Model on AWS
"""
import boto3
import cloudless.model
from cloudless.providers.aws.log import logger
from cloudless.types.common import SubnetModel
import cloudless.providers.aws.impl.subnetwork
from cloudless.util.exceptions import DisallowedOperationException

class SubnetResourceDriver(cloudless.model.ResourceDriver):
    """
    Driver for the "Subnet" resource.

    It's a little strange here because subnets in GCE are per region, while subnets in AWS are per
    availability zone.

    The abstraction provided by this resource is "subnet per region" which means that there is a
    translation down to AWS.  When you create a "Subnet", AWS will actually create multiple subnets
    across three regions by default (when possible).  All subnets with the same name, region
    combination will be treated as a single subnet.

    This raises the problem of availability zones and cidr blocks.  In theory the user should be
    allowed to explicitly set these, but for now AWS will hardcode max(3, num_available_in_region)
    availability zones.  Future work to make this explicitly configurable.
    """
    def __init__(self, provider, credentials, model):
        self.provider = provider
        self.credentials = credentials
        super(SubnetResourceDriver, self).__init__(provider, credentials)
        if "profile" in credentials:
            boto3.setup_default_session(profile_name=credentials["profile"])
        self.driver = boto3
        # Should remove this when I actually have a real model for the network.
        # e.g. model.get("Network", "etc...")
        self.subnetwork = cloudless.providers.aws.impl.subnetwork.SubnetworkClient(boto3,
                                                                                   mock=False)
        self.model = model

    def _get_network(self, network):
        if "Network" not in self.model.resources():
            raise DisallowedOperationException(
                "Network model must be registered to use Subnet model.")
        networks = self.model.get("Network", network)
        if len(networks) != 1:
            raise DisallowedOperationException(
                "Matcher must match exactly one network, %s matched %s" % (
                    network, networks))
        return networks[0]

    def create(self, resource_definition):
        subnet = resource_definition
        logger.info("Creating subnet: %s", subnet)
        network = self._get_network(subnet.network)
        old_subnetworks = self.subnetwork.create_from_args(network.name, network.id,
                                                           network.cidr_block, subnet.name, 3,
                                                           subnet.size)
        subnets = [{"id": old_subnetwork.subnetwork_id,
                    "availability_zone": old_subnetwork.availability_zone,
                    "cidr_block": old_subnetwork.cidr_block}
                   for old_subnetwork in old_subnetworks]
        return SubnetModel(version=subnet.version, name=subnet.name, subnets=subnets,)

    def apply(self, resource_definition):
        subnets = self.get(resource_definition)
        if len(subnets) != 1:
            raise DisallowedOperationException(
                "Cannot apply, matched more than one subnet!: %s" % subnets)
        logger.info("Applying subnet: %s", subnets[0])
        return subnets[0]

    def delete(self, resource_definition):
        subnet = resource_definition
        logger.info("Deleting subnet: %s", subnet)
        network = self._get_network(subnet.network)
        return self.subnetwork.destroy_with_args(network.name, network.id, subnet.name)

    def get(self, resource_definition):
        subnet = resource_definition
        network = self._get_network(subnet.network)
        old_subnetworks = self.subnetwork.get_with_args(network.name, subnet.name)
        if not old_subnetworks:
            return []
        subnets = [{"id": old_subnetwork.subnetwork_id,
                    "availability_zone": old_subnetwork.availability_zone,
                    "cidr_block": old_subnetwork.cidr_block}
                   for old_subnetwork in old_subnetworks]
        return [SubnetModel(version=subnet.version, name=subnet.name,
                            subnets=subnets)]

    def flags(self, resource_definition):
        return []
