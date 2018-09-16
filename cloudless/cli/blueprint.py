"""
Cloudless blueprint command line interface.
"""
import sys
import os
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
        <config_path>/blueprint-test-state.json.
        """
        ctx.obj['DEV'] = dev
        profile = cloudless.profile.load_profile(ctx.obj['PROFILE'])
        if not profile:
            click.echo("Profile: \"%s\" not found." % ctx.obj['PROFILE'])
            click.echo("Try running \"cldls --profile %s init\"." % ctx.obj['PROFILE'])
            sys.exit(1)
        ctx.obj['PROVIDER'] = profile["provider"]
        ctx.obj['CREDENTIALS'] = profile["credentials"]
        click.echo('Blueprint group with provider: %s' % ctx.obj['PROVIDER'])
        ctx.obj['CLIENT'] = cloudless.Client(provider=ctx.obj['PROVIDER'],
                                             credentials=ctx.obj['CREDENTIALS'])

    @blueprint_group.command(name="create")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_create(ctx, config):
        """
        Create test service from blueprint.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        do_setup(ctx.obj['CLIENT'], config)
        click.echo("Creation complete!")

    @blueprint_group.command(name="verify")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_verify(ctx, config):
        """
        Verify test service is behaving as expected.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        do_verify(ctx.obj['CLIENT'], config)
        click.echo("Verify complete!")

    @blueprint_group.command(name="cleanup")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_cleanup(ctx, config):
        """
        Cleanup test service.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        do_teardown(ctx.obj['CLIENT'], config)
        click.echo("Cleanup complete!")

    @blueprint_group.command(name="test")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_test(ctx, config):
        """
        Run create, verify, and cleanup.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        run_all(ctx.obj['CLIENT'], config)
        click.echo("Full test run complete!")
