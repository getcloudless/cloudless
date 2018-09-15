"""
Utilities needed for command line interface.
"""
import sys
from collections import OrderedDict
import click
import cloudless

class NaturalOrderGroup(click.Group):
    """Command group trying to list subcommands in the order they were added.
    Example use::

        @click.group(cls=NaturalOrderGroup)

    If passing dict of commands from other sources, ensure they are of type
    OrderedDict and properly ordered, otherwise order of them will be random
    and newly added will come to the end.

    See: https://github.com/pallets/click/issues/513
    """
    def __init__(self, name=None, commands=None, **attrs):
        if commands is None:
            commands = OrderedDict()
        elif not isinstance(commands, OrderedDict):
            commands = OrderedDict(commands)
        click.Group.__init__(self, name=name, commands=commands, **attrs)

    def list_commands(self, ctx):
        """List command names as they are in commands dict.

        If the dict is OrderedDict, it will preserve the order commands
        were added.
        """
        return self.commands.keys()


class NaturalOrderAliasedGroup(NaturalOrderGroup):
    """
    Handles command aliases.  See: http://click.pocoo.org/5/advanced/#command-aliases
    """
    def get_command(self, ctx, cmd_name):
        """
        Get the command, currently only aliases "ls" to "list".
        """
        if cmd_name == "ls":
            cmd_name = "list"
        return click.Group.get_command(self, ctx, cmd_name)


def handle_profile_for_cli(ctx):
    """
    Loads the profile and sets the proper fields on the context object for the command line.
    """
    profile = cloudless.profile.load_profile(ctx.obj['PROFILE'])
    if not profile:
        click.echo("Profile: \"%s\" not found." % ctx.obj['PROFILE'])
        click.echo("Try running \"cldls --profile %s init\"." % ctx.obj['PROFILE'])
        sys.exit(1)
    ctx.obj['PROVIDER'] = profile["provider"]
    ctx.obj['CREDENTIALS'] = profile["credentials"]
    ctx.obj['CLIENT'] = cloudless.Client(provider=ctx.obj['PROVIDER'],
                                         credentials=ctx.obj['CREDENTIALS'])

def get_network_for_cli(ctx, network_name):
    """
    Get network for cli commands with proper handling.
    """
    network = ctx.obj['CLIENT'].network.get(network_name)
    if not network:
        click.echo("Could not find network: %s" % network_name)
        sys.exit(1)
    return network

def get_service_for_cli(ctx, network_name, service_name):
    """
    Get service for cli commands with proper handling.
    """
    network = get_network_for_cli(ctx, network_name)
    service = ctx.obj['CLIENT'].service.get(network, service_name)
    if not service:
        click.echo("Could not find service: %s in network %s" % (service_name, network.name))
        sys.exit(1)
    return service
