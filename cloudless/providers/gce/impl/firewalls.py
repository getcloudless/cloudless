"""
Firewalls Impl

Helper utilities for dealing with google compute engine firewalls.
"""
from cloudless.providers.gce.log import logger


# pylint: disable=too-few-public-methods
class Firewalls:
    """
    Class to manage GCE firewalls.
    """

    def __init__(self, driver):
        self.driver = driver

    def delete_firewall(self, network_name, subnetwork_name):
        """
        Delete the firewall corresponding to the service described by "network_name" and
        "subnetwork_name".
        """
        firewalls = self.driver.ex_list_firewalls()
        tag = "%s-%s" % (network_name, subnetwork_name)
        for firewall in firewalls:
            if not firewall.source_tags and not firewall.target_tags:
                continue
            if firewall.source_tags:
                if tag in firewall.source_tags:
                    logger.info("Deleting firewall %s because of source tag: %s", firewall, tag)
                    self.driver.ex_destroy_firewall(firewall)
            if firewall.target_tags:
                if tag in firewall.target_tags:
                    logger.info("Deleting firewall %s because of target tag: %s", firewall, tag)
                    self.driver.ex_destroy_firewall(firewall)
