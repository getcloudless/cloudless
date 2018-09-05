"""
Cloudless Mock AWS Service
"""
import boto3
from moto import mock_ec2, mock_autoscaling
import cloudless.providers.aws.impl.service

@mock_ec2
@mock_autoscaling
class ServiceClient:
    """
    Cloudless Service Client Object for Mock AWS
    """
    def __init__(self, credentials):
        self.service = cloudless.providers.aws.impl.service.ServiceClient(boto3, credentials,
                                                                          mock=True)

    # pylint: disable=too-many-arguments
    def create(self, network, service_name, blueprint, template_vars, count):
        """
        Create a service in "network" named "service_name" with blueprint file at "blueprint".

        "template_vars" are passed to the initialization scripts as jinja2 variables.

        "count" is the number of instances to create for the service.  Default is one for each
        availability zone.
        """
        return self.service.create(network, service_name, blueprint, template_vars, count)

    def get(self, network, service_name):
        """
        Get a service in "network" named "service_name".
        """
        return self.service.get(network, service_name)

    def destroy(self, service):
        """
        Destroy a service described by the "service" object.
        """
        return self.service.destroy(service)

    def list(self):
        """
        List all services.
        """
        return self.service.list()

    def node_types(self):
        """
        Get mapping of node types to the resources.
        """
        return self.service.node_types()
