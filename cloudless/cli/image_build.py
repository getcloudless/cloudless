"""
Cloudless image build command line interface.
"""
import os
import sys
import click
from cloudless.cli.utils import NaturalOrderAliasedGroup
from cloudless.cli.utils import handle_profile_for_cli
from cloudless.util.image_build_configuration import ImageBuildConfiguration
from cloudless.testutils.image_builder import ImageBuilder

def add_image_build_group(cldls):
    """
    Add commands for the image_build command group.
    """
    @cldls.group(name='image-build', cls=NaturalOrderAliasedGroup)
    @click.option('--dev/--no-dev', default=False, help="Development mode.")
    @click.pass_context
    def image_build_group(ctx, dev):
        """
        Tools to build and test instance images.

        Commands to interact with machine images.
        """
        handle_profile_for_cli(ctx)
        click.echo('image group with provider: %s' % ctx.obj['PROVIDER'])
        ctx.obj['DEV'] = dev

    @image_build_group.command(name="deploy")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_build_deploy(ctx, config):
        """
        deploy an image given a configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        config_obj = ImageBuildConfiguration(config)
        image_builder = ImageBuilder(ctx.obj['CLIENT'], config=config_obj)
        service, state = image_builder.deploy()
        click.echo('Successfully deployed!  Log in with:')
        for instance in ctx.obj['CLIENT'].service.get_instances(service):
            click.echo("ssh -i %s %s@%s" % (state["ssh_private_key"], state["ssh_username"],
                                            instance.public_ip))

    @image_build_group.command(name="configure")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_build_configure(ctx, config):
        """
        configure an image given a config file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        config_obj = ImageBuildConfiguration(config)
        image_builder = ImageBuilder(ctx.obj['CLIENT'], config=config_obj)
        image_builder.configure()
        click.echo('Configure complete!')

    @image_build_group.command(name="check")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_build_check(ctx, config):
        """
        check an image given a configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        config_obj = ImageBuildConfiguration(config)
        image_builder = ImageBuilder(ctx.obj['CLIENT'], config=config_obj)
        image_builder.check()
        click.echo('Check complete!')

    @image_build_group.command(name="cleanup")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_build_cleanup(ctx, config):
        """
        cleanup images given a configuration file.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        config_obj = ImageBuildConfiguration(config)
        image_builder = ImageBuilder(ctx.obj['CLIENT'], config=config_obj)
        image_builder.cleanup()
        click.echo('Cleanup complete!')

    @image_build_group.command(name="run")
    @click.argument('config')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_build_run(ctx, config):
        """
        Build an image given a configuration file.  Runs all steps in order and saves the image at
        the end.

        This is the only way to save images, which ensures that every saved image had all the tests
        pass.
        """
        if os.path.isdir(config):
            click.echo("Configuration must be a file, not a directory!")
            sys.exit(1)
        config_obj = ImageBuildConfiguration(config)
        image_builder = ImageBuilder(ctx.obj['CLIENT'], config=config_obj)
        if ctx.obj['PROVIDER'] == "mock-aws":
            image_builder.run(mock=True)
        else:
            image_builder.run()
        click.echo('Build complete!')
