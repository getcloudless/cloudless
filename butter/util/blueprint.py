#!/usr/bin/env python
"""
Utilities to deal with blueprint files.  All here so that I can keep them as a
standard format.
"""

import os
import logging
import yaml

logger = logging.getLogger(__name__)


class Blueprint(object):
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
        return 32 - self.blueprint["size"]


class InstancesBlueprint(Blueprint):
    """
    Blueprint for instances/subnetworks.
    """

    def max_count(self):
        return self.blueprint["resources"]["max_count"]

    def availability_zone_count(self):
        return self.blueprint["resources"].get("availability_zones", 3)

    def image(self):
        return self.blueprint["image"]["name"]

    def runtime_scripts(self):
        relative_path = self.blueprint["initialization"][0]["path"]
        config_path = os.path.join(self.blueprint_path, relative_path)
        with open(config_path) as f:
            return f.read()

    def public_ip(self):
        return self.blueprint["resources"].get("public_ip", False)
