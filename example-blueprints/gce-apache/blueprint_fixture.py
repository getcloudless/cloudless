"""
Apache Test Fixture

This fixture doesn't do any setup, but verifies that the created service is
running default apache.
"""
import requests
from butter.testutils.blueprint_tester import call_with_retries
from butter.testutils.fixture import BlueprintTestInterface, SetupInfo

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup_before_tested_service(self, network_name):
        """
        Create the dependent services needed to test this service.
        """
        # Since this service has no dependencies, do nothing.
        return SetupInfo({}, {})

    def setup_after_tested_service(self, network_name, service_name,
                                   setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
        self.client.paths.expose(network_name, service_name, 80)

    def verify(self, network_name, service_name, setup_info):
        """
        Given the network name and the service name of the service under test,
        verify that it's behaving as expected.
        """
        def check_responsive():
            service = self.client.instances.discover(network_name, service_name)
            public_ips = [i["PublicIp"] for i in service["Instances"]]
            assert public_ips
            for public_ip in public_ips:
                response = requests.get("http://%s" % public_ip)
                expected_content = "Hello World"
                assert response.content, "No content in response"
                assert expected_content in str(response.content), (
                    "Unexpected content in response: %s" % response.content)

        call_with_retries(check_responsive, RETRY_COUNT, RETRY_DELAY)
