"""
Test boilerplate for modules.
"""
import os
import time
import sys
import random
import string
import json
import importlib

from butter.testutils.log import logger
from butter.testutils.fixture import SetupInfo


SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
NETWORK_BLUEPRINT = os.path.join(SCRIPT_PATH, "network.yml")
TEST_STATE_FILENAME = "state.json"

def call_with_retries(function, retry_count, retry_delay):
    """
    Calls the given function with retries.  Also handles logging on each retry.
    """
    logger.info("Calling function: %s with retry count: %s, retry_delay: %s",
                function, retry_count, retry_delay)
    for retry in range(1, int(retry_count) + 1):
        logger.info("Attempt number: %s", retry)
        try:
            return function()
        # pylint: disable=broad-except
        except Exception as verify_exception:
            logger.info("Verify exception: %s", verify_exception)
            time.sleep(float(retry_delay))
    logger.info("Exceeded max retries!  Reraising last exception")
    # pylint: disable=misplaced-bare-raise
    raise


def generate_unique_name(base):
    """
    Generates a somewhat unique name given "base".
    """
    random_length = 10
    random_string = ''.join(random.choices(string.ascii_uppercase,
                                           k=random_length))
    return "%s-%s" % (base, random_string)

def get_blueprint_tester(client, blueprint_dir):
    """
    Import the test boilerplate from the blueprint directory.
    """
    sys.path.append(blueprint_dir)
    fixture = importlib.import_module("blueprint_fixture")
    return fixture.BlueprintTest(client)

def get_blueprint(blueprint_dir):
    """
    Given a blueprint dir, return the blueprint under test.
    """
    return "%s/blueprint.yml" % blueprint_dir

def save_state(state, blueprint_dir):
    """
    Save test state so we can run each command independently.
    """
    state_file_path = "%s/%s" % (blueprint_dir, TEST_STATE_FILENAME)
    state_json = json.dumps(state, indent=2, sort_keys=True)
    with open(state_file_path, "w") as state_file:
        state_file.write(state_json)

def get_state(blueprint_dir):
    """
    Get test state so we can run each command independently.
    """
    state_file_path = "%s/%s" % (blueprint_dir, TEST_STATE_FILENAME)
    with open(state_file_path, "r") as state_file:
        return json.loads(state_file.read())

def setup(client, blueprint_dir):
    """
    Create all the boilerplate to spin up the service, and the service itself.
    """
    logger.info("Running setup to test: %s", blueprint_dir)
    # Save the state now in case something fails
    network_name = generate_unique_name("blueprint-tester")
    service_name = generate_unique_name("blueprint-tester")
    save_state({"network_name": network_name, "service_name": service_name},
               blueprint_dir)

    # Create the test network
    client.network.create(network_name, NETWORK_BLUEPRINT)

    # Setup the custom environment
    blueprint_tester = get_blueprint_tester(client, blueprint_dir)
    setup_info = blueprint_tester.setup(network_name)
    assert isinstance(setup_info, SetupInfo)

    # Instantiate the actual instances for this module
    blueprint = get_blueprint(blueprint_dir)
    instances = client.instances.create(network_name, service_name, blueprint,
                                        setup_info.blueprint_vars)
    assert instances["Instances"]
    save_state({"network_name": network_name,
                "service_name": service_name,
                "setup_info": {
                    "deployment_info": setup_info.deployment_info,
                    "blueprint_vars": setup_info.blueprint_vars,
                    }},
               blueprint_dir)

def verify(client, blueprint_dir):
    """
    Verify that the instances are behaving as expected.
    """
    logger.info("Running verify on: %s", blueprint_dir)
    state = get_state(blueprint_dir)
    blueprint_tester = get_blueprint_tester(client, blueprint_dir)
    setup_info = SetupInfo(state["setup_info"]["deployment_info"],
                           state["setup_info"]["blueprint_vars"])
    blueprint_tester.verify(state["network_name"], state["service_name"],
                            setup_info)
    logger.info("Verify successful!")

def teardown(client, blueprint_dir):
    """
    Destroy all services in this network, and destroy the network.
    """
    logger.info("Running teardown on: %s", blueprint_dir)
    state = get_state(blueprint_dir)
    all_instances = client.instances.list()
    for instance_group in all_instances:
        if instance_group["Network"] == state["network_name"]:
            client.instances.destroy(state["network_name"], instance_group["Id"])
    client.network.destroy(state["network_name"])

def run_all(client, blueprint_dir):
    """
    Test blueprint.
    """
    tests_passed = False
    try:
        setup(client, blueprint_dir)
        verify(client, blueprint_dir)
        tests_passed = True
    finally:
        teardown(client, blueprint_dir)
    if tests_passed:
        logger.info("All tests passed!")
