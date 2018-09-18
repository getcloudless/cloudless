"""
Cloudless service command line interface.
"""
from collections import OrderedDict
import yaml
import click
from cloudless.cli.utils import NaturalOrderAliasedGroup
from cloudless.cli.utils import handle_profile_for_cli, get_network_for_cli, get_service_for_cli

# pylint:disable=too-many-statements
def add_service_group(cldls):
    """
    Add commands for the service command group.
    """
    @cldls.group(name='service', cls=NaturalOrderAliasedGroup)
    @click.pass_context
    def service_group(ctx):
        """
        Create, list, get, destroy services.

        Commands to interact with services, which are groups of instances and the main unit of work
        in cloudless.
        """
        handle_profile_for_cli(ctx)
        click.echo('Service group with provider: %s' % ctx.obj['PROVIDER'])

    @service_group.command(name="create")
    @click.argument('network')
    @click.argument('name')
    @click.argument('blueprint')
    @click.argument('var_file', required=False)
    @click.pass_context
    # pylint:disable=unused-variable
    def service_create(ctx, network, name, blueprint, var_file=None):
        """
        Create a service in this profile.
        """
        if var_file:
            with open(var_file, 'r') as stream:
                var_file_contents = yaml.load(stream)
        else:
            var_file_contents = {}
        network_object = get_network_for_cli(ctx, network)
        service = ctx.obj['CLIENT'].service.create(network_object, name, blueprint,
                                                   var_file_contents)
        click.echo('Created service: %s in network: %s' % (name, network))

    @service_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def service_list(ctx):
        """
        List all services in this profile.
        """
        for service in ctx.obj['CLIENT'].service.list():
            click.echo("Network: %s, Service: %s" % (service.network.name, service.name))

    @service_group.command(name="get")
    @click.argument('network')
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_get(ctx, network, name):
        """
        Get details about a service in this profile.
        """

        # See
        # https://stackoverflow.com/questions/16782112/can-pyyaml-dump-dict-items-in-non-alphabetical-order
        def represent_ordereddict(dumper, data):
            value = []

            for item_key, item_value in data.items():
                node_key = dumper.represent_data(item_key)
                node_value = dumper.represent_data(item_value)

                value.append((node_key, node_value))

            return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)
        yaml.add_representer(OrderedDict, represent_ordereddict)

        def get_paths_info_for_service(service):
            paths = ctx.obj['CLIENT'].paths.list()
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

        service = get_service_for_cli(ctx, network, name)
        paths_info = get_paths_info_for_service(service)
        service_info = OrderedDict()
        service_info['name'] = service.name
        service_info['has_access_to'] = paths_info['has_access_to']
        service_info['is_accessible_from'] = paths_info['is_accessible_from']
        network_info = OrderedDict()
        network_info['name'] = service.network.name
        network_info['id'] = service.network.network_id
        network_info['block'] = service.network.cidr_block
        network_info['region'] = service.network.region
        network_info['subnetworks'] = []
        service_info['network'] = network_info
        for subnetwork in service.subnetworks:
            subnetwork_info = OrderedDict()
            subnetwork_info['name'] = subnetwork.name
            subnetwork_info['id'] = subnetwork.subnetwork_id
            subnetwork_info['block'] = subnetwork.cidr_block
            subnetwork_info['region'] = subnetwork.region
            subnetwork_info['availability_zone'] = subnetwork.availability_zone
            subnetwork_info['instances'] = []
            for instance in subnetwork.instances:
                instance_info = OrderedDict()
                instance_info['id'] = instance.instance_id
                instance_info['public_ip'] = instance.public_ip
                instance_info['private_ip'] = instance.private_ip
                instance_info['state'] = instance.state
                instance_info['availability_zone'] = instance.availability_zone
                subnetwork_info["instances"].append(instance_info)
            service_info["network"]["subnetworks"].append(subnetwork_info)
        click.echo(yaml.dump(service_info, default_flow_style=False))

    @service_group.command(name="destroy")
    @click.argument('network')
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_destroy(ctx, network, name):
        """
        Destroy a service in this profile.
        """
        service = get_service_for_cli(ctx, network, name)
        ctx.obj['CLIENT'].service.destroy(service)
        click.echo('Destroyed service: %s in network: %s' % (name, network))
