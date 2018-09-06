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

from cloudless.testutils.log import logger
from cloudless.testutils.fixture import SetupInfo
from cloudless.util.exceptions import DisallowedOperationException


SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
NETWORK_BLUEPRINT = os.path.join(SCRIPT_PATH, "network.yml")
TEST_STATE_FILENAME = "blueprint-test-state.json"

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
            if retry > int(retry_count):
                logger.info("Exceeded max retries!  Reraising last exception")
                raise
    assert False, "Should never get here."


def generate_unique_name(base):
    """
    Generates a somewhat unique name given "base".
    """
    random_length = 10
    random_string = ''.join(random.choices(string.ascii_lowercase,
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
    if not os.path.exists(state_file_path):
        return {}
    with open(state_file_path, "r") as state_file:
        return json.loads(state_file.read())

def setup(client, blueprint_dir):
    """
    Create all the boilerplate to spin up the service, and the service itself.
    """
    logger.info("Running setup to test: %s", blueprint_dir)
    state = get_state(blueprint_dir)
    if state:
        raise DisallowedOperationException(
            "Found non empty state file: %s" % state)
    network_name = generate_unique_name("test-network")
    service_name = generate_unique_name("test-service")
    state = {"network_name": network_name, "service_name": service_name}
    logger.info("Saving state: %s now in case something fails", state)
    save_state(state, blueprint_dir)

    logger.info("Creating test network: %s", network_name)
    network = client.network.create(network_name, NETWORK_BLUEPRINT)

    logger.info("Calling the pre service setup in test fixture")
    blueprint_tester = get_blueprint_tester(client, blueprint_dir)
    setup_info = blueprint_tester.setup_before_tested_service(network)
    assert isinstance(setup_info, SetupInfo)
    state["setup_info"] = {
        "deployment_info": setup_info.deployment_info,
        "blueprint_vars": setup_info.blueprint_vars,
        }
    logger.info("Saving full state: %s", state)
    save_state(state, blueprint_dir)

    logger.info("Creating services using the blueprint under test")
    blueprint = get_blueprint(blueprint_dir)
    service = client.service.create(network, service_name, blueprint, setup_info.blueprint_vars)
    assert service.subnetworks
    for subnetwork in service.subnetworks:
        assert subnetwork.instances

    logger.info("Calling the post service setup in test fixture")
    blueprint_tester.setup_after_tested_service(network, service, setup_info)

def verify(client, blueprint_dir):
    """
    Verify that the instances are behaving as expected.
    """
    logger.info("Running verify on: %s", blueprint_dir)
    state = get_state(blueprint_dir)
    blueprint_tester = get_blueprint_tester(client, blueprint_dir)
    setup_info = SetupInfo(state["setup_info"]["deployment_info"],
                           state["setup_info"]["blueprint_vars"])
    network = client.network.get(state["network_name"])
    service = client.service.get(network, state["service_name"])
    blueprint_tester.verify(network, service, setup_info)
    logger.info("Verify successful!")

def teardown(client, blueprint_dir):
    """
    Destroy all services in this network, and destroy the network.
    """
    logger.info("Running teardown on: %s", blueprint_dir)
    state = get_state(blueprint_dir)
    if not state or "network_name" not in state:
        return
    all_services = client.service.list()
    for service in all_services:
        if service.network.name == state["network_name"]:
            client.service.destroy(service)
    network = client.network.get(state["network_name"])
    if network:
        client.network.destroy(network)
    save_state({}, blueprint_dir)

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
