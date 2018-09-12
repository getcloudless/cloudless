"""
Cloudless service command line interface.
"""
from collections import OrderedDict
import yaml
import click
from cloudless.cli.utils import AliasedGroup
import cloudless

def add_service_group(cldls):
    """
    Add commands for the service command group.
    """
    @cldls.group(name='service', cls=AliasedGroup)
    @click.pass_context
    def service_group(ctx):
        """
        Commands to manage services.

        Commands to interact with services, which are groups of instances and the main unit of work
        in cloudless.
        """
        profile = cloudless.profile.load_profile(ctx.obj['PROFILE'])
        ctx.obj['PROVIDER'] = profile["provider"]
        click.echo('Service group with provider: %s' % ctx.obj['PROVIDER'])
        ctx.obj['CLIENT'] = cloudless.Client(provider=ctx.obj['PROVIDER'], credentials={})

    @service_group.command(name="create")
    @click.argument('network')
    @click.argument('name')
    @click.argument('blueprint')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_create(ctx, network, name, blueprint):
        """
        Create a service in this profile.
        """
        network_object = ctx.obj['CLIENT'].network.get(network)
        service = ctx.obj['CLIENT'].service.create(network_object, name, blueprint)
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

        def represent_ordereddict(dumper, data):
            value = []

            for item_key, item_value in data.items():
                node_key = dumper.represent_data(item_key)
                node_value = dumper.represent_data(item_value)

                value.append((node_key, node_value))

            return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

        class LastUpdatedOrderedDict(OrderedDict):
            'Store items in the order the keys were last added'
            def __setitem__(self, key, value):
                if key in self:
                    del self[key]
                OrderedDict.__setitem__(self, key, value)

        yaml.add_representer(OrderedDict, represent_ordereddict)

        network_object = ctx.obj['CLIENT'].network.get(network)
        service = ctx.obj['CLIENT'].service.get(network_object, name)
        service_info = OrderedDict()
        service_info['name'] = service.name
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
        network_object = ctx.obj['CLIENT'].network.get(network)
        service_object = ctx.obj['CLIENT'].service.get(network_object, name)
        ctx.obj['CLIENT'].service.destroy(service_object)
        click.echo('Destroyed service: %s in network: %s' % (name, network))
