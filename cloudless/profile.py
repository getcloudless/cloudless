"""
Cloudless Profile

These are helper functions to manage cloudless profiles.
"""
import configparser
import os

class FileConfigSource:
    """
    Loads and saves configuration data to an INI file.
    """

    def __init__(self):
        self.config_dir = os.path.expanduser("~/.cloudless/")
        self.config_path = os.path.join(self.config_dir, "config.ini")

    def load(self):
        """
        Load configuration.
        """
        if not os.path.exists(self.config_path):
            return None
        config_parser = configparser.ConfigParser()
        config_parser.read(self.config_path)
        return {section:config_parser[section] for section in config_parser.sections()}

    def save(self, config):
        """
        Save configuration.
        """
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        config_parser = configparser.ConfigParser()
        for section, options in config.items():
            config_parser.add_section(section)
            for option, value in options.items():
                config_parser.set(section, option, value)
        with open(self.config_path, 'w') as configfile:
            config_parser.write(configfile)

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
