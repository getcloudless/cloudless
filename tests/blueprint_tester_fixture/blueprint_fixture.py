"""
HAProxy Test Fixture

This fixture creates a single service that will run behind HAProxy, and passes
those IP addresses back to the test runner so the test runner can pass them to
the HAProxy blueprint.
"""
import os
from butter.testutils.blueprint_tester import generate_unique_name
from butter.testutils.fixture import BlueprintTestInterface, SetupInfo
from butter.types.networking import CidrBlock

SERVICE_BLUEPRINT = os.path.join(os.path.dirname(__file__),
                                 "../../example-blueprints/aws-nginx/blueprint.yml")

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)
SERVICE_NAME = generate_unique_name("service")

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup_before_tested_service(self, network):
        """
        Create the dependent services needed to test this service.
        """
        service = self.client.service.create(network, SERVICE_NAME, SERVICE_BLUEPRINT)
        return SetupInfo(
            {"service_name": SERVICE_NAME},
            {"PrivateIps": [i.private_ip for s in service.subnetworks for i in s.instances]})

    def setup_after_tested_service(self, network, service, setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
        assert setup_info.deployment_info["service_name"] == SERVICE_NAME
        internal_service_name = setup_info.deployment_info["service_name"]
        internal_service = self.client.service.get(network, internal_service_name)
        internet = CidrBlock("0.0.0.0/0")
        self.client.paths.add(service, internal_service, 80)
        self.client.paths.add(internet, service, 80)

    def verify(self, network, service, setup_info):
        """
        Given the network name and the service name of the service under test,
        verify that it's behaving as expected.
        """
        assert setup_info.deployment_info["service_name"] == SERVICE_NAME
        assert self.client.service.get(network, service.name)
        assert self.client.service.get(network, SERVICE_NAME)
