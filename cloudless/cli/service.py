"""
Cloudless service command line interface.
"""
import click
from cloudless.cli.utils import AliasedGroup

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
        click.echo('service group with profile: %s' % ctx.obj['PROFILE'])

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
        click.echo('service group create with profile: %s, network: %s, name: %s, blueprint: %s' % (
            ctx.obj['PROFILE'],
            network,
            name,
            blueprint))

    @service_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def service_list(ctx):
        """
        List all services in this profile.
        """
        click.echo('service group list with profile: %s' % ctx.obj['PROFILE'])

    @service_group.command(name="get")
    @click.argument('network')
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_get(ctx, network, name):
        """
        Get details about a service in this profile.
        """
        click.echo('service group get with profile: %s, network: %s, name: %s' % (
            ctx.obj['PROFILE'], network, name))

    @service_group.command(name="destroy")
    @click.argument('network')
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_destroy(ctx, network, name):
        """
        Destroy a service in this profile.
        """
        click.echo('service group destroy with profile: %s, network: %s, name: %s' % (
            ctx.obj['PROFILE'], network, name))
