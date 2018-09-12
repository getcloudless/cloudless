"""
Cloudless command line interface definitions.
"""
import os
import logging
import click
from click_repl import register_repl
from cloudless.cli.init import add_init_group
from cloudless.cli.network import add_network_group
from cloudless.cli.service import add_service_group
from cloudless.cli.paths import add_paths_group
from cloudless.cli.image import add_image_group
from cloudless.cli.blueprint import add_blueprint_group
from cloudless.cli.utils import NaturalOrderGroup
import cloudless

cloudless.set_level(logging.WARN)

def get_cldls():
    """
    Does all the work to initialize the cldls command line and subcommands.
    """
    @click.group(name='cldls', cls=NaturalOrderGroup)
    @click.option('--debug/--no-debug', default=False)
    @click.option('--profile', help="The profile to use.")
    @click.pass_context
    def cldls(ctx, debug, profile):
        """
        The cloudless command line.  Use this to interact with networks and services deployed with
        cloudless, and to run the testing framework.

        If the "profile" option is not set, the value of "CLOUDLESS_PROFILE" will be used.  If
        neither option is set, the default profile is "default".
        """
        if not ctx.obj:
            ctx.obj = {}
        if debug:
            click.echo('Debug mode is currently not implemented, ignoring.')
        if profile:
            ctx.obj['PROFILE'] = profile
        elif "CLOUDLESS_PROFILE" in os.environ:
            ctx.obj['PROFILE'] = os.environ["CLOUDLESS_PROFILE"]
        else:
            ctx.obj['PROFILE'] = "default"

    add_init_group(cldls)
    add_network_group(cldls)
    add_service_group(cldls)
    add_paths_group(cldls)
    add_image_group(cldls)
    add_blueprint_group(cldls)
    register_repl(cldls)
    return cldls
