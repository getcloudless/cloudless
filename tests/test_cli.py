"""
Test the cloudless command line interface.
"""
import os
import re
from unittest.mock import patch
from click.testing import CliRunner
from cloudless.cli.cldls import get_cldls
import cloudless.profile

EXAMPLE_BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "..", "example-blueprints")
NETWORK_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR, "network", "blueprint.yml")
AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLE_BLUEPRINTS_DIR, "aws-nginx", "blueprint.yml")

# See https://kalnytskyi.com/howto/assert-str-matches-regex-in-pytest/
# pylint:disable=invalid-name
class pytest_regex:
    """Assert that a given string meets some expectations."""

    def __init__(self, pattern, flags=0):
        self._regex = re.compile(pattern, flags)

    def __eq__(self, actual):
        return bool(self._regex.match(actual))

    def __repr__(self):
        return self._regex.pattern

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_init_subcommand(mock_config_source):
    """
    Test that the subcommand to initialize our credentials works.
    """
    runner = CliRunner()
    result = runner.invoke(get_cldls(), ['init', '--provider', 'mock-aws'])
    assert result.output == ('Setting provider for profile "default" to "mock-aws"\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_network_subcommand(mock_config_source):
    """
    Test that the subcommand to work with networks works.
    """
    # Do some mock weirdness to make sure our commands get the right values for the default profile.
    mock_config_source = mock_config_source.return_value
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws"}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws"}

    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['network', 'create', 'foobar', NETWORK_BLUEPRINT])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Created network: foobar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'list'])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Networks: [None, \'foobar\']\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'ls'])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Networks: [None, \'foobar\']\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'get', 'foobar'])
    assert result.output == (pytest_regex('Network group with provider: mock-aws\n'
                                          'Name: foobar\n'
                                          'Id: vpc-.*\n'
                                          'Network: 10.0.0.0/16\n'
                                          'Region: us-east-1\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['network', 'destroy', 'foobar'])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Destroyed network: foobar\n')
    assert result.exception is None
    assert result.exit_code == 0


# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_service_subcommand(mock_config_source):
    """
    Test that the subcommand to work with services works.
    """
    # Do some mock weirdness to make sure our commands get the right values for the default profile.
    mock_config_source = mock_config_source.return_value
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws"}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws"}

    runner = CliRunner()

    # Create the network that I'll deploy into
    result = runner.invoke(get_cldls(), ['network', 'create', 'foo', NETWORK_BLUEPRINT])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Created network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'create', 'foo', 'bar', AWS_SERVICE_BLUEPRINT])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Created service: bar in network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'list'])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Network: foo, Service: bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'ls'])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Network: foo, Service: bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'get', 'foo', 'bar'])
    assert result.output == (pytest_regex(
        r'Service group with provider: mock-aws\n'
        r'Name: bar\n'
        r'Network Name: foo.*\n'
        r'Network Id: vpc-.*\n'
        r'Network Block: 10.0.0.0/16\n'
        r'Network Region: us-east-1\n'
        r'    Subnetwork Name: None\n.*'
        r'    Subnetwork Id: subnet-.*\n'
        r'    Subnetwork Block: 10.0.0.0/24\n'
        r'    Subnetwork Region: us-east-1\n.*'
        r'    Subnetwork Availability_zone: us-east-1a\n'
        r'        Instance Id: i-.*\n'
        r'        Instance Public IP: .*\..*\..*\..*\n'
        r'        Instance Private IP: 10\..*\..*\..*\n'
        r'        Instance State: running\n'
        r'    Subnetwork Name: None\n'
        r'    Subnetwork Id: subnet-.*\n'
        r'    Subnetwork Block: 10.0.1.0/24\n'
        r'    Subnetwork Region: us-east-1\n'
        r'    Subnetwork Availability_zone: us-east-1b\n'
        r'        Instance Id: i-.*\n'
        r'        Instance Public IP: .*\..*\..*\..*\n'
        r'        Instance Private IP: 10\..*\..*\..*\n'
        r'        Instance State: running\n'
        r'    Subnetwork Name: None\n'
        r'    Subnetwork Id: subnet-.*\n'
        r'    Subnetwork Block: 10.0.2.0/24\n'
        r'    Subnetwork Region: us-east-1\n'
        r'    Subnetwork Availability_zone: us-east-1c\n'
        r'        Instance Id: i-.*\n'
        r'        Instance Public IP: .*\..*\..*\..*\n'
        r'        Instance Private IP: 10\..*\..*\..*\n'
        r'        Instance State: running\n'))

    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'destroy', 'foo', 'bar'])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Destroyed service: bar in network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_paths_subcommand(mock_config_source):
    """
    Test that the subcommand to work with pathss works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['paths', 'allow_service', 'foo', 'bar', 'baz'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group allow_service with profile: default'
                             ', network: foo, destination: bar, source: baz\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'allow_external', 'foo', 'bar', '0.0.0.0/0'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group allow_external with profile: default'
                             ', network: foo, destination: bar, source: 0.0.0.0/0\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'revoke_service', 'foo', 'bar', 'baz'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group revoke_service with profile: default'
                             ', network: foo, destination: bar, source: baz\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'revoke_external', 'foo', 'bar', '0.0.0.0/0'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group revoke_external with profile: default'
                             ', network: foo, destination: bar, source: 0.0.0.0/0\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'list'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'ls'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group list with profile: default\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'is_internet_accessible', 'foo', 'bar'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group is_internet_accessible with profile: default'
                             ', network: foo, destination: bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'service_has_access', 'foo', 'bar', 'baz'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group service_has_access with profile: default'
                             ', network: foo, destination: bar, source: baz\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'external_has_access', 'foo', 'bar', '0.0.0.0/0'])
    assert result.output == ('paths group with profile: default\n'
                             'paths group external_has_access with profile: default'
                             ', network: foo, destination: bar, source: 0.0.0.0/0\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_image_subcommand(mock_config_source):
    """
    Test that the subcommand to work with images works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['image', 'build', 'configuration.yml'])
    assert result.output == ('image group with profile: default\n'
                             'image group build with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'provision', 'configuration.yml'])
    assert result.output == ('image group with profile: default\n'
                             'image group provision with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'configure', 'configuration.yml'])
    assert result.output == ('image group with profile: default\n'
                             'image group configure with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'validate', 'configuration.yml'])
    assert result.output == ('image group with profile: default\n'
                             'image group validate with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'list', 'configuration.yml'])
    assert result.output == ('image group with profile: default\n'
                             'image group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'ls', 'configuration.yml'])
    assert result.output == ('image group with profile: default\n'
                             'image group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_blueprint_subcommand(mock_config_source):
    """
    Test that the subcommand to work with blueprints works.
    """
    runner = CliRunner()

    result = runner.invoke(get_cldls(), ['blueprint', 'test', 'configuration.yml'])
    assert result.output == ('blueprint group with profile: default\n'
                             'blueprint group test with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'provision', 'configuration.yml'])
    assert result.output == ('blueprint group with profile: default\n'
                             'blueprint group provision with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'configure', 'configuration.yml'])
    assert result.output == ('blueprint group with profile: default\n'
                             'blueprint group configure with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'validate', 'configuration.yml'])
    assert result.output == ('blueprint group with profile: default\n'
                             'blueprint group validate with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'list', 'configuration.yml'])
    assert result.output == ('blueprint group with profile: default\n'
                             'blueprint group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['blueprint', 'ls', 'configuration.yml'])
    assert result.output == ('blueprint group with profile: default\n'
                             'blueprint group list with profile: default'
                             ', configuration: configuration.yml\n')
    assert result.exception is None
    assert result.exit_code == 0
