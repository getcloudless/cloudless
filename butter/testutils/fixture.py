"""
Base fixture class used for testing modules.  Users should inherit from this.
"""
import attr

# pylint: disable=too-few-public-methods
@attr.s
class SetupInfo:
    """
    Class that represents what should be returned from setup for everything to
    work.
    """
    deployment_info = attr.ib(type=dict)
    blueprint_vars = attr.ib(type=dict)

class BlueprintTestInterface:
    """
    Parent class for a blueprint test.  This is imported by the butter test
    runner, and the test runner will expect certain methods to be implemented.

    You should inherit from this class, name your class "BlueprintTest", and
    make it importable from the root of your blueprint directory.

    The teardown is handled automatically by the test runner.
    """
    def __init__(self, client):
        """
        A butter client object.  Use this to do all the setup and
        initialization.  You should override this if you need to do any other
        state.
        """
        self.client = client

    def setup(self, network_name):
        """
        Do any necessary initialization before the service using the blueprint
        can be created.  Create all services in the given network.

        Must return a SetupInfo object described above.
        """
        raise NotImplementedError("setup must be implemented in test fixture")

    def verify(self, network_name, service_name, setup_info):
        """
        Called after the service using the blueprint is created.  Do any final
        setup and then any verification to check that the service is behaving as
        expected.  Throw any exception if an error is encountered.

        This will be called with the same object that was returned from setup as
        the third argument, so that this class does not have to store any state.
        """
        raise NotImplementedError("verify must be implemented in test fixture")
