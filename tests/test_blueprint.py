"""
Tests for blueprint reader.
"""
import os
import pytest
from butter.util.blueprint import ServiceBlueprint
from butter.util.exceptions import BlueprintException


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
    instances_blueprint = ServiceBlueprint(INSTANCES_BLUEPRINT,
                                           {"list_var": ["foo"],
                                            "other_var": ["bar"]})
    assert instances_blueprint.runtime_scripts() == OPTIONAL_NOT_SET
    instances_blueprint = ServiceBlueprint(INSTANCES_BLUEPRINT,
                                           {"list_var": ["foo"],
                                            "other_var": ["bar"],
                                            "optional_var": ["baz"]})
    assert instances_blueprint.runtime_scripts() == OPTIONAL_SET
    instances_blueprint = ServiceBlueprint(INSTANCES_BLUEPRINT,
                                           {"list_var": ["foo"],
                                            "other_var": ["bar"],
                                            "optional_var": ["baz"],
                                            "unrecognized_var": ["bop"]})
    with pytest.raises(BlueprintException,
                       message="Expected unrecognized value exception"):
        instances_blueprint.runtime_scripts()
    instances_blueprint = ServiceBlueprint(INSTANCES_BLUEPRINT, {})
    with pytest.raises(BlueprintException,
                       message="Expected missing value exception"):
        instances_blueprint.runtime_scripts()
    instances_blueprint = ServiceBlueprint(NOVARS_BLUEPRINT, {})
    instances_blueprint.runtime_scripts()
