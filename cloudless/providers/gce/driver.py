"""
Google Compute Engine Driver Setup

GCE uses an oauth process to authenticate, so getting the driver uses the provided credentials to do
that.
"""
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from cloudless.providers.gce.log import logger


DRIVER = None


def get_gce_driver(credentials):
    """
    Uses the given credentials to get a GCE driver object from libcloud.
    """
    # pylint:disable=global-statement
    global DRIVER
    if not DRIVER:
        logger.debug("GCE driver not initialized, creating.")
        compute_engine_driver = get_driver(Provider.GCE)
        DRIVER = compute_engine_driver(user_id=credentials["user_id"],
                                       key=credentials["key"],
                                       project=credentials["project"])
    return DRIVER
