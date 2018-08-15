"""
Butter Instances on GCE

This is the GCE implmentation for the instances API, a high level interface to manage groups of
instances.
"""
import re

from butter.providers.gce.driver import get_gce_driver

from butter.util.blueprint import InstancesBlueprint
from butter.util.instance_fitter import get_fitting_instance
from butter.util.exceptions import (DisallowedOperationException,
                                    BadEnvironmentStateException)
from butter.providers.gce import subnetwork
from butter.providers.gce.impl.firewalls import Firewalls
from butter.providers.gce.log import logger
from butter.providers.gce.schemas import (canonicalize_instances_info,
                                          canonicalize_node_size)

DEFAULT_REGION = "us-east1"


class InstancesClient:
    """
    Client object to manage instances.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)
        self.subnetwork = subnetwork.SubnetworkClient(credentials)
        self.firewalls = Firewalls(self.driver)

    def create(self, network_name, subnetwork_name, blueprint, template_vars):
        """
        Create a group of instances in "network_name" named "subnetwork_name"
        with blueprint file at "blueprint".
        """
        logger.info('Creating instances %s, %s with blueprint %s and '
                    'template_vars %s', network_name, subnetwork_name,
                    blueprint, template_vars)
        self.subnetwork.create(network_name, subnetwork_name,
                               blueprint=blueprint)
        instances_blueprint = InstancesBlueprint(blueprint, template_vars)
        az_count = instances_blueprint.availability_zone_count()

        def get_image(image_specifier):
            images = [image for image in self.driver.list_images() if re.match(image_specifier,
                                                                               image.name)]
            if not images:
                raise DisallowedOperationException("Could not find image named %s"
                                                   % image_specifier)
            if len(images) > 1:
                raise DisallowedOperationException("Found multiple images for specifier %s: %s"
                                                   % (image_specifier, images))
            return images[0]

        image = get_image(instances_blueprint.image())
        instance_type = get_fitting_instance(self, blueprint)
        for zone in self._get_availability_zones():
            if az_count == 0:
                break
            full_subnetwork_name = "%s-%s" % (network_name, subnetwork_name)
            instance_name = "%s-%s" % (full_subnetwork_name, az_count)
            metadata = [
                {"key": "startup-script", "value":
                 instances_blueprint.runtime_scripts()},
                {"key": "network", "value": network_name},
                {"key": "subnetwork", "value": subnetwork_name}
            ]
            logger.info('Creating instance %s in zone %s', instance_name, zone)
            self.driver.create_node(instance_name, instance_type, image, location=zone,
                                    ex_network=network_name, ex_subnetwork=full_subnetwork_name,
                                    external_ip="ephemeral", ex_metadata=metadata,
                                    ex_tags=[full_subnetwork_name])
            az_count = az_count - 1
        return self.discover(network_name, subnetwork_name)

    def discover(self, network_name, subnetwork_name):
        """
        Discover a group of instances in "network_name" named "subnetwork_name".
        """
        logger.info('Discovering instances %s, %s', network_name,
                    subnetwork_name)
        nodes = []
        node_name = "%s-%s" % (network_name, subnetwork_name)
        for node in self.driver.list_nodes():
            if node.name.startswith(node_name):
                nodes.append(node)
        return canonicalize_instances_info(network_name, subnetwork_name, nodes)

    def destroy(self, network_name, subnetwork_name):
        """
        Destroy a group of instances named "subnetwork_name" in "network_name".
        """
        logger.info('Destroying instances: %s, %s', network_name,
                    subnetwork_name)
        destroy_results = []
        for node in self.driver.list_nodes():
            metadata = node.extra.get("metadata", {}).get("items", [])
            node_network_name = None
            node_subnetwork_name = None
            for item in metadata:
                logger.debug("Found metadata item %s for node %s", item, node)
                if item["key"] == "network":
                    node_network_name = item["value"]
                if item["key"] == "subnetwork":
                    node_subnetwork_name = item["value"]
            if (network_name == node_network_name and
                    subnetwork_name == node_subnetwork_name):
                logger.info('Destroying instance: %s', node.name)
                destroy_results.append(self.driver.destroy_node(node))
        subnetwork_destroy = self.subnetwork.destroy(network_name,
                                                     subnetwork_name)
        self.firewalls.delete_firewall(network_name, subnetwork_name)
        return {"Subnetwork": subnetwork_destroy,
                "Instances": destroy_results}

    def list(self):
        """
        List all instance groups.
        """
        logger.debug('Listing instances')
        instances_info = {}
        for node in self.driver.list_nodes():
            logger.debug("Node metadata: %s", node.extra["metadata"])
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
                instances_info[instance_group_name] = {}
                instances_info[instance_group_name]["Nodes"] = []
                instances_info[instance_group_name]["Network"] = network_names[0]
                instances_info[instance_group_name]["Id"] = subnetwork_names[0]
            instances_info[instance_group_name]["Nodes"].append(node)
        return [canonicalize_instances_info(group_info["Network"],
                                            group_info["Id"],
                                            group_info["Nodes"])
                for group_info in instances_info.values()]

    def _get_availability_zones(self):
        zones = self.driver.ex_list_zones()
        return [zone for zone in zones if zone.name.startswith(DEFAULT_REGION)]

    def node_types(self):
        """
        Get a list of node sizes to use for matching resource requirements to
        instance type.
        """
        # Need to do this because the "list_sizes" function doesn't seem to work
        # with region strings.
        zones = self.driver.ex_list_zones()
        for zone in zones:
            if zone.name.startswith(DEFAULT_REGION):
                node_sizes = self.driver.list_sizes(location=zone)
                return [canonicalize_node_size(node_size) for node_size in node_sizes]
        raise DisallowedOperationException("Could not find zone in region: %s" %
                                           DEFAULT_REGION)
