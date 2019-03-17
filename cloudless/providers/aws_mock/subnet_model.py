"""
Cloudless Subnet Model on Mock AWS
"""
from moto import mock_ec2
import cloudless.model

@mock_ec2
class MockSubnetResourceDriver(cloudless.model.ResourceDriver):
    """
    This class is what gets called when the user is trying to interact with a "Subnet" resource.

    By the time it gets called to interact with "Subnet" resources, it should be fully initialized
    and prepared to interact with the backing provider, because that is all configured up front.
    """
    def __init__(self, provider, credentials, model):
        self.provider = provider
        self.credentials = credentials
        self.driver = cloudless.providers.aws.subnet_model.SubnetResourceDriver(provider,
                                                                                credentials,
                                                                                model)
        super(MockSubnetResourceDriver, self).__init__(provider, credentials)

    def create(self, resource_definition):
        return self.driver.create(resource_definition)

    def apply(self, resource_definition):
        return self.driver.apply(resource_definition)

    def delete(self, resource_definition):
        return self.driver.delete(resource_definition)

    def get(self, resource_definition):
        return self.driver.get(resource_definition)

    def flags(self, resource_definition):
        return self.driver.flags(resource_definition)
