"""
Helper to return a fitting instance given the provided resource requirements.
"""
import re
from butter.util.blueprint import InstancesBlueprint

# pylint: disable=unused-argument
def get_fitting_instance(provider, blueprint):
    """
    Finds the cheapest instance that satisfies the requirements specified in
    the given blueprint.
    """
    instances_blueprint = InstancesBlueprint(blueprint)

    units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
    def parse_size(size):
        match = re.match(r"(\d+(?:\.\d+)?)(B|KB|MB|GB|TB)", size)
        number = match.group(1)
        unit = match.group(2)
        return int(float(number)*units[unit])
    memory_bytes = parse_size(instances_blueprint.memory())

    # Currently, this doesn't support anything besides the smallest instance types.
    if memory_bytes > parse_size("0.5GB"):
        raise NotImplementedError
    if instances_blueprint.cpus() > 0.2:
        raise NotImplementedError
    if instances_blueprint.gpus():
        raise NotImplementedError
    if len(instances_blueprint.disks()) > 1:
        raise NotImplementedError
    for disk in instances_blueprint.disks():
        if parse_size(disk["size"]) > parse_size("8GB"):
            raise NotImplementedError
        if disk["type"] != "standard":
            raise NotImplementedError
        if disk["device_name"] != "/dev/sda1":
            raise NotImplementedError
    if provider == "aws":
        return "t2.nano"
    if provider == "gce":
        return "f1-micro"
    raise NotImplementedError
