"""
Cloudless init command line interface.
"""
import click

def add_init_group(cldls):
    """
    Add commands for the init command group.
    """
    @cldls.command()
    @click.pass_context
    # pylint:disable=unused-variable
    def init(ctx):
        """
        Initialize credentials for the command line.

        Creates a configuration in "$HOME/.cloudless".  You can use this command to create separate
        "profiles" that you can pass on the command line or set via environment variables.
        """
        click.echo('TODO: Initialize profile: %s' % ctx.obj['PROFILE'])
