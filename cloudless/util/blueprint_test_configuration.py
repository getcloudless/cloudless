"""
Utilities to deal with blueprint test configuration files.
"""

import os
import yaml

from cloudless.util.log import logger

class BlueprintTestConfiguration:
    """
    Base blueprint test configuration object

    This is where to enforce things like types, required arguments, and just general configuration
    constraints.  This turns it into a kind of "schema" that someday we can probably auto generate
    using a YAML schema library.
    """

    def __init__(self, config):
        with open(config, 'r') as stream:
            try:
                self.config = yaml.load(stream)
            except yaml.YAMLError as exc:
                logger.error("Error parsing config: %s", exc)
                raise exc
        self.config_path = os.path.dirname(config)
        if not self.config_path:
            self.config_path = "./"
        self.config_filename = config

    def get_config_dir(self):
        """
        Get directory of the file behind this configuration.
        """
        return self.config_path

    def get_count(self):
        """
        Get number of instances needed to test.
        """
        return int(self.config.get("create", {}).get("count", 1))

    def get_blueprint_path(self):
        """
        Get path to the blueprint being tested.
        """
        relative_blueprint_path = self.config.get("create", {}).get("blueprint", "blueprint.yml")
        return os.path.join(self.config_path, relative_blueprint_path)

    def get_create_fixture_type(self):
        """
        Get the fixture type for the create step.
        """
        return self.config.get("create", {}).get("fixture_type", "python-blueprint-fixture")

    def get_create_fixture_options(self):
        """
        Get the fixture options for the create step.
        """
        return self.config.get("create", {}).get("fixture_options",
                                                 {"module_name": "blueprint_fixture"})

    def get_verify_fixture_type(self):
        """
        Get the fixture type for the verify step.
        """
        return self.config.get("verify", {}).get("fixture_type", "python-blueprint-fixture")

    def get_verify_fixture_options(self):
        """
        Get the fixture options for the verify step.
        """
        return self.config.get("verify", {}).get("fixture_options",
                                                 {"module_name": "blueprint_fixture"})
