import math
import logging

from libcloud.common.google import ResourceNotFoundError

from butter.util.blueprint import InstancesBlueprint
from butter.util.subnet_generator import generate_subnets
from butter.util.exceptions import NotEnoughIPSpaceException
from butter.providers.gce.driver import get_gce_driver

logger = logging.getLogger(__name__)

# TODO: Figure out how to set these placement options
DEFAULT_BASE_CIDR = "10.0.0.0/16"
DEFAULT_REGION = "us-east1"


class SubnetworkClient(object):

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)

    def _canonicalize_subnet_info(self, subnetwork):
        return {
            "Id": subnetwork.id,
            "Name": subnetwork.name,
            "Network": subnetwork.network.name,
            "CidrBlock": subnetwork.cidr,
            "Region": subnetwork.region.name,
            "AvailabilityZone": "N/A",
        }

    def create(self, network_name, subnetwork_name, blueprint):
        """
        Create a group of subnetworks in "network_name" named "subnetwork_name"
        with blueprint file at "blueprint".
        """
        logger.info('Creating subnetwork %s in %s with blueprint %s',
                    subnetwork_name, network_name, blueprint)

        # Provision subnets across zones
        subnets_info = []
        instances_blueprint = InstancesBlueprint(blueprint)
        max_count = instances_blueprint.max_count()
        prefix = 32 - int(math.log(max_count, 2))
        region = DEFAULT_REGION
        # In google compute engine we provision instances across availability
        # zones, not subnets.  This means we only provision one subnetwork and
        # will stripe instances across azs within that.
        #
        # TODO: Figure out the interface for this and warn the user.
        for cidr in self._carve_subnets(network_name, prefix=prefix, count=1):
            try:
                # This is odd...  Because subnet names are globally unique, we
                # need to do some namespacing to not conflict.  TODO: Are they
                # globally unique even in different networks?
                full_name = "%s-%s" % (network_name, subnetwork_name)
                subnet_info = self._gce_provision_subnet(full_name, cidr,
                                                         region, network_name)
            except Exception as exception:
                logger.info('Exception provisioning subnetwork: %s', exception)
                raise exception
            subnets_info.append(subnet_info)
        return subnets_info

    def discover(self, network_name, subnetwork_name):
        """
        Discover a group of subnetworks in "network_name" named
        "subnetwork_name".
        """
        logger.info('Discovering subnetwork %s, %s', network_name,
                    subnetwork_name)
        full_name = "%s-%s" % (network_name, subnetwork_name)
        all_subnetworks = self.driver.ex_list_subnetworks()
        # TODO: Filter on region?
        subnets = [sn for sn in all_subnetworks if
                   sn.network.name == network_name and
                   sn.name == full_name]
        return [self._canonicalize_subnet_info(sn) for sn in subnets]

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy a group of subnetworks named "subnetwork_name" in
        "network_name".
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

        Example:

            butter.subnetwork.list()

        """
        logger.info('Listing subnetworks')
        subnets = self.driver.ex_list_subnetworks()
        subnets_info = {}
        for subnet in subnets:
            subnetwork_name = subnet.name.replace("%s-" % subnet.network.name,
                                                  "")
            if subnet.network.name not in subnets_info:
                subnets_info[subnet.network.name] = {}
            if subnetwork_name not in subnets_info[subnet.network.name]:
                subnets_info[subnet.network.name][subnetwork_name] = []
            subnets_info[subnet.network.name][subnetwork_name].append(
                self._canonicalize_subnet_info(subnet))
        logger.info('Found subnetworks: %s', subnets_info)
        return subnets_info

    def _carve_subnets(self, network_name, prefix=28, count=3):
        # Get existing subnets, to make sure we don't overlap CIDR blocks
        all_subnetworks = self.driver.ex_list_subnetworks()
        existing_subnets = [subnetwork for subnetwork in all_subnetworks if
                            subnetwork.network.name == network_name]
        existing_cidrs = [subnet.cidr for subnet in existing_subnets]

        # Finally, iterate the list of all subnets of the given prefix that can
        # fit in the given VPC
        subnets = []
        for new_cidr in generate_subnets(DEFAULT_BASE_CIDR, existing_cidrs,
                                         prefix):
            subnets.append(str(new_cidr))
            if len(subnets) == count:
                return subnets
        raise NotEnoughIPSpaceException("Could not allocate %s subnets with "
                                        "prefix %s in vpc %s" %
                                        (count, prefix, network_name))

    def _gce_provision_subnet(self, name, cidr, region, network_name):
        subnetwork = self.driver.ex_create_subnetwork(name, cidr, network_name,
                                                      region)
        return self._canonicalize_subnet_info(subnetwork)
