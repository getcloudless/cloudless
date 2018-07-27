"""
Base fixture class used for testing modules.  Users should inherit from this.
"""

class Fixture:
    """
    Fixture class that creates the dependent resources.
    """
    def __init__(self, client):
        self.client = client

    def create(self):
        """
        Create the dependent services needed to test this service.
        """
        raise NotImplementedError("create must be implemented in test fixture")

    def setup_routes(self, service_name):
        """
        Make sure all the paths are properly setup for the test.
        """
        raise NotImplementedError(
                "setup_routes must be implemented in test fixture")

    def verify(self, service_name):
        """
        Given the name of the service under test, verifies that it's behaving as
        expected.
        """
        raise NotImplementedError("verify must be implemented in test fixture")

    def destroy(self):
        """
        Destroy the dependent services needed to test this service.
        """
        raise NotImplementedError("destroy must be implemented in test fixture")

    def get_network(self):
        """
        Get the network this fixture is or will be deployed in.
        """
        raise NotImplementedError(
                "get_network must be implemented in test fixture")

    def get_blueprint_vars(self):
        """
        Get the variables that should be passed to the blueprint under test.
        """
        raise NotImplementedError(
                "get_blueprint_vars must be implemented in test fixture")
