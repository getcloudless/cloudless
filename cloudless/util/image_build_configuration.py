"""
Utilities to deal with image build configuration files.
"""

import os
import yaml

from cloudless.util.log import logger
from cloudless.util.exceptions import BadConfigurationException

class ImageBuildConfiguration:
    """
    Image build configuration object.

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
        image_name = self.config.get("save", {}).get("name")
        if not image_name:
            raise BadConfigurationException(
                "Missing required configuration option \"save.name\" in config file: %s" % (
                    self.config_filename))

    def get_config_dir(self):
        """
        Get directory of the file behind this configuration.
        """
        return self.config_path

    def get_blueprint_path(self):
        """
        Get path to the blueprint being tested.
        """
        relative_blueprint_path = self.config.get("deploy", {}).get("blueprint", "blueprint.yml")
        return os.path.join(self.config_path, relative_blueprint_path)

    def get_configure_script_path(self):
        """
        Get the path for the configure script.
        """
        return os.path.join(self.config_path, self.config.get("configure", {}).get("path",
                                                                                   "configure"))

    def get_check_script_path(self):
        """
        Get the path for the check script.
        """
        return os.path.join(self.config_path, self.config.get("check", {}).get("path", "check"))

    def get_image_name(self):
        """
        Get the image name to save as.
        """
        return self.config.get("save", {}).get("name")
