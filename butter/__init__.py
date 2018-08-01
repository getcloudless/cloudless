"""
Butter

This is a python library to provide a basic set of easy to use primitive
operations that can work with many different cloud providers.

These primitives are:

    - Create a "Network" (also known as VPC, Environment).  e.g. "dev".
    - Create a named group of instances within that network.  e.g. "dev.public".
    - Easily control network connections and firewalls.

The goal is to provide an intuitive abstraction that is powerful enough to build
on, so that building other layers on top is easy and anything built on it is
automatically cross cloud.
"""
from butter import network, subnetwork, instances, paths


# pylint: disable=too-few-public-methods
class Client:
    """
    Butter Client Object

    This is the object through which all calls are made.

    Usage:

        import butter
        client = butter.Client(provider, credentials)
        client.network.*
        client.subnetwork.*
        client.instances.*
        client.paths.*

    See the documentation on those sub-components for more details.
    """

    def __init__(self, provider, credentials):
        self.network = network.NetworkClient(provider, credentials)
        self.subnetwork = subnetwork.SubnetworkClient(provider, credentials)
        self.instances = instances.InstancesClient(provider, credentials)
        self.paths = paths.PathsClient(provider, credentials)

    # pylint: disable=too-many-locals
    def graph(self):
        """
        Return a human readable formatted string representation of the paths
        graph.

        Right now this is designed to print a dotfile that can be consumed by
        graphviz.  This should probably be cleaned up/replaced with a real
        visualization but for now it's good enough to show how this should work.
        """
        paths_info = self.paths.list()
        graph_string = "digraph services {\n\n"
        instances_info = self.instances.list()
        cluster_num = 0

        for network_info in self.network.list()["Named"]:
            path_info = paths_info.get(network_info["Name"], {})

            # We need this to get nodes with no rules set up
            connected_instances = set()

            network_empty = True
            graph_string += "subgraph cluster_%s {\n" % cluster_num
            cluster_num = cluster_num + 1
            graph_string += "    label = \"%s\";\n" % network_info["Name"]
            for from_node, to_info in path_info.items():
                connected_instances.add(from_node)
                for to_node, rule_info, in to_info.items():
                    connected_instances.add(to_node)
                    for path in rule_info:
                        network_empty = False
                        graph_string += ("    \"%s\" -> \"%s\" [ label=\"(%s:%s)\" ];\n" %
                                         (from_node, to_node, path["protocol"], path["port"]))

            for instance in instances_info:
                if instance["Network"] != network_info["Name"]:
                    continue
                if instance["Id"] not in connected_instances:
                    network_empty = False
                    graph_string += "    \"%s\";\n" % instance["Id"]

            if network_empty:
                # Need this becuse graphviz won't show an empty cluster
                graph_string += "    \"Empty Network %s\";\n" % cluster_num

            graph_string += "\n}\n"
        graph_string += "\n}\n"
        return graph_string
