"""
Cloudless image command line interface.
"""
import sys
import click
from cloudless.cli.utils import NaturalOrderAliasedGroup
from cloudless.cli.utils import handle_profile_for_cli

def add_image_group(cldls):
    """
    Add commands for the image command group.
    """
    @cldls.group(name='image', cls=NaturalOrderAliasedGroup)
    @click.option('--dev/--no-dev', default=False, help="Development mode.")
    @click.pass_context
    def image_group(ctx, dev):
        """
        Tools to build and test instance images.

        Commands to interact with machine images.
        """
        handle_profile_for_cli(ctx)
        click.echo('image group with provider: %s' % ctx.obj['PROVIDER'])
        ctx.obj['DEV'] = dev

    @image_group.command(name="get")
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_get(ctx, name):
        """
        Get an image given a name.
        """
        image = ctx.obj['CLIENT'].image.get(name)
        if not image:
            click.echo("Image %s does not exist" % name)
            sys.exit(1)
        click.echo("Image Name: %s" % image.name)
        click.echo("Image Id: %s" % image.image_id)
        click.echo("Image Created At: %s" % image.created_at)

    @image_group.command(name="list")
    @click.pass_context
    # pylint:disable=unused-variable
    def image_list(ctx):
        """
        List images.
        """
        images = ctx.obj['CLIENT'].image.list()
        click.echo("Listing all images.")
        for image in images:
            click.echo("Image Name: %s" % image.name)
            click.echo("Image Id: %s" % image.image_id)
            click.echo("Image Created At: %s" % image.created_at)

    @image_group.command(name="delete")
    @click.argument('name')
    @click.pass_context
    # pylint:disable=unused-variable
    def image_delete(ctx, name):
        """
        Delete an image.
        """
        image = ctx.obj['CLIENT'].image.get(name)
        if not image:
            click.echo("Image %s does not exist" % name)
            sys.exit(1)
        ctx.obj['CLIENT'].image.destroy(image)
        click.echo("Deleted image: %s" % name)
