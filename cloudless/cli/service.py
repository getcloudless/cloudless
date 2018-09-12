"""
Cloudless service command line interface.
"""
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
        network_object = ctx.obj['CLIENT'].network.get(network)
        service = ctx.obj['CLIENT'].service.get(network_object, name)
        click.echo('Name: %s' % service.name)
        click.echo('Network Name: %s' % service.network.name)
        click.echo('Network Id: %s' % service.network.network_id)
        click.echo('Network Block: %s' % service.network.cidr_block)
        click.echo('Network Region: %s' % service.network.region)
        for subnetwork in service.subnetworks:
            click.echo('    Subnetwork Name: %s' % subnetwork.name)
            click.echo('    Subnetwork Id: %s' % subnetwork.subnetwork_id)
            click.echo('    Subnetwork Block: %s' % subnetwork.cidr_block)
            click.echo('    Subnetwork Region: %s' % subnetwork.region)
            click.echo('    Subnetwork Availability_zone: %s' % subnetwork.availability_zone)
            for instance in subnetwork.instances:
                click.echo('        Instance Id: %s' % instance.instance_id)
                click.echo('        Instance Public IP: %s' % instance.public_ip)
                click.echo('        Instance Private IP: %s' % instance.private_ip)
                click.echo('        Instance State: %s' % instance.state)

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
