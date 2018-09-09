"""
Test the cloudless command line interface.
"""
from click.testing import CliRunner
from cloudless.cli import get_cldls

def test_init_subcommand():
    """
    Test that the subcommand to initialize our credentials works.
    """
    runner = CliRunner()
    result = runner.invoke(get_cldls(), ['init'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'TODO: Initialize profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

def test_network_subcommand():
    """
    Test that the subcommand to work with networks works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['network', 'create', 'foobar', 'test-blueprint.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'Network group with profile: default\n'
                             'Network group create with profile: default'
                             ', name: foobar, blueprint: test-blueprint.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'list'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'Network group with profile: default\n'
                             'Network group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'ls'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'Network group with profile: default\n'
                             'Network group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'get', 'foobar'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'Network group with profile: default\n'
                             'Network group get with profile: default'
                             ', name: foobar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'destroy', 'foobar'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'Network group with profile: default\n'
                             'Network group destroy with profile: default'
                             ', name: foobar\n')
    assert result.exception is None
    assert result.exit_code == 0


def test_service_subcommand():
    """
    Test that the subcommand to work with services works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['service', 'create', 'foo', 'bar', 'test-blueprint.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'service group with profile: default\n'
                             'service group create with profile: default'
                             ', network: foo, name: bar, blueprint: test-blueprint.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'list'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'service group with profile: default\n'
                             'service group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'ls'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'service group with profile: default\n'
                             'service group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'get', 'foo', 'bar'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'service group with profile: default\n'
                             'service group get with profile: default'
                             ', network: foo, name: bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'destroy', 'foo', 'bar'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'service group with profile: default\n'
                             'service group destroy with profile: default'
                             ', network: foo, name: bar\n')
    assert result.exception is None
    assert result.exit_code == 0

def test_paths_subcommand():
    """
    Test that the subcommand to work with pathss works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['paths', 'allow_service', 'foo', 'bar', 'baz'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group allow_service with profile: default'
                             ', network: foo, destination: bar, source: baz\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'allow_external', 'foo', 'bar', '0.0.0.0/0'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group allow_external with profile: default'
                             ', network: foo, destination: bar, source: 0.0.0.0/0\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'revoke_service', 'foo', 'bar', 'baz'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group revoke_service with profile: default'
                             ', network: foo, destination: bar, source: baz\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'revoke_external', 'foo', 'bar', '0.0.0.0/0'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group revoke_external with profile: default'
                             ', network: foo, destination: bar, source: 0.0.0.0/0\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'list'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'ls'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'is_internet_accessible', 'foo', 'bar'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group is_internet_accessible with profile: default'
                             ', network: foo, destination: bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'service_has_access', 'foo', 'bar', 'baz'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group service_has_access with profile: default'
                             ', network: foo, destination: bar, source: baz\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'external_has_access', 'foo', 'bar', '0.0.0.0/0'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'paths group with profile: default\n'
                             'paths group external_has_access with profile: default'
                             ', network: foo, destination: bar, source: 0.0.0.0/0\n')
    assert result.exception is None
    assert result.exit_code == 0

def test_image_subcommand():
    """
    Test that the subcommand to work with images works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['image', 'build', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'image group with profile: default\n'
                             'image group build with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'provision', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'image group with profile: default\n'
                             'image group provision with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'configure', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'image group with profile: default\n'
                             'image group configure with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'validate', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'image group with profile: default\n'
                             'image group validate with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'list', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'image group with profile: default\n'
                             'image group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'ls', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'image group with profile: default\n'
                             'image group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

def test_blueprint_subcommand():
    """
    Test that the subcommand to work with blueprints works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['blueprint', 'test', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'blueprint group with profile: default\n'
                             'blueprint group test with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'provision', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'blueprint group with profile: default\n'
                             'blueprint group provision with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'configure', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'blueprint group with profile: default\n'
                             'blueprint group configure with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'validate', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'blueprint group with profile: default\n'
                             'blueprint group validate with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'list', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'blueprint group with profile: default\n'
                             'blueprint group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'ls', 'configuration.yml'])
    assert result.output == ('Debug mode is off\nProfile is default\n'
                             'blueprint group with profile: default\n'
                             'blueprint group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0
