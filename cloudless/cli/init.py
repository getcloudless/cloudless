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
        credentials = {}
        if provider == 'gce':
            click.echo('Google Compute Engine requires additional parameters.')
            click.echo('To retrieve these parameters, navigate to:')
            click.echo(('https://console.cloud.google.com/iam-admin/serviceaccounts?'
                        'project=<your_project_id>'))
            click.echo(('And create a service account.  "user_id" is the email, '
                        '"key" is the JSON key file you must create, '
                        'and "project" is the project id (not the project name).'))
            credentials["user_id"] = click.prompt('Please enter gce user id', type=str).strip()
            credentials["key"] = click.prompt('Please enter path to gce key file', type=str).strip()
            credentials["project"] = click.prompt('Please enter gce project name', type=str).strip()
        cloudless.profile.save_profile(ctx.obj['PROFILE'], {"provider": provider,
                                                            "credentials": credentials})
