"""
Cloudless blueprint command line interface.
"""
import click

def add_blueprint_group(cldls):
    """
    Add commands for the blueprint command group.
    """
    @cldls.group(name='blueprint')
    @click.option('--dev/--no-dev', default=False, help="Development mode.")
    @click.pass_context
    def blueprint_group(ctx, dev):
        """
        Commands to manage service blueprints.

        Commands to interact with machine blueprints.
        """
        click.echo('blueprint group with profile: %s' % ctx.obj['PROFILE'])
        ctx.obj['DEV'] = dev

    @blueprint_group.command(name="test")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_build(ctx, configuration):
        """
        Test an blueprint given a configuration file.  Runs all steps in order.
        """
        click.echo('blueprint group test with profile: %s, configuration: %s' % (ctx.obj['PROFILE'],
                                                                                 configuration))

    @blueprint_group.command(name="provision")
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_provision(ctx, configuration):
        """
        provision an blueprint given a configuration file.
        """
        click.echo('blueprint group provision with profile: %s, configuration: %s' % (
            ctx.obj['PROFILE'], configuration))

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
    @click.argument('configuration')
    @click.pass_context
    # pylint:disable=unused-variable
    def blueprint_validate(ctx, configuration):
        """
        validate an blueprint given a configuration file.
        """
        click.echo('blueprint group validate with profile: %s, configuration: %s' % (
            ctx.obj['PROFILE'], configuration))

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
