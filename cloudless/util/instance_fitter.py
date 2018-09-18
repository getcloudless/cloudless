"""
Helper to return a fitting instance given the provided resource requirements.
"""
from cloudless.util.storage_size_parser import parse_storage_size
from cloudless.util.log import logger

# pylint: disable=unused-argument
def get_fitting_instance(instances_client, blueprint):
    """
    Finds the cheapest instance that satisfies the requirements specified in
    the given blueprint.
    """
    # Raise exceptions for anything not supported
    if len(blueprint.disks()) > 1:
        raise NotImplementedError
    for disk in blueprint.disks():
        if parse_storage_size(disk["size"]) > parse_storage_size("8GB"):
            raise NotImplementedError
        if disk["type"] != "standard":
            raise NotImplementedError
        if disk["device_name"] != "/dev/sda1":
            raise NotImplementedError

    # Get the smallest node type that satisfies our requirements
    node_types = instances_client.node_types()
    current_node = None
    for node_type in node_types:

        # First, check if the node even satisfies our requirements
        if (node_type["cpus"] >= blueprint.cpus() and
                node_type["memory"] >= blueprint.memory()):
            logger.debug("Need cpus: %s memory: %s", blueprint.cpus(),
                         blueprint.memory())
            logger.debug("Found satisfying node: %s", node_type)

            # Set our node to this one if it's the first we've found
            if not current_node:
                current_node = node_type

            # Otherwise, if this node is smaller than the one we found before,
            # reset (this is a heuristic for "cheapest").
            elif (node_type["cpus"] <= current_node["cpus"] and
                  node_type["memory"] <= current_node["memory"]):
                current_node = node_type
    return current_node["type"]
