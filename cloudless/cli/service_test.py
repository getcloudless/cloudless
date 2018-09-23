
"""
Cloudless service-test command line interface.
"""
import sys
import os
import click
from cloudless.cli.utils import NaturalOrderAliasedGroup
from cloudless.testutils.blueprint_tester import setup as do_setup
from cloudless.testutils.blueprint_tester import verify as do_verify
from cloudless.testutils.blueprint_tester import teardown as do_teardown
from cloudless.testutils.blueprint_tester import run_all
from cloudless.cli.utils import handle_profile_for_cli

def add_service_test_group(cldls):
    """
    Add commands for the service_test command group.
    """
    @cldls.group(name='service-test', cls=NaturalOrderAliasedGroup)
    @click.option('--dev/--no-dev', default=False, help="Development mode.")
    @click.pass_context
    def service_test_group(ctx, dev):
        """
        Service testing framework.

        Test framework to make sure the service behaves as expected.  Manages the lifecycle of the
        service being tested.  Saves state into <config_path>/blueprint-test-state.json.
        """
        ctx.obj['DEV'] = dev
        handle_profile_for_cli(ctx)
        click.echo('Service test group with provider: %s' % ctx.obj['PROVIDER'])

    @service_test_group.command(name="deploy")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_test_deploy(ctx, config):
        """
        Deploy test service.

        Config must be the path to a test configuration file.  This will actually deploy a service
        with all its dependencies on the configured cloud provider.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        service, ssh_username, private_key_path = do_setup(ctx.obj['CLIENT'], config)
        click.echo("Deploy complete!")
        click.echo("To log in, run:")
        for instance in ctx.obj['CLIENT'].service.get_instances(service):
            click.echo("ssh -i %s %s@%s" % (private_key_path, ssh_username, instance.public_ip))

    @service_test_group.command(name="check")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_test_check(ctx, config):
        """
        Check test service is behaving as expected.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        service, ssh_username, private_key_path = do_verify(ctx.obj['CLIENT'], config)
        click.echo("Check complete!")
        click.echo("To log in, run:")
        for instance in ctx.obj['CLIENT'].service.get_instances(service):
            click.echo("ssh -i %s %s@%s" % (private_key_path, ssh_username, instance.public_ip))

    @service_test_group.command(name="cleanup")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_test_cleanup(ctx, config):
        """
        Cleanup test service.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        do_teardown(ctx.obj['CLIENT'], config)
        click.echo("Cleanup complete!")

    @service_test_group.command(name="run")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def service_test_run(ctx, config):
        """
        Run create, verify, and cleanup.

        Config must be the path to a test configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        run_all(ctx.obj['CLIENT'], config)
        click.echo("Full test run complete!")
