import logging

from butter.providers.gce.driver import get_gce_driver

from butter.util.blueprint import InstancesBlueprint
from butter.util.instance_fitter import InstanceFitter
from butter.util.exceptions import (DisallowedOperationException,
                                    BadEnvironmentStateException)
from butter.providers.gce import subnetwork
from butter.providers.gce.impl.firewalls import Firewalls

logger = logging.getLogger(__name__)

DEFAULT_REGION = "us-east1"


class InstancesClient(object):

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)
        self.subnetwork = subnetwork.SubnetworkClient(credentials)
        self.firewalls = Firewalls(self.driver)

    def _canonicalize_node_info(self, node):
        return {
            "Id": node.uuid,
            "PublicIp": node.public_ips[0],
            "PrivateIp": node.private_ips[0],
            "State": node.state
        }

    def create(self, network_name, subnetwork_name, blueprint):
        logger.info('Creating instances %s, %s with blueprint %s',
                    network_name, subnetwork_name, blueprint)
        # TODO: Handle return values here, for now I just care that it didn't
        # throw an exception.
        self.subnetwork.create(network_name, subnetwork_name,
                               blueprint=blueprint)
        instances_blueprint = InstancesBlueprint(blueprint)
        az_count = instances_blueprint.availability_zone_count()
        image_name = instances_blueprint.image()
        node_info = []
        # TODO: Get latest image if there are duplicate names, and support
        # wildcards.
        images = [image for image in self.driver.list_images() if image.name ==
                  image_name]
        if not images:
            raise DisallowedOperationException("Could not find image named %s"
                                               % image_name)
        image = images[0]
        instance_fitter = InstanceFitter()
        instance_type = instance_fitter.get_fitting_instance("gce", blueprint)
        for zone in self._get_availability_zones():
            if az_count == 0:
                return node_info
            # TODO: This namespacing hasn't been figured out, since subnetworks
            # have to be globally unique in a region.
            full_subnetwork_name = "%s-%s" % (network_name, subnetwork_name)
            instance_name = "%s-%s" % (full_subnetwork_name, az_count)
            startup_script = instances_blueprint.runtime_scripts()
            metadata = [
                {"key": "startup-script", "value": startup_script},
                {"key": "network", "value": network_name},
                {"key": "subnetwork", "value": subnetwork_name}
            ]
            logger.info('Creating instance %s in zone %s', instance_name, zone)
            node = self.driver.create_node(instance_name, instance_type, image,
                                           location=zone,
                                           ex_network=network_name,
                                           ex_subnetwork=full_subnetwork_name,
                                           external_ip="ephemeral",
                                           ex_metadata=metadata,
                                           ex_tags=[full_subnetwork_name])
            az_count = az_count - 1
            node_info.append(self._canonicalize_node_info(node))
        return node_info

    def discover(self, network_name, subnetwork_name):
        logger.info('Discovering instances %s, %s', network_name,
                    subnetwork_name)
        node_results = []
        node_name = "%s-%s" % (network_name, subnetwork_name)
        for node in self.driver.list_nodes():
            if node.name.startswith(node_name):
                node_results.append(self._canonicalize_node_info(node))
        return {"Id": node_name, "Instances": node_results}

    def destroy(self, network_name, subnetwork_name):
        logger.info('Destroying instances: %s, %s', network_name,
                    subnetwork_name)
        destroy_results = []
        node_name = "%s-%s" % (network_name, subnetwork_name)
        for node in self.driver.list_nodes():
            if node.name.startswith(node_name):
                logger.info('Destroying instance: %s', node.name)
                destroy_results.append(self.driver.destroy_node(node))
        subnetwork_destroy = self.subnetwork.destroy(network_name,
                                                     subnetwork_name)
        self.firewalls.cleanup_orphaned_firewalls()
        return {"Subnetwork": subnetwork_destroy,
                "Instances": destroy_results}

    def list(self):
        """
        List all instance groups.

        Example:

            butter.instances.list()

        """
        logger.info('Listing instances')
        instances_info = {}
        for node in self.driver.list_nodes():
            logger.info("Node metadata: %s", node.extra["metadata"])
            metadata = node.extra["metadata"]["items"]
            network_names = [item["value"] for item in metadata
                             if item["key"] == "network"]
            if len(network_names) != 1:
                raise BadEnvironmentStateException(
                    "Found node with no network in metadata: %s" % metadata)
            subnetwork_names = [item["value"] for item in metadata
                                if item["key"] == "subnetwork"]
            if len(subnetwork_names) != 1:
                raise BadEnvironmentStateException(
                    "Found node with no subnetwork in metadata: %s" % metadata)
            instance_group_name = "%s-%s" % (network_names[0],
                                             subnetwork_names[0])
            if instance_group_name not in instances_info:
                instances_info[instance_group_name] = []
            instance_info = self._canonicalize_node_info(node)
            instances_info[instance_group_name].append(instance_info)
        return [{"Id": group, "Instances": instances} for (group, instances) in
                instances_info.items()]

    def _get_availability_zones(self):
        zones = self.driver.ex_list_zones()
        return [zone for zone in zones if zone.name.startswith(DEFAULT_REGION)]
