"""
Cloudless Model

This class represents the state of the project in an abstracted, cloud agnostic way.
"""
from collections import OrderedDict
import difflib
import yaml
from cloudless.types.common import Path, Service, Network
from cloudless.util.exceptions import DisallowedOperationException
from cloudless.util.yaml_representer import represent_ordereddict

class ProjectModel:
    """
    The abstract state of a Project.  This is actually just a set of graphs with services as nodes
    and paths as edges.  Each network is a single graph.

    This will not have a commit method.  That must be implemented by the provider.
    """

    def __init__(self, networks, services, paths):
        self.networks = networks
        self.services = services
        self.paths = paths
        self.new_networks = []
        self.new_services = []
        self.new_paths = []

    def to_yaml(self, include_new=False):
        """
        Dump this network as YAML.
        """
        yaml.add_representer(OrderedDict, represent_ordereddict)

        def get_paths_info_for_service(service):
            paths = list(self.paths)
            if include_new:
                paths.extend(self.new_paths)
            paths = [path for path in paths if path.network.name == service.network.name]
            has_access_to = ["default-all-outgoing-allowed"]
            is_accessible_from = []
            for path in paths:
                if path.destination.name == service.name:
                    if path.source.name:
                        is_accessible_from.append("%s:%s:%s" % (path.network.name, path.source.name,
                                                                path.port))
                    else:
                        cidr_blocks = [subnetwork.cidr_block for subnetwork
                                       in path.source.subnetworks]
                        cidr_blocks_string = ",".join(cidr_blocks)
                        is_accessible_from.append("external:%s:%s" % (cidr_blocks_string,
                                                                      path.port))
                elif path.source.name == service.name:
                    has_access_to.append("%s:%s:%s" % (path.network.name, path.destination.name,
                                                       path.port))
            return {"has_access_to": has_access_to, "is_accessible_from": is_accessible_from}

        def instance_info(instance):
            return OrderedDict([
                ('id', instance.instance_id),
                ('public_ip', instance.public_ip),
                ('private_ip', instance.private_ip),
                ('state', instance.state),
                ('availability_zone', instance.availability_zone)])

        def subnetwork_info(subnetwork):
            return OrderedDict([
                ('name', subnetwork.name),
                ('id', subnetwork.subnetwork_id),
                ('block', subnetwork.cidr_block),
                ('region', subnetwork.region),
                ('availability_zone', subnetwork.availability_zone),
                ('instances', [instance_info(instance) for instance in subnetwork.instances])])

        def service_info(service):
            paths_info = get_paths_info_for_service(service)
            service_info = OrderedDict([
                ('name', service.name),
                ('has_access_to', paths_info['has_access_to']),
                ('is_accessible_from', paths_info['is_accessible_from']),
                ('subnetworks', [subnetwork_info(subnetwork)
                                 for subnetwork in service.subnetworks])])
            return service_info

        def network_info(network):
            services = list(self.services)
            if include_new:
                services.extend(self.new_services)
            services = [service for service in services if service.network.name == network.name]
            return OrderedDict([
                ('name', network.name),
                ('id', network.network_id),
                ('block', network.cidr_block),
                ('region', network.region),
                ('services', [service_info(service) for service in services])])

        networks = list(self.networks)
        if include_new:
            networks.extend(self.new_networks)

        return yaml.dump([network_info(network) for network in networks], default_flow_style=False)

    def add_network(self, network):
        """
        Add a network to this model.  This will show up in various output commands, but is not yet
        committed.
        """
        if not isinstance(network, Network):
            raise DisallowedOperationException(
                "Argument to add_network must be of type cloudless.types.common.Network")
        if self.new_services or self.new_paths or self.new_networks:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_networks.append(network)

    def add_service(self, service):
        """
        Add a service to this model.  This will show up in various output commands, but is not yet
        committed.
        """
        if not isinstance(service, Service):
            raise DisallowedOperationException(
                "Argument to add_service must be of type cloudless.types.common.Service")
        if self.new_services or self.new_paths or self.new_networks:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_services.append(service)

    def add_path(self, path):
        """
        Add a path to this model.  This will show up in various output commands, but is not yet
        committed.
        """
        if not isinstance(path, Path):
            raise DisallowedOperationException(
                "Argument to add_path must be of type cloudless.types.common.Path")
        if self.new_services or self.new_paths or self.new_networks:
            raise DisallowedOperationException(
                "This model already has pending operations.  Commit this using a backend provider.")
        self.new_paths.append(path)

    def to_yaml_diff(self):
        """
        Print a diff between old and new to show what changed.
        """
        old_yaml = self.to_yaml().split("\n")
        new_yaml = self.to_yaml(include_new=True).split("\n")
        return "\n".join(difflib.ndiff(old_yaml, new_yaml))
