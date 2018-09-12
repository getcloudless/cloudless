"""
Cloudless network command line interface.
"""
import click
from cloudless.cli.utils import AliasedGroup
import cloudless

def add_network_group(cldls):
    """
    Add commands for the network command group.
    """
    @cldls.group(name='network', cls=AliasedGroup)
    @click.pass_context
    def network_group(ctx):
        """
        Commands to manage networks.

        Commands to interact with networks, which are isolated private networks that cloudless can
        deploy services into.
        """
        profile = cloudless.profile.load_profile(ctx.obj['PROFILE'])
        ctx.obj['PROVIDER'] = profile["provider"]
        click.echo('Network group with provider: %s' % ctx.obj['PROVIDER'])
        ctx.obj['CLIENT'] = cloudless.Client(provider=ctx.obj['PROVIDER'], credentials={})

    @network_group.command(name="create")
    @click.argument('name')
    @click.argument('blueprint')
    @click.pass_context
    # pylint:disable=unused-variable
    def network_create(ctx, name, blueprint):
        """
        Create a network in this profile.
        """
        network = ctx.obj['CLIENT'].network.create(name, blueprint)
        click.echo('Created network: %s' % network.name)

    @network_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def network_list(ctx):
        """
        List all networks in this profile.
        """
        networks = ctx.obj['CLIENT'].network.list()
        click.echo('Networks: %s' % [network.name for network in networks])

    @network_group.command(name="get")
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def network_get(ctx, name):
        """
        Get details about a network in this profile.
        """
        network = ctx.obj['CLIENT'].network.get(name)
        click.echo('Name: %s' % network.name)
        click.echo('Id: %s' % network.network_id)
        click.echo('Network: %s' % network.cidr_block)
        click.echo('Region: %s' % network.region)

    @network_group.command(name="destroy")
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def network_destroy(ctx, name):
        """
        Destroy a network in this profile.
        """
        ctx.obj['CLIENT'].network.destroy(ctx.obj['CLIENT'].network.get(name))
        click.echo('Destroyed network: %s' % name)
