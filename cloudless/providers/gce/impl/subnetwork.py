"""
Cloudless Subnetwork on GCE

This is a the GCE implmentation for the subnetwork API, a high level interface to manage groups of
subnets.  This is mainly for internal use, as the instances API is the real high level interface.

This is also in flux because of the differences between how cloud providers manage subnetworks, so
it might go away.
"""
import math

from libcloud.common.google import ResourceNotFoundError

from cloudless.util.blueprint import ServiceBlueprint, NetworkBlueprint
from cloudless.util.subnet_generator import generate_subnets
from cloudless.util.exceptions import NotEnoughIPSpaceException
from cloudless.providers.gce.driver import get_gce_driver
from cloudless.providers.gce.log import logger
from cloudless.providers.gce.schemas import canonicalize_subnetwork_info

DEFAULT_REGION = "us-east1"


class SubnetworkClient:
    """
    Client object to manage subnetworks.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)

    def create(self, network_name, subnetwork_name, blueprint):
        """
        Create a group of subnetworks in "network_name" named "subnetwork_name"
        with blueprint file at "blueprint".
        """
        logger.info('Creating subnetwork %s in %s with blueprint %s',
                    subnetwork_name, network_name, blueprint)

        # Provision subnets across zones
        subnets_info = []
        instances_blueprint = ServiceBlueprint.from_file(blueprint)
        max_count = instances_blueprint.max_count()
        prefix = 32 - int(math.log(max_count, 2))
        region = DEFAULT_REGION
        # In google compute engine we provision instances across availability
        # zones, not subnets.  This means we only provision one subnetwork and
        # will stripe instances across azs within that.
        for cidr in self._carve_subnets(network_name, blueprint, prefix=prefix, count=1):
            try:
                full_name = "%s-%s" % (network_name, subnetwork_name)
                subnet_info = self._gce_provision_subnet(full_name, cidr,
                                                         region, network_name)
            except Exception as exception:
                logger.info('Exception provisioning subnetwork: %s', exception)
                raise exception
            subnets_info.append(subnet_info)
        return subnets_info

    def get(self, network, subnetwork_name):
        """
        Get a group of subnetworks in "network" named "subnetwork_name".
        """
        logger.info('Discovering subnetwork %s, %s', network.name, subnetwork_name)
        full_name = "%s-%s" % (network.name, subnetwork_name)
        all_subnetworks = self.driver.ex_list_subnetworks()
        subnets = [sn for sn in all_subnetworks if
                   sn.network.name == network.name and
                   sn.name == full_name]
        return [canonicalize_subnetwork_info(sn) for sn in subnets]

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy a group of subnetworks named "subnetwork_name" in "network_name".
        """
        logger.info('Destroying subnetwork group %s, %s', network_name,
                    subnetwork_name)
        full_name = "%s-%s" % (network_name, subnetwork_name)
        all_subnetworks = self.driver.ex_list_subnetworks()
        subnets = [sn for sn in all_subnetworks if
                   sn.network.name == network_name and
                   sn.name == full_name]
        region = DEFAULT_REGION
        destroy_results = []
        for subnet in subnets:
            try:
                logger.info('Destroying subnetwork %s', subnet.name)
                subnet_info = self.driver.ex_get_subnetwork(subnet.name,
                                                            region)
            except ResourceNotFoundError as not_found:
                logger.info("Caught exception destroying subnetwork, "
                            "ignoring: %s", not_found)
                return True
            destroy_results.append(self.driver.ex_destroy_subnetwork(
                subnet_info))
        return destroy_results

    def list(self):
        """
        List all subnetworks.
        """
        logger.info('Listing subnetworks')
        subnets = self.driver.ex_list_subnetworks()
        subnets_info = {}
        for subnet in subnets:
            if subnet.network.name == "default":
                continue
            subnetwork_name = subnet.name.replace("%s-" % subnet.network.name, "")
            if subnet.network.name not in subnets_info:
                subnets_info[subnet.network.name] = {}
            if subnetwork_name not in subnets_info[subnet.network.name]:
                subnets_info[subnet.network.name][subnetwork_name] = []
            subnets_info[subnet.network.name][subnetwork_name].append(
                canonicalize_subnetwork_info(subnet))
        logger.info('Found subnetworks: %s', subnets_info)
        return subnets_info

    def _carve_subnets(self, network_name, blueprint, prefix=28, count=3):
        # Get existing subnets, to make sure we don't overlap CIDR blocks
        all_subnetworks = self.driver.ex_list_subnetworks()
        existing_subnets = [subnetwork for subnetwork in all_subnetworks if
                            subnetwork.network.name == network_name]
        existing_cidrs = [subnet.cidr for subnet in existing_subnets]

        if blueprint:
            network_blueprint = NetworkBlueprint.from_file(blueprint)
        else:
            network_blueprint = NetworkBlueprint("")
        allowed_private_cidr = network_blueprint.get_allowed_private_cidr()
        subnets = generate_subnets(allowed_private_cidr, existing_cidrs, prefix, count)
        if len(subnets) < count:
            raise NotEnoughIPSpaceException("Could not allocate %s subnets with "
                                            "prefix %s in network %s" %
                                            (count, prefix, network_name))
        return subnets

    def _gce_provision_subnet(self, name, cidr, region, network_name):
        subnetwork = self.driver.ex_create_subnetwork(name, cidr, network_name,
                                                      region)
        return canonicalize_subnetwork_info(subnetwork)
