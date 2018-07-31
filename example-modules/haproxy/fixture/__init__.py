"""
Test Fixture Class

Should create whatever dependent resources are necessary to test this module,
and return a dictionary with the names of the dependent resources.

It needs to return the names so it can generate unique names per test.
"""
import os
import random
import string
import pytest
import requests
from butter.testutils.blueprint_tester import generate_unique_name
from butter.testutils.fixture import Fixture

BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "blueprints")
NETWORK_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "network.yml")
SERVICE_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "service.yml")


class Fixture(Fixture):
    """
    Fixture class that creates the dependent resources.
    """
    def __init__(self, client):
        self.client = client
        self.info = {}
        self.network_name = generate_unique_name("fixture")
        self.service_name = generate_unique_name("service")

    def create(self):
        """
        Create the dependent services needed to test this service.
        """
        self.client.network.create(self.network_name, NETWORK_BLUEPRINT)
        self.client.instances.create(self.network_name, self.service_name,
                                     SERVICE_BLUEPRINT)
        self.info = {"network": self.network_name, "service": self.service_name}

    def setup_routes(self, service_name):
        """
        Make sure all the paths are properly setup for the test.
        """
        self.client.paths.add(self.network_name, service_name,
                              self.service_name, 80)
        self.client.paths.expose(self.network_name, service_name, 80)

    def verify(self, service_name):
        """
        Given the name of the service under test, verifies that it's behaving as
        expected.
        """
        service = self.client.instances.discover(self.network_name,
                                                 service_name)
        public_ips = [i["PublicIp"] for i in service["Instances"]]
        assert public_ips
        for public_ip in public_ips:
            response = requests.get("http://%s" % public_ip)
            assert response.content
            assert "Welcome to nginx!" in str(response.content)

    def destroy(self):
        """
        Destroy the dependent services needed to test this service.
        """
        self.client.instances.destroy(self.network_name, self.service_name)
        self.client.network.destroy(self.network_name)
        self.info = {}

    def get_network(self):
        """
        Get the network this fixture is or will be deployed in.
        """
        return self.network_name

    def get_blueprint_vars(self):
        """
        Get the variables that should be passed to the blueprint under test.
        """
        instances = self.client.instances.discover(self.network_name,
                                                   self.service_name)
        return {
            "PrivateIps": [i["PrivateIp"] for i in instances["Instances"]]
            }
