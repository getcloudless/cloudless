"""
Cloudless paths command line interface.
"""
import click
import cloudless
from cloudless.cli.utils import NaturalOrderAliasedGroup
from cloudless.cli.utils import handle_profile_for_cli, get_service_for_cli

# pylint:disable=too-many-statements
def add_paths_group(cldls):
    """
    Add commands for the paths command group.
    """
    @cldls.group(name='paths', cls=NaturalOrderAliasedGroup)
    @click.pass_context
    def paths_group(ctx):
        """
        Control access to and from services.

        Commands to interact with paths, which are allowed connections between services.
        """
        handle_profile_for_cli(ctx)
        click.echo('Paths group with provider: %s' % ctx.obj['PROVIDER'])

    @paths_group.command(name="allow_service")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_allow_service(ctx, network, destination, source, port):
        """
        Allow access from service to service.  These must be names of services in the same network.
        """
        source_service = get_service_for_cli(ctx, network, source)
        destination_service = get_service_for_cli(ctx, network, destination)
        ctx.obj['CLIENT'].paths.add(source_service, destination_service, port)
        click.echo('Added path from %s to %s in network %s for port %s' % (source, destination,
                                                                           network, port))

    @paths_group.command(name="allow_network_block")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_allow_network_block(ctx, network, destination, source, port):
        """
        Allow access from network block to service.  Destination must be a service and source must
        be a public network address block.

        For example, pass 0,0.0.0/0 to allow all addresses on the internet.
        """
        source_block = cloudless.paths.CidrBlock(source)
        destination_service = get_service_for_cli(ctx, network, destination)
        ctx.obj['CLIENT'].paths.add(source_block, destination_service, port)
        click.echo('Added path from %s to %s in network %s for port %s' % (source, destination,
                                                                           network, port))

    @paths_group.command(name="revoke_service")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_revoke_service(ctx, network, destination, source, port):
        """
        Revoke access from service to service.  These must be names of services in the same network.
        """
        source_service = get_service_for_cli(ctx, network, source)
        destination_service = get_service_for_cli(ctx, network, destination)
        ctx.obj['CLIENT'].paths.remove(source_service, destination_service, port)
        click.echo('Removed path from %s to %s in network %s for port %s' % (source, destination,
                                                                             network, port))

    @paths_group.command(name="revoke_network_block")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_revoke_network_block(ctx, network, destination, source, port):
        """
        Revoke access from network block to service.  Destination must be a service and source must
        be a public network address block.

        For example, pass 0,0.0.0/0 to revoke all addresses on the internet.  Does not revoke access
        for internal services.  Use the "revoke_service" command for that.
        """
        source_block = cloudless.paths.CidrBlock(source)
        destination_service = get_service_for_cli(ctx, network, destination)
        ctx.obj['CLIENT'].paths.remove(source_block, destination_service, port)
        click.echo('Removed path from %s to %s in network %s for port %s' % (source, destination,
                                                                             network, port))

    @paths_group.command(name="service_has_access")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_service_has_access(ctx, network, destination, source, port):
        """
        Can this service access this service?
        """
        source_service = get_service_for_cli(ctx, network, source)
        destination_service = get_service_for_cli(ctx, network, destination)
        if ctx.obj['CLIENT'].paths.has_access(source_service, destination_service, port):
            click.echo('Service %s has access to %s in network %s on port %s' % (
                source, destination, network, port))
        else:
            click.echo('Service %s does not have access to %s in network %s on port %s' % (
                source, destination, network, port))

    @paths_group.command(name="network_block_has_access")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('source')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_network_block_has_access(ctx, network, destination, source, port):
        """
        Can this network block access this service?
        """
        source_block = cloudless.paths.CidrBlock(source)
        destination_service = get_service_for_cli(ctx, network, destination)
        if ctx.obj['CLIENT'].paths.has_access(source_block, destination_service, port):
            click.echo('Network %s has access to %s in network %s on port %s' % (
                source, destination, network, port))
        else:
            click.echo('Network %s does not have access to %s in network %s on port %s' % (
                source, destination, network, port))

    @paths_group.command(name="is_internet_accessible")
    @click.argument('network')
    @click.argument('destination')
    @click.argument('port')
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_is_internet_accessible(ctx, network, destination, port):
        """
        Is this service reachable from the internet?
        """
        destination_service = get_service_for_cli(ctx, network, destination)
        if ctx.obj['CLIENT'].paths.internet_accessible(destination_service, port):
            click.echo('Service %s in network %s is internet accessible on port %s' % (
                destination, network, port))
        else:
            click.echo('Service %s in network %s is not internet accessible on port %s' % (
                destination, network, port))

    @paths_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def paths_list(ctx):
        """
        List all pathss in this profile.
        """
        for path in ctx.obj['CLIENT'].paths.list():
            if not path.source.name:
                cidr_blocks = [subnetwork.cidr_block for subnetwork in path.source.subnetworks]
                source_name = ",".join(cidr_blocks)
                network_name = "external"
            else:
                source_name = path.source.name
                network_name = path.source.network.name
            click.echo("%s:%s -(%s)-> %s:%s" % (network_name, source_name, path.port,
                                                path.network.name, path.destination.name))
