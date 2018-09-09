"""
Cloudless network command line interface.
"""
import click

def add_network_group(cldls):
    """
    Add commands for the network command group.
    """
    @cldls.group(name='network')
    @click.pass_context
    def network_group(ctx):
        """
        Commands to manage networks.

        Commands to interact with networks, which are isolated private networks that cloudless can
        deploy services into.
        """
        click.echo('Network group with profile: %s' % ctx.obj['PROFILE'])

    @network_group.command(name="create")
    @click.argument('name')
    @click.argument('blueprint')
    @click.pass_context
    # pylint:disable=unused-variable
    def network_create(ctx, name, blueprint):
        """
        Create a network in this profile.
        """
        click.echo('Network group create with profile: %s, name: %s, blueprint: %s' % (
            ctx.obj['PROFILE'],
            name,
            blueprint))

    @network_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def network_list(ctx):
        """
        List all networks in this profile.
        """
        click.echo('Network group list with profile: %s' % ctx.obj['PROFILE'])

    @network_group.command(name="get")
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def network_get(ctx, name):
        """
        Get details about a network in this profile.
        """
        click.echo('Network group get with profile: %s, name: %s' % (ctx.obj['PROFILE'], name))

    @network_group.command(name="destroy")
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def network_destroy(ctx, name):
        """
        Destroy a network in this profile.
        """
        click.echo('Network group destroy with profile: %s, name: %s' % (ctx.obj['PROFILE'], name))
