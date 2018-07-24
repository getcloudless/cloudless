"""
Firewalls Impl

Helper utilities for dealing with google compute engine firewalls.
"""

import logging

logger = logging.getLogger(__name__)


class Firewalls(object):
    def __init__(self, driver):
        self.driver = driver

    def cleanup_orphaned_firewalls(self):
        firewalls = self.driver.ex_list_firewalls()
        nodes = self.driver.list_nodes()
        for firewall in firewalls:
            used = False
            for node in nodes:
                if not node.extra["tags"]:
                    pass
                for tag in node.extra["tags"]:
                    if not firewall.source_tags and not firewall.target_tags:
                        # XXX: This is here now so I don't delete the default
                        # firewall rules, but it shows an issue in how I'm
                        # interpreting these.
                        used = True
                        continue
                    if firewall.source_tags:
                        if tag in firewall.source_tags:
                            used = True
                    if firewall.target_tags:
                        if tag in firewall.target_tags:
                            used = True
            if not used:
                logger.info("Deleting unused firewall: %s", firewall)
                self.driver.ex_destroy_firewall(firewall)
