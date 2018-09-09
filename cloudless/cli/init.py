"""
Cloudless init command line interface.
"""
import click
import cloudless.profile

def add_init_group(cldls):
    """
    Add commands for the init command group.
    """
    @cldls.command()
    @click.option('--provider', type=str, required=True, help="Development mode.")
    @click.pass_context
    # pylint:disable=unused-variable
    def init(ctx, provider):
        """
        Initialize credentials for the command line.

        Creates a configuration in "$HOME/.cloudless".  You can use this command to create separate
        "profiles" that you can pass on the command line or set via environment variables.
        """
        click.echo('Setting provider for profile "%s" to "%s"' % (ctx.obj['PROFILE'], provider))
        cloudless.profile.save_profile(ctx.obj['PROFILE'], {"provider": provider})
