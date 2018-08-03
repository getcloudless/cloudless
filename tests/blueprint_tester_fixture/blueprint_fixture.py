"""
HAProxy Test Fixture

This fixture creates a single service that will run behind HAProxy, and passes
those IP addresses back to the test runner so the test runner can pass them to
the HAProxy blueprint.
"""
import os
from butter.testutils.blueprint_tester import generate_unique_name
from butter.testutils.fixture import BlueprintTestInterface, SetupInfo

SERVICE_BLUEPRINT = os.path.join(os.path.dirname(__file__),
                                 "../../example-blueprints/aws-nginx/blueprint.yml")

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)
SERVICE_NAME = generate_unique_name("service")

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup_before_tested_service(self, network_name):
        """
        Create the dependent services needed to test this service.
        """
        self.client.instances.create(network_name, SERVICE_NAME,
                                     SERVICE_BLUEPRINT)
        instances = self.client.instances.discover(network_name, SERVICE_NAME)
        return SetupInfo(
            {"service_name": SERVICE_NAME},
            {"PrivateIps": [i["PrivateIp"] for i in instances["Instances"]]})

    def setup_after_tested_service(self, network_name, service_name,
                                   setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
        assert setup_info.deployment_info["service_name"] == SERVICE_NAME
        internal_service_name = setup_info.deployment_info["service_name"]
        self.client.paths.add(network_name, service_name, internal_service_name,
                              80)
        self.client.paths.expose(network_name, service_name, 80)

    def verify(self, network_name, service_name, setup_info):
        """
        Given the network name and the service name of the service under test,
        verify that it's behaving as expected.
        """
        assert setup_info.deployment_info["service_name"] == SERVICE_NAME
        assert self.client.instances.discover(network_name, service_name)
        assert self.client.instances.discover(network_name, SERVICE_NAME)
