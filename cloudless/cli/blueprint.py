"""
Cloudless blueprint command line interface.
"""
import click
from cloudless.cli.utils import NaturalOrderAliasedGroup
import cloudless
from cloudless.testutils.blueprint_tester import setup as do_setup
from cloudless.testutils.blueprint_tester import verify as do_verify
from cloudless.testutils.blueprint_tester import teardown as do_teardown
from cloudless.testutils.blueprint_tester import run_all

def add_blueprint_group(cldls):
    """
    Add commands for the blueprint command group.
    """
    @cldls.group(name='blueprint', cls=NaturalOrderAliasedGroup)
    @click.option('--dev/--no-dev', default=False, help="Development mode.")
    @click.pass_context
    def blueprint_group(ctx, dev):
        """
        Blueprint testing framework.

        Helper to test blueprints, run create, verify, and cleanup.  Saves deployment state into
        <blueprint_directory>/blueprint-test-state.json.
        """
        ctx.obj['DEV'] = dev
        profile = cloudless.profile.load_profile(ctx.obj['PROFILE'])
        ctx.obj['PROVIDER'] = profile["provider"]
        ctx.obj['CREDENTIALS'] = profile["credentials"]
        click.echo('Service group with provider: %s' % ctx.obj['PROVIDER'])
        ctx.obj['CLIENT'] = cloudless.Client(provider=ctx.obj['PROVIDER'],
                                             credentials=ctx.obj['CREDENTIALS'])

    @blueprint_group.command(name="test")
    @click.argument('blueprint-directory')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_build(ctx, blueprint_directory):
        """
        Test an blueprint given a configuration file.  Runs all steps in order.
        """
        run_all(ctx.obj['CLIENT'], blueprint_directory)

    @blueprint_group.command(name="provision")
    @click.argument('blueprint-directory')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_provision(ctx, blueprint_directory):
        """
        provision an blueprint given a configuration file.
        """
        do_setup(ctx.obj['CLIENT'], blueprint_directory)

    @blueprint_group.command(name="configure")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_configure(ctx, configuration):
        """
        configure an blueprint given a configuration file.
        """
        click.echo('blueprint group configure with profile: %s, configuration: %s' % (
            ctx.obj['PROFILE'], configuration))

    @blueprint_group.command(name="validate")
    @click.argument('blueprint-directory')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_validate(ctx, blueprint_directory):
        """
        validate an blueprint given a configuration file.
        """
        do_verify(ctx.obj['CLIENT'], blueprint_directory)

    @blueprint_group.command(name="cleanup")
    @click.argument('blueprint-directory')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_cleanup(ctx, blueprint_directory):
        """
        Tear down a blueprint given a configuration file.
        """
        do_teardown(ctx.obj['CLIENT'], blueprint_directory)

    @blueprint_group.command(name="list")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_list(ctx, configuration):
        """
        List blueprints given a configuration file.
        """
        click.echo('blueprint group list with profile: %s, configuration: %s' % (ctx.obj['PROFILE'],
                                                                                 configuration))
