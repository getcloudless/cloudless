"""
Test that profile management works properly.
"""
import os
from unittest.mock import patch
import cloudless.profile


@patch('cloudless.profile.FileConfigSource')
def test_profile(mock_instance):
    """
    Test that managing the profile works properly.  Note this isn't a great test at the moment, but
    it's a pain with all the filesystem access.  The class that this is mocking should just save and
    load a configuration dictionary to and from the filesystem.
    """
    mock_instance = mock_instance.return_value
    mock_instance.load.return_value = {"myprofile": {"provider": "mock-aws"}}

    # Load profile we mocked out
    result = cloudless.profile.load_profile("myprofile")
    assert result == {"provider": "mock-aws"}

    # Load nonexistent profile
    result = cloudless.profile.load_profile("myprofile2")
    assert not result

    # Save nonexistent profile and load it back
    cloudless.profile.save_profile("myprofile2", {"provider": "mock-aws"})
    result = cloudless.profile.load_profile("myprofile2")
    assert result == {"provider": "mock-aws"}

    # Test our profile selection rules
    if "CLOUDLESS_PROFILE" in os.environ:
        del os.environ["CLOUDLESS_PROFILE"]
    assert cloudless.profile.select_profile(None) == "default"
    assert cloudless.profile.select_profile("foo") == "foo"
    os.environ["CLOUDLESS_PROFILE"] = "bar"
    assert cloudless.profile.select_profile(None) == "bar"
    assert cloudless.profile.select_profile("foo") == "foo"
