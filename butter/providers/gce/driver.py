from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver


def get_gce_driver(credentials):
    ComputeEngine = get_driver(Provider.GCE)
    driver = ComputeEngine(user_id=credentials["user_id"],
                           key=credentials["key"],
                           project=credentials["project"])
    return driver
