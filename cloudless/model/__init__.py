"""
Model Utilities

This file should contain things to help drivers for each provider implement the "resource loading"
where they can specify what functions should be called for each model operation.
"""

import json
from jsonschema import validate
import cattr
import attr
import boto3
from moto import mock_ec2
from cloudless.util.exceptions import BadConfigurationException

@attr.s
class Resource:
    """
    Base class for a resource object.
    """
    @classmethod
    def fromdict(cls, resource_dict):
        """Create a new instance of this resource from a dictionary representation."""
        # This is a gross hack to get this working for now...  I want each instance of a Resource
        # object to include a "schema" member, and so I attach it to the class and reference it
        # here.  I could probably just have the init do it, but then the subclasses have to remember
        # to call super.
        # pylint: disable=no-member
        validate(instance=resource_dict, schema=cls.schema)
        return cattr.structure(resource_dict, cls)

    @classmethod
    def fromjson(cls, resource_json):
        """Create a new instance of this resource from a json representation."""
        return cls.fromdict(json.loads(resource_json))

class ResourceDriver():
    """
    Base class for a resource driver.

    Each resource that a model implements should have a driver that can do these things.
    """
    def __init__(self, provider, credentials):
        self.provider = provider
        self.credentials = credentials

    def create(self, resource_definition):
        """
        Create the resource this driver is implementing using the given resource definition.  Fails
        if the resource would be conflicting somehow or already exist.
        """
        raise NotImplementedError("Create not implemented for %s" % self.__class__.__name__)

    def apply(self, resource_definition):
        """
        Make sure some resource that matches the given resource definition exists.  It will try to
        go based on uniquely identifiable things.  If it can't uniquely identify a resource it
        should fail and not change anything, otherwise modify that resource to match the given
        definition.
        """
        raise NotImplementedError("Apply not implemented for %s" % self.__class__.__name__)

    def delete(self, resource_definition):
        """
        Use resource definition to find a resource and delete it.  It will try to go based on
        uniquely identifiable things.  If it can't uniquely identify a resource it should fail and
        not change anything.
        """
        raise NotImplementedError("Delete not implemented for %s" % self.__class__.__name__)

    def get(self, resource_definition):
        """
        Use resource definition to find any matching resources and return them.
        """
        raise NotImplementedError("Get not implemented for %s" % self.__class__.__name__)

    def flags(self, resource_definition):
        """
        Return any flags that specify underlying provider specific behaviour that the user might
        care about.
        """
        raise NotImplementedError("Flags not implemented for %s" % self.__class__.__name__)


class Model():
    """
    The entry point to a provider.  Each provider should return a model object that has that
    provider's information inside.
    """
    RESOURCE_TYPES = {}
    RESOURCE_SCHEMAS = {}

    def __init__(self):
        pass

    def register(self, resource_type, schema_path, resource_driver):
        """
        Register a given resource type with the given file and driver.

        Examples:
            register("VirtualMachine", "cloudless-core-model/models/virtual-machine.json",
                vm_driver)
            register("PrivateNetwork", "cloudless-core-model/models/private-network.json",
                pn_driver)
        """
        with open(schema_path) as model_raw:
            model = json.loads(model_raw.read())
        if resource_type != model["title"]:
            raise BadConfigurationException(
                "Expected resource type %s does not match type in config %s" % (resource_type,
                                                                                schema_path))
        self.RESOURCE_TYPES[model["title"]] = resource_driver
        self.RESOURCE_SCHEMAS[model["title"]] = model

    def _check_resource_registered(self, resource_type):
        """
        Check if we have a handler registered for resource_type.
        """
        if resource_type not in self.RESOURCE_TYPES:
            raise NotImplementedError("No handler found for resource %s!" % resource_type)

    def resources(self):
        """
        Return the list of resources currently registered with this model.
        """
        return self.RESOURCE_TYPES.keys()

    def create(self, resource_type, resource_definition, plan=False):
        """
        Create the given resource type using the registered resource driver.
        """
        self._check_resource_registered(resource_type)
        if plan:
            raise NotImplementedError("plan not implemented!")
        return self.RESOURCE_TYPES[resource_type].create(resource_definition)

    def apply(self, resource_type, resource_definition, plan=False):
        """
        Apply the given resource type using the registered resource driver.
        """
        self._check_resource_registered(resource_type)
        if plan:
            raise NotImplementedError("plan not implemented!")
        return self.RESOURCE_TYPES[resource_type].apply(resource_definition)

    def delete(self, resource_type, resource_definition, plan=False):
        """
        Delete the given resource type using the registered resource driver.
        """
        self._check_resource_registered(resource_type)
        if plan:
            raise NotImplementedError("plan not implemented!")
        return self.RESOURCE_TYPES[resource_type].delete(resource_definition)

    def get(self, resource_type, resource_definition, plan=False):
        """
        Get the given resource type using the registered resource driver.
        """
        self._check_resource_registered(resource_type)
        if plan:
            raise NotImplementedError("plan not implemented!")
        return self.RESOURCE_TYPES[resource_type].get(resource_definition)

    def flags(self, resource_type, resource_definition, plan=False):
        """
        Get provider specific flags for the given resource type using the registered resource
        driver.
        """
        self._check_resource_registered(resource_type)
        if plan:
            raise NotImplementedError("plan not implemented!")
        return self.RESOURCE_TYPES[resource_type].flags(resource_definition)
