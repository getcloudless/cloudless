"""
AWS Model Tests
"""
import pytest
import cloudless

@pytest.fixture
def model():
    """
    Pytest fixture to create a mock model.
    """
    return cloudless.providers.aws.model.AWSProjectModel([], [], [], [])

@pytest.fixture
def base_model_yaml():
    """
    The YAML output for the base model without changes.
    """
    return """[]
"""

@pytest.fixture
def new_model_yaml():
    """
    The YAML output for the base model without changes.
    """
    return """"""

@pytest.fixture
def diff_model_yaml():
    """
    The YAML output for the base model without changes.
    """
    return """"""

# pylint:disable=redefined-outer-name
def test_model(model, base_model_yaml):
    """
    Test that model works properly.
    """
    assert model
    assert model.to_yaml() == base_model_yaml
