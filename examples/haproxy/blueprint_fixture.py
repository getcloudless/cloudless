"""
HAProxy Test Fixture

This fixture creates a single service that will run behind HAProxy, and passes
those IP addresses back to the test runner so the test runner can pass them to
the HAProxy blueprint.
"""
import os
import requests
from cloudless.testutils.blueprint_tester import (generate_unique_name,
                                                  call_with_retries)
from cloudless.testutils.fixture import BlueprintTestInterface, SetupInfo
from cloudless.types.networking import CidrBlock

SERVICE_BLUEPRINT = os.path.join(os.path.dirname(__file__),
                                 "../apache/blueprint.yml")

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(10)

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup_before_tested_service(self, network):
        """
        Create the dependent services needed to test this service.
        """
        service_name = generate_unique_name("service")
        service = self.client.service.create(network, service_name, SERVICE_BLUEPRINT, count=1)
        return SetupInfo(
            {"service_name": service_name},
            {"PrivateIps": [i.private_ip for s in service.subnetworks for i in s.instances]})

    def setup_after_tested_service(self, network, service, setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
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
        def check_responsive():
            public_ips = [i.public_ip for s in service.subnetworks for i in s.instances]
            assert public_ips
            for public_ip in public_ips:
                response = requests.get("http://%s" % public_ip)
                expected_content = "Hello World"
                assert response.content, "No content in response"
                assert expected_content in str(response.content), (
                    "Unexpected content in response: %s" % response.content)

        call_with_retries(check_responsive, RETRY_COUNT, RETRY_DELAY)
