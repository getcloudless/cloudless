"""
Tests for blueprint reader.
"""
import os
import pytest
from cloudless.util.blueprint import ServiceBlueprint
from cloudless.util.exceptions import BlueprintException


# Get the blueprint locations relative to the test script
BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "variables_test_blueprints")
INSTANCES_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "blueprint-test.yml")
NOVARS_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "blueprint-test-novars.yml")
OPTIONAL_SET = """# Blueprint Test
# Only to test that the jinja2 templating is handled properly.
# other_template_var: 
# list_var: foo
# other_var: bar
# optional_var: baz"""
OPTIONAL_NOT_SET = """# Blueprint Test
# Only to test that the jinja2 templating is handled properly.
# other_template_var: 
# list_var: foo
# other_var: bar
# optional_var: """

def test_blueprint():
    """
    Blueprint reader tests.
    """
    sbp = ServiceBlueprint.from_file(INSTANCES_BLUEPRINT)
    template_vars = {"list_var": ["foo"], "other_var": ["bar"]}
    assert sbp.runtime_scripts(template_vars) == OPTIONAL_NOT_SET
    template_vars = {"list_var": ["foo"], "other_var": ["bar"], "optional_var": ["baz"]}
    assert sbp.runtime_scripts(template_vars) == OPTIONAL_SET
    template_vars = {"list_var": ["foo"], "other_var": ["bar"], "optional_var": ["baz"],
                     "unrecognized_var": ["bop"]}
    with pytest.raises(BlueprintException):
        sbp.runtime_scripts(template_vars)
        pytest.fail("Expected unrecognized value exception")
    with pytest.raises(BlueprintException):
        sbp.runtime_scripts({})
        pytest.fail("Expected missing value exception")
    sbp = ServiceBlueprint.from_file(NOVARS_BLUEPRINT)
    sbp.runtime_scripts({})
