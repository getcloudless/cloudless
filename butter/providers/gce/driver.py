"""
Google Compute Engine Driver Setup

GCE uses an oauth process to authenticate, so getting the driver uses the provided credentials to do
that.
"""
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


def get_gce_driver(credentials):
    """
    Uses the given credentials to get a GCE driver object from libcloud.
    """
    compute_engine_driver = get_driver(Provider.GCE)
    driver = compute_engine_driver(user_id=credentials["user_id"],
                                   key=credentials["key"],
                                   project=credentials["project"])
    return driver
