"""
Cloudless Service on AWS

This is the AWS implmentation for the service API, a high level interface to manage groups of
instances.
"""
import boto3
import cloudless.providers.aws.impl.service



class ServiceClient:
    """
    Client object to manage instances.
    """

    def __init__(self, credentials):
        self.service = cloudless.providers.aws.impl.service.ServiceClient(boto3, credentials,
                                                                          mock=False)

    # pylint: disable=too-many-arguments
    def create(self, network, service_name, blueprint, template_vars, count):
        """
        Create a service in "network" named "service_name" with blueprint file at "blueprint".

        "template_vars" are passed to the initialization scripts as jinja2 variables.

        "count" is the number of instances to create for the service.  Default is one for each
        availability zone.
        """
        return self.service.create(network, service_name, blueprint, template_vars, count)

    def list(self):
        """
        List all services.
        """
        return self.service.list()

    # pylint: disable=no-self-use
    def get(self, network, service_name):
        """
        Discover a service in "network" named "service_name".
        """
        return self.service.get(network, service_name)

    def destroy(self, service):
        """
        Destroy a group of instances described by "service".
        """
        return self.service.destroy(service)

    def node_types(self):
        """
        Get a list of node sizes to use for matching resource requirements to
        instance type.
        """
        return self.service.node_types()
