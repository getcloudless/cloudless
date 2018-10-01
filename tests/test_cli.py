"""
Test the cloudless command line interface.
"""
import os
import shutil
import re
from unittest.mock import patch
from click.testing import CliRunner
from cloudless.cli.cldls import get_cldls
import cloudless.profile

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
NETWORK_BLUEPRINT = os.path.join(EXAMPLES_DIR, "network", "blueprint.yml")
AWS_SERVICE_BLUEPRINT = os.path.join(EXAMPLES_DIR, "base-image", "aws_blueprint.yml")

# Get the blueprint locations relative to the test script
BLUEPRINT_DIR = os.path.join(os.path.dirname(__file__), "cli_blueprint_tester_fixture")
BLUEPRINT_TEST_CONFIGURATION = os.path.join(BLUEPRINT_DIR, "blueprint-test-configuration.yml")
BLUEPRINT_TEST_STATE = os.path.join(BLUEPRINT_DIR, ".cloudless")

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "cli_image_build_fixture")
IMAGE_BUILD_CONFIGURATION = os.path.join(IMAGE_DIR, "image-build-configuration.yml")
IMAGE_BUILD_STATE = os.path.join(IMAGE_DIR, ".cloudless")

# Make sure we don't leak this from the environment.
if 'CLOUDLESS_PROFILE' in os.environ:
    del os.environ['CLOUDLESS_PROFILE']

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
    assert result.exception is None
    assert result.output == ('Setting provider for profile "default" to "mock-aws"\n')
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
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws", "credentials": {}}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws", "credentials": {}}

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
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws", "credentials": {}}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws", "credentials": {}}

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
        r'name: bar\n'
        r'has_access_to:\n'
        r'- default-all-outgoing-allowed\n'
        r'is_accessible_from: \[\]\n'
        r'network:\n'
        r'  name: foo\n'
        r'  id: vpc-.*\n'
        r'  block: 10.0.0.0/16\n'
        r'  region: us-east-1\n'
        r'  subnetworks:\n'
        r'  - name: bar\n'
        r'    id: subnet-.*\n'
        r'    block: 10.0..*.0/23\n'
        r'    region: us-east-1\n'
        r'    availability_zone: us-east-1.\n'
        r'    instances:\n'
        r'    - id: i-.*\n'
        r'      public_ip: .*\n'
        r'      private_ip: .*\n'
        r'      state: running\n'
        r'      availability_zone: us-east-1.\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'destroy', 'foo', 'bar'])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Destroyed service: bar in network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    # Destroy the network we created.
    result = runner.invoke(get_cldls(), ['network', 'destroy', 'foo'])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Destroyed network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_service_subcommand_with_count(mock_config_source):
    """
    Test that the subcommand to work with services works.
    """
    # Do some mock weirdness to make sure our commands get the right values for the default profile.
    mock_config_source = mock_config_source.return_value
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws", "credentials": {}}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws", "credentials": {}}

    runner = CliRunner()

    # Create the network that I'll deploy into
    result = runner.invoke(get_cldls(), ['network', 'create', 'foo', NETWORK_BLUEPRINT])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Created network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'create', 'foo', 'bar', AWS_SERVICE_BLUEPRINT,
                                         '--count', '3'])
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
        r'name: bar\n'
        r'has_access_to:\n'
        r'- default-all-outgoing-allowed\n'
        r'is_accessible_from: \[\]\n'
        r'network:\n'
        r'  name: foo\n'
        r'  id: vpc-.*\n'
        r'  block: 10.0.0.0/16\n'
        r'  region: us-east-1\n'
        r'  subnetworks:\n'
        r'  - name: bar\n'
        r'    id: subnet-.*\n'
        r'    block: 10.0..*.0/23\n'
        r'    region: us-east-1\n'
        r'    availability_zone: us-east-1.\n'
        r'    instances:\n'
        r'    - id: i-.*\n'
        r'      public_ip: .*\n'
        r'      private_ip: .*\n'
        r'      state: running\n'
        r'      availability_zone: us-east-1.\n'
        r'    - id: i-.*\n'
        r'      public_ip: .*\n'
        r'      private_ip: .*\n'
        r'      state: running\n'
        r'      availability_zone: us-east-1.\n'
        r'    - id: i-.*\n'
        r'      public_ip: .*\n'
        r'      private_ip: .*\n'
        r'      state: running\n'
        r'      availability_zone: us-east-1.\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'destroy', 'foo', 'bar'])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Destroyed service: bar in network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    # Destroy the network we created.
    result = runner.invoke(get_cldls(), ['network', 'destroy', 'foo'])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Destroyed network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_service_test_subcommand(mock_config_source):
    """
    Test that the subcommand to work with blueprints works.
    """
    runner = CliRunner()

    # Remove state from old tests that may have failed.
    if os.path.exists(BLUEPRINT_TEST_STATE):
        shutil.rmtree(BLUEPRINT_TEST_STATE)

    # Do some mock weirdness to make sure our commands get the right values for the default profile.
    mock_config_source = mock_config_source.return_value
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws", "credentials": {}}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws", "credentials": {}}

    result = runner.invoke(get_cldls(), ['service-test', 'deploy', BLUEPRINT_TEST_CONFIGURATION])
    assert result.output == (pytest_regex(
        r'Service test group with provider: mock-aws\n'
        r'Deploy complete!\n'
        r'To log in, run:\n'
        r'ssh -i /.*/tests/.*/.cloudless/id_rsa_test cloudless_service_test@.*\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service-test', 'check', BLUEPRINT_TEST_CONFIGURATION])
    assert result.output == (pytest_regex(
        r'Service test group with provider: mock-aws\n'
        r'Check complete!\n'
        r'To log in, run:\n'
        r'ssh -i /.*/tests/.*/.cloudless/id_rsa_test cloudless_service_test@.*\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service-test', 'cleanup', BLUEPRINT_TEST_CONFIGURATION])
    assert result.output == ('Service test group with provider: mock-aws\n'
                             'Cleanup complete!\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service-test', 'run', BLUEPRINT_TEST_CONFIGURATION])
    assert result.output == ('Service test group with provider: mock-aws\n'
                             'Full test run complete!\n')
    assert result.exception is None
    assert result.exit_code == 0

# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument,too-many-statements
@patch('cloudless.profile.FileConfigSource')
def test_paths_subcommand(mock_config_source):
    """
    Test that the subcommand to work with pathss works.
    """
    # Do some mock weirdness to make sure our commands get the right values for the default profile.
    mock_config_source = mock_config_source.return_value
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws", "credentials": {}}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws", "credentials": {}}

    runner = CliRunner()

    # Create the network and services I'll be connecting.
    result = runner.invoke(get_cldls(), ['network', 'create', 'foo', NETWORK_BLUEPRINT])
    assert result.output == ('Network group with provider: mock-aws\n'
                             'Created network: foo\n')
    assert result.exit_code == 0
    assert result.exception is None

    result = runner.invoke(get_cldls(), ['service', 'create', 'foo', 'bar', AWS_SERVICE_BLUEPRINT])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Created service: bar in network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['service', 'create', 'foo', 'baz', AWS_SERVICE_BLUEPRINT])
    assert result.output == ('Service group with provider: mock-aws\n'
                             'Created service: baz in network: foo\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'allow_service', 'foo', 'bar', 'baz', '80'])
    assert result.exception is None
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Added path from baz to bar in network foo for port 80\n')
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'allow_network_block', 'foo', 'bar', '0.0.0.0/0',
                                         '80'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Added path from 0.0.0.0/0 to bar in network foo for port 80\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'list'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'foo:baz -(80)-> foo:bar\n'
                             'external:0.0.0.0/0 -(80)-> foo:bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'ls'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'foo:baz -(80)-> foo:bar\n'
                             'external:0.0.0.0/0 -(80)-> foo:bar\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'revoke_service', 'foo', 'bar', 'baz', '80'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Removed path from baz to bar in network foo for port 80\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'revoke_network_block', 'foo', 'bar', '0.0.0.0/0',
                                         '80'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Removed path from 0.0.0.0/0 to bar in network foo for port 80\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'is_internet_accessible', 'foo', 'bar', '80'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Service bar in network foo is not internet accessible on port 80\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'service_has_access', 'foo', 'bar', 'baz', '80'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Service baz does not have access to bar in network foo on port 80\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['paths', 'network_block_has_access', 'foo', 'bar',
                                         '0.0.0.0/0', '80'])
    assert result.output == ('Paths group with provider: mock-aws\n'
                             'Network 0.0.0.0/0 does not have access to bar in '
                             'network foo on port 80\n')
    assert result.exception is None
    assert result.exit_code == 0


# Need to patch this so the test doesn't mess up our real configuration.
# pylint:disable=unused-argument
@patch('cloudless.profile.FileConfigSource')
def test_image_build_subcommand(mock_config_source):
    """
    Test that the subcommand to work with images works.
    """
    runner = CliRunner()

    # Do some mock weirdness to make sure our commands get the right values for the default profile.
    mock_config_source = mock_config_source.return_value
    mock_config_source.load.return_value = {"default": {"provider": "mock-aws", "credentials": {}}}
    result = cloudless.profile.load_profile("default")
    assert result == {"provider": "mock-aws", "credentials": {}}

    # Remove state from old tests that may have failed.
    if os.path.exists(IMAGE_BUILD_STATE):
        shutil.rmtree(IMAGE_BUILD_STATE)

    result = runner.invoke(get_cldls(), ['image-build', 'deploy', IMAGE_BUILD_CONFIGURATION])
    assert result.exception is None
    assert result.output == (pytest_regex(
        r'image group with provider: mock-aws\n'
        r'Successfully deployed!  Log in with:\n'
        r'ssh -i /.*/tests/.*/.cloudless/id_rsa_image_build cloudless_image_build@.*\n'))
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image-build', 'configure', IMAGE_BUILD_CONFIGURATION])
    assert result.output == ('image group with provider: mock-aws\n'
                             'Configure complete!\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image-build', 'check', IMAGE_BUILD_CONFIGURATION])
    assert result.output == ('image group with provider: mock-aws\n'
                             'Check complete!\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image-build', 'cleanup', IMAGE_BUILD_CONFIGURATION])
    assert result.output == ('image group with provider: mock-aws\n'
                             'Cleanup complete!\n')
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image-build', 'run', IMAGE_BUILD_CONFIGURATION])
    assert result.output == ('image group with provider: mock-aws\n'
                             'Build complete!\n')
    assert result.exception is None
    assert result.exit_code == 0

    # Need to test these with the image build commands otherwise they would race in parallel tests.
    result = runner.invoke(get_cldls(), ['image', 'get', 'my-image'])
    assert result.output == (pytest_regex(
        r'image group with provider: mock-aws\n'
        r'Image Name: .*\n'
        r'Image Id: .*\n'
        r'Image Created At: .*\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'list'])
    assert result.output == (pytest_regex(
        r'image group with provider: mock-aws\n'
        r'Listing all images.\n'
        r'Image Name: .*\n'
        r'Image Id: .*\n'
        r'Image Created At: .*\n'))
    assert result.exception is None
    assert result.exit_code == 0

    result = runner.invoke(get_cldls(), ['image', 'delete', 'my-image'])
    assert result.output == ('image group with provider: mock-aws\n'
                             'Deleted image: my-image\n')
    assert result.exception is None
    assert result.exit_code == 0
