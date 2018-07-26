#!/usr/bin/env python
"""
Utilities to deal with blueprint files.  All here so that I can keep them as a
standard format.
"""

import os
import yaml

from butter.util.logging import logger


# pylint: disable=too-few-public-methods
class Blueprint:
    """
    Base blueprint object
    """

    def __init__(self, blueprint_file):
        with open(blueprint_file, 'r') as stream:
            try:
                self.blueprint = yaml.load(stream)
            except yaml.YAMLError as exc:
                logger.error("Error parsing blueprint: %s", exc)
                raise exc
        self.blueprint_path = os.path.dirname(blueprint_file)
        self.blueprint_filename = blueprint_file


class NetworkBlueprint(Blueprint):
    """
    Blueprint for top level network.
    """
    def get_prefix(self):
        """
        Get the number of bits of prefix for the CIDR block.  A network of size 0 would give a
        prefix of 32 meaning the network has 1 address in it (so effectively nothing since that's
        usually disallowed or filled by internal services.
        """
        return 32 - self.blueprint["size"]


class InstancesBlueprint(Blueprint):
    """
    Blueprint for instances/subnetworks.
    """
    def max_count(self):
        """
        Returns the maximum number of instances expected.  Used to compute subnet sizes.
        """
        return self.blueprint["resources"]["max_count"]

    def availability_zone_count(self):
        """
        Number of availability zones.  Used to determine how redundant the services should be.
        """
        return self.blueprint["resources"].get("availability_zones", 3)

    def image(self):
        """
        The human readable name of the image to use.  This will be used internally to look up the
        image ID to deploy with.
        """
        return self.blueprint["image"]["name"]

    def runtime_scripts(self):
        """
        Returns the contents of the provided runtime scripts.  Currently only supports a list with
        one script.
        """
        if len(self.blueprint["initialization"]) > 1:
            raise NotImplementedError("Only one initialization script currently supported")
        relative_path = self.blueprint["initialization"][0]["path"]
        config_path = os.path.join(self.blueprint_path, relative_path)
        with open(config_path) as startup_script_file:
            return startup_script_file.read()

    def public_ip(self):
        """
        Returns whether a public IP should be added to the instances.
        """
        return self.blueprint["resources"].get("public_ip", False)

    def cpus(self):
        """
        Returns the cpus to allocate for the instance.  This is required.
        """
        return float(self.blueprint["resources"]["cpus"])

    def gpus(self):
        """
        Whether to allocate a GPU.
        """
        return self.blueprint["resources"].get("gpus", False)

    def memory(self):
        """
        Returns the memory to allocate for the instance.  This is required.
        """
        return self.blueprint["resources"]["memory"]

    def disks(self):
        """
        Returns the disks to allocate for the instance.  This is required.
        """
        return self.blueprint["resources"]["disks"]
