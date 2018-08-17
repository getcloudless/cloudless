"""
HAProxy Test Fixture

This fixture creates a single service that will run behind HAProxy, and passes
those IP addresses back to the test runner so the test runner can pass them to
the HAProxy blueprint.
"""
import os
import requests
from butter.testutils.blueprint_tester import (generate_unique_name,
                                               call_with_retries)
from butter.testutils.fixture import BlueprintTestInterface, SetupInfo
from butter.types.networking import Service, CidrBlock

SERVICE_BLUEPRINT = os.path.join(os.path.dirname(__file__),
                                 "../aws-nginx/blueprint.yml")

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
        service_name = generate_unique_name("service")
        self.client.instances.create(network_name, service_name,
                                     SERVICE_BLUEPRINT)
        instances = self.client.instances.discover(network_name, service_name)
        return SetupInfo(
            {"service_name": service_name},
            {"PrivateIps": [i["PrivateIp"] for i in instances["Instances"]]})

    def setup_after_tested_service(self, network_name, service_name,
                                   setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
        internal_service_name = setup_info.deployment_info["service_name"]
        internal_service = Service(network_name, internal_service_name)
        load_balancer = Service(network_name, service_name)
        internet = CidrBlock("0.0.0.0/0")
        self.client.paths.add(load_balancer, internal_service, 80)
        self.client.paths.add(internet, load_balancer, 80)

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
                assert response.content
                assert "Welcome to nginx!" in str(response.content)
        call_with_retries(check_responsive, RETRY_COUNT, RETRY_DELAY)
