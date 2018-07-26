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
