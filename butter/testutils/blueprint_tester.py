"""
Test boilerplate for modules.
"""
import os
import time
import sys
import random
import string
import importlib

from butter.testutils.log import logger


SCRIPT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)


def generate_unique_name(base):
    """
    Generates a somewhat unique name given "base".
    """
    random_length = 10
    random_string = ''.join(random.choices(string.ascii_uppercase,
                                           k=random_length))
    return "%s-%s" % (base, random_string)


def blueprint_tester(client, blueprint_dir):
    """
    Test blueprint.
    """
    blueprint = "%s/blueprint.yml" % blueprint_dir
    sys.path.append(blueprint_dir)
    fixture = importlib.import_module("fixture")
    service_name = generate_unique_name("blueprint-tester")
    try:
        # Initialize the fixture
        fixture = fixture.Fixture(client)
        fixture.create()

        # Instantiate the actual instances for this module
        instances = client.instances.create(fixture.get_network(), service_name,
                                            blueprint,
                                            fixture.get_blueprint_vars())
        assert instances["Instances"]

        # Allow fixture to set up firewalls
        fixture.setup_routes(service_name)

        # Verify that the service is behaving as expected
        retries = 0
        while True:
            try:
                fixture.verify(service_name)
                break
            # pylint: disable=broad-except
            except Exception as verify_exception:
                logger.info("Verify exception: %s", verify_exception)
                if retries >= RETRY_COUNT:
                    raise
                retries = retries + 1
                time.sleep(RETRY_DELAY)
    finally:

        # Destroy the service and fixture
        client.instances.destroy(fixture.get_network(), service_name)
        fixture.destroy()
