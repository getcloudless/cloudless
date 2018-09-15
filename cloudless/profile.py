"""
Cloudless Profile

These are helper functions to manage cloudless profiles.
"""
import os
import yaml

class FileConfigSource:
    """
    Loads and saves configuration data to a YAML file.
    """

    def __init__(self):
        self.config_dir = os.path.expanduser("~/.cloudless/")
        self.config_path = os.path.join(self.config_dir, "config.yml")

    def load(self):
        """
        Load configuration.
        """
        if not os.path.exists(self.config_path):
            return None
        with open(self.config_path, 'r') as config_file:
            return yaml.load(config_file)

    def save(self, config):
        """
        Save configuration.
        """
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        with open(self.config_path, 'w') as config_file:
            config_file.write(yaml.dump(config))

def save_profile(profile, options):
    """
    Saves the profile to the correct path.  Currently only accepts a profile name and a provider.
    """
    file_config_source = FileConfigSource()
    config = file_config_source.load()
    if not config:
        config = {}
    config[profile] = options
    file_config_source.save(config)

def load_profile(profile):
    """
    Loads the profile into a dictionary.
    """
    file_config_source = FileConfigSource()
    config = file_config_source.load()
    return config.get(profile, None)
