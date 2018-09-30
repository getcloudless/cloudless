"""
Apache Test Fixture

This fixture doesn't do any setup, but verifies that the created service is
running default apache.
"""
import requests
from cloudless.testutils.blueprint_tester import call_with_retries
from cloudless.testutils.fixture import BlueprintTestInterface, SetupInfo
from cloudless.types.networking import CidrBlock

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup_before_tested_service(self, network):
        """
        Create the dependent services needed to test this service.
        """
        # Since this service has no dependencies, do nothing.
        return SetupInfo({}, {})

    def setup_after_tested_service(self, network, service, setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
        internet = CidrBlock("0.0.0.0/0")
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
