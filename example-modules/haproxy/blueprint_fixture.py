"""
Test Fixture Class

Should create whatever dependent resources are necessary to test this module,
and return a dictionary with the names of the dependent resources.

It needs to return the names so it can generate unique names per test.
"""
import os
import requests
from butter.testutils.blueprint_tester import (generate_unique_name,
                                               call_with_retries)
from butter.testutils.fixture import BlueprintTestInterface, SetupInfo

SERVICE_BLUEPRINT = os.path.join(os.path.dirname(__file__),
                                 "internal-service.yml")

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup(self, network_name):
        """
        Create the dependent services needed to test this service.
        """
        service_name = generate_unique_name("service")
        self.client.instances.create(network_name, service_name,
                                     SERVICE_BLUEPRINT)
        instances = self.client.instances.discover(network_name, service_name)
        return SetupInfo(
            {"service_name": service_name},
            {"PrivateIps": [i["PrivateIp"] for i in instances["Instances"]]})

    def verify(self, network_name, service_name, setup_info):
        """
        Given the network name and the service name of the service under test,
        do any last setup and verity that it's behaving as expected.
        """
        # First, set up routing to expose the load balancer and add a path to
        # the internal service.
        internal_service_name = setup_info.deployment_info["service_name"]
        self.client.paths.add(network_name, service_name, internal_service_name,
                              80)
        self.client.paths.expose(network_name, service_name, 80)

        # Now, keep trying until the services is up or we exceed our retries.
        def check_responsive():
            service = self.client.instances.discover(network_name, service_name)
            public_ips = [i["PublicIp"] for i in service["Instances"]]
            assert public_ips
            for public_ip in public_ips:
                response = requests.get("http://%s" % public_ip)
                assert response.content
                assert "Welcome to nginx!" in str(response.content)
        call_with_retries(check_responsive, RETRY_COUNT, RETRY_DELAY)
