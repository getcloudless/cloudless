"""
Cloudless image command line interface.
"""
import click

def add_image_group(cldls):
    """
    Add commands for the image command group.
    """
    @cldls.group(name='image')
    @click.option('--dev/--no-dev', default=False, help="Development mode.")
    @click.pass_context
    def image_group(ctx, dev):
        """
        Commands to manage machine images.

        Commands to interact with machine images.
        """
        click.echo('image group with profile: %s' % ctx.obj['PROFILE'])
        ctx.obj['DEV'] = dev

    @image_group.command(name="build")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_build(ctx, configuration):
        """
        Build an image given a configuration file.  Runs all steps in order and saves the image at
        the end.

        This is the only way to save images, which ensures that every saved image had all the tests
        pass.
        """
        click.echo('image group build with profile: %s, configuration: %s' % (ctx.obj['PROFILE'],
                                                                              configuration))

    @image_group.command(name="provision")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_provision(ctx, configuration):
        """
        provision an image given a configuration file.
        """
        click.echo('image group provision with profile: %s, configuration: %s' % (
            ctx.obj['PROFILE'], configuration))

    @image_group.command(name="configure")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_configure(ctx, configuration):
        """
        configure an image given a configuration file.
        """
        click.echo('image group configure with profile: %s, configuration: %s' % (
            ctx.obj['PROFILE'], configuration))

    @image_group.command(name="validate")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_validate(ctx, configuration):
        """
        validate an image given a configuration file.
        """
        click.echo('image group validate with profile: %s, configuration: %s' % (ctx.obj['PROFILE'],
                                                                                 configuration))

    @image_group.command(name="list")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_list(ctx, configuration):
        """
        List images given a configuration file.
        """
        click.echo('image group list with profile: %s, configuration: %s' % (ctx.obj['PROFILE'],
                                                                             configuration))
