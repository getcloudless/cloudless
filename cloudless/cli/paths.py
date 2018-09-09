"""
Cloudless paths command line interface.
"""
import click
from cloudless.cli.utils import AliasedGroup

def add_paths_group(cldls):
    """
    Add commands for the paths command group.
    """
    @cldls.group(name='paths', cls=AliasedGroup)
    @click.pass_context
    def paths_group(ctx):
        """
        Commands to manage paths.

        Commands to interact with paths, which are allowed connections between services.
        """
        click.echo('paths group with profile: %s' % ctx.obj['PROFILE'])

    @paths_group.command(name="allow_service")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_allow_service(ctx, network, destination, source):
        """
        Allow access from source to destination.  These must be names of services in the same
        network.
        """
        click.echo(('paths group allow_service with profile: %s, network: %s, destination: %s, '
                    'source: %s') % (ctx.obj['PROFILE'], network, destination, source))

    @paths_group.command(name="allow_external")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_allow_external(ctx, network, destination, source):
        """
        Revoke access from source to destination.  Destination must be a service and source must be
        a public network address block.

        For example, pass 0,0.0.0/0 to allow all addresses on the internet.
        """
        click.echo(('paths group allow_external with profile: %s, network: %s, destination: %s, '
                    'source: %s') % (ctx.obj['PROFILE'], network, destination, source))

    @paths_group.command(name="revoke_service")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_revoke_service(ctx, network, destination, source):
        """
        Revoke access from source to destination.  These must be names of services in the same
        network.
        """
        click.echo(('paths group revoke_service with profile: %s, network: %s, destination: %s, '
                    'source: %s') % (ctx.obj['PROFILE'], network, destination, source))

    @paths_group.command(name="revoke_external")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_revoke_external(ctx, network, destination, source):
        """
        Revoke access from source to destination.  Destination must be a service and source must be
        a public network address block.

        For example, pass 0,0.0.0/0 to revoke all addresses on the internet.  Does not revoke access
        for internal services.  Use the "revoke_service" command for that.
        """
        click.echo(('paths group revoke_external with profile: %s, network: %s, destination: %s, '
                    'source: %s') % (ctx.obj['PROFILE'], network, destination, source))

    @paths_group.command(name="service_has_access")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_service_has_access(ctx, network, destination, source):
        """
        Returns true if access is allowed from source to destination.
        """
        click.echo(('paths group service_has_access with profile: %s, network: %s, '
                    'destination: %s, source: %s') % (ctx.obj['PROFILE'], network, destination,
                                                      source))

    @paths_group.command(name="external_has_access")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_external_has_access(ctx, network, destination, source):
        """
        Returns true if access is allowed from source to destination.
        """
        click.echo(('paths group external_has_access with profile: %s, network: %s, '
                    'destination: %s, source: %s') % (ctx.obj['PROFILE'], network, destination,
                                                      source))

    @paths_group.command(name="is_internet_accessible")
    @click.argument('network')
    @click.argument('destination')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_is_internet_accessible(ctx, network, destination):
        """
        Returns true if access is allowed from source to destination.
        """
        click.echo(('paths group is_internet_accessible with profile: %s, network: %s, '
                    'destination: %s') % (ctx.obj['PROFILE'], network, destination))

    @paths_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_list(ctx):
        """
        List all pathss in this profile.
        """
        click.echo('paths group list with profile: %s' % ctx.obj['PROFILE'])
