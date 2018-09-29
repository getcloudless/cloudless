"""
YAML Representer

Helper to preserve ordering when dumping an ordereddict with yaml.

See
https://stackoverflow.com/questions/16782112/can-pyyaml-dump-dict-items-in-non-alphabetical-order
"""
import yaml

def represent_ordereddict(dumper, data):
    """
    Use this to tell yaml how to properly represent OrderedDict objects.

    Usage:

        yaml.add_representer(OrderedDict, represent_ordereddict)

    """
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)
