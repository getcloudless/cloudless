"""
Command line interface for test runner.
"""
import json
import click
import butter
from butter.testutils.blueprint_tester import setup as do_setup
from butter.testutils.blueprint_tester import verify as do_verify
from butter.testutils.blueprint_tester import teardown as do_teardown
from butter.testutils.blueprint_tester import run_all

@click.group()
@click.option('--provider', type=click.Choice(["aws", "gce"]))
@click.option('--credentials_file', type=str, default="",
              help="Credentials JSON file")
@click.option('--blueprint_dir', type=str, default=".")
@click.pass_context
def cli(ctx, provider, credentials_file, blueprint_dir):
    """
    Test utility for testing blueprints.
    """
    ctx.obj['PROVIDER'] = provider
    if credentials_file:
        with open(credentials_file) as credentials:
            ctx.obj['CREDENTIALS'] = json.loads(credentials.read())
    else:
        ctx.obj['CREDENTIALS'] = {}
    ctx.obj['BLUEPRINT_DIR'] = blueprint_dir

@cli.command()
@click.pass_context
def setup(ctx):
    """
    Deploy the service and dependencies.
    """
    client = butter.Client(ctx.obj['PROVIDER'], ctx.obj['CREDENTIALS'])
    do_setup(client, ctx.obj['BLUEPRINT_DIR'])

@cli.command()
@click.pass_context
def verify(ctx):
    """
    Verify the service is behaving as expected.
    """
    client = butter.Client(ctx.obj['PROVIDER'], ctx.obj['CREDENTIALS'])
    do_verify(client, ctx.obj['BLUEPRINT_DIR'])

@cli.command()
@click.pass_context
def teardown(ctx):
    """
    Clean up and destroy all resources.
    """
    client = butter.Client(ctx.obj['PROVIDER'], ctx.obj['CREDENTIALS'])
    do_teardown(client, ctx.obj['BLUEPRINT_DIR'])

@cli.command()
@click.pass_context
def run(ctx):
    """
    Run setup, verify, and teardown in sequence.
    """
    client = butter.Client(ctx.obj['PROVIDER'], ctx.obj['CREDENTIALS'])
    run_all(client, ctx.obj['BLUEPRINT_DIR'])

def main():
    """
    Main entry point.
    """
    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    cli(obj={})

if __name__ == '__main__':
    main()
