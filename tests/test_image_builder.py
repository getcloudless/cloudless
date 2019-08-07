"""
Tests for image build framework.
"""
import os
import pytest
import cloudless

from cloudless.testutils.image_builder import ImageBuilder

# Get the blueprint locations relative to the test script
BLUEPRINT_DIR = os.path.join(os.path.dirname(__file__), "image_builder_fixture")
BLUEPRINT_FILE = os.path.join(BLUEPRINT_DIR, "blueprint.yml")
CONFIGURE_FILE = os.path.join(BLUEPRINT_DIR, "configure")
CHECK_FILE = os.path.join(BLUEPRINT_DIR, "check")
BAD_CONFIGURE_FILE = os.path.join(BLUEPRINT_DIR, "configure_bad")
BAD_CHECK_FILE = os.path.join(BLUEPRINT_DIR, "check_bad")

class MockFileSystemWrapper:
    """
    Mocks out read and write so we can test that the image builder behaves as expecte without
    actually writing files.
    """
    def __init__(self):
        self.files = {}

    # pylint:disable=no-self-use
    def write(self, path, data, mode=None):
        """
        Writes to a file, optionally allowing setting file permissions.  Currently does not support
        append mode.
        """
        self.files[path] = {"data": data, "mode": mode}

    # pylint:disable=no-self-use
    def read(self, path):
        """
        Reads a file and returns its data.
        """
        return self.files[path]["data"]

    # pylint:disable=no-self-use
    def exists(self, path):
        """
        Return true if we've written to path.
        """
        return path in self.files

    # pylint:disable=no-self-use
    def remove(self, path):
        """
        Remove the file at the given path.
        """
        del self.files[path]

    # pylint:disable=no-self-use, unused-argument
    def mkdir(self, path):
        """
        Make the directory at the given path.
        """
        return True

@pytest.fixture
def mock_filesystem():
    """
    Pytest fixture to pass a mock filesystem object.
    """
    return MockFileSystemWrapper()

class MockImageBuildConfiguration:
    """
    Mock Image build configuration object.
    """

    def __init__(self):
        self.configure = CONFIGURE_FILE
        self.check = CHECK_FILE

    # pylint:disable=no-self-use
    def get_config_dir(self):
        """
        Get directory of the file behind this configuration.
        """
        return "/test-directory"

    # pylint:disable=no-self-use
    def get_state_dir(self):
        """
        Get directory of the file behind this configuration.
        """
        return "/test-directory/.cloudless/"

    # pylint:disable=no-self-use
    def get_blueprint_path(self):
        """
        Get path to the blueprint being tested.
        """
        return BLUEPRINT_FILE

    def get_configure_script_path(self):
        """
        Get the path for the configure script.
        """
        return self.configure

    def set_configure_script_path(self, configure):
        """
        Set the path for the configure script.
        """
        self.configure = configure

    def get_check_script_path(self):
        """
        Get the path for the check script.
        """
        return self.check

    def set_check_script_path(self, check):
        """
        Set the path for the check script.
        """
        self.check = check

    # pylint:disable=no-self-use
    def get_image_name(self):
        """
        Get the image name to save as.
        """
        return "my-test-image"

@pytest.fixture
def mock_image_build_configuration():
    """
    Pytest fixture to pass a mock image build configuration object.
    """
    return MockImageBuildConfiguration()

# pylint:disable=redefined-outer-name
@pytest.mark.mock_aws
def test_image_builder(mock_filesystem, mock_image_build_configuration):
    """
    Test image builder using the mock-aws provider.
    """
    client = cloudless.Client("mock-aws", {})
    image_builder = ImageBuilder(client, config=mock_image_build_configuration,
                                 filesystem=mock_filesystem)

    # Make sure we can actually deploy the service.
    deployed_service, state = image_builder.deploy()
    network = client.network.get(state["network"])
    assert network
    assert network.name == deployed_service.network.name
    service = client.service.get(network, state["service"])
    assert service
    assert service.name == deployed_service.name

    # Make sure configure works and properly finds errors.
    image_builder.configure()
    mock_image_build_configuration.set_configure_script_path(BAD_CONFIGURE_FILE)
    with pytest.raises(Exception):
        image_builder.configure()
        pytest.fail("Expected exception on bad configure file")
    mock_image_build_configuration.set_configure_script_path(CONFIGURE_FILE)
    image_builder.configure()

    # Make sure check works and properly finds errors.
    image_builder.check()
    mock_image_build_configuration.set_check_script_path(BAD_CHECK_FILE)
    with pytest.raises(Exception):
        image_builder.check()
        pytest.fail("Expected exception on bad check file")
    mock_image_build_configuration.set_check_script_path(CHECK_FILE)
    image_builder.check()

    # Make sure things are gone when we clean up.
    image_builder.cleanup()
    network = client.network.get(state["network"])
    assert not network

    image_builder.run(mock=True)
