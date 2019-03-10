"""
Cloudless Firewall Model on GCE
"""
import cloudless.model

class FirewallResourceDriver(cloudless.model.ResourceDriver):
    """
    This class is what gets called when the user is trying to interact with a "Firewall" resource.

    By the time it gets called to interact with "Firewall" resources, it should be fully initialized
    and prepared to interact with the backing provider, because that is all configured up front.
    """
    def __init__(self, provider, credentials):
        self.provider = provider
        self.credentials = credentials
        super(FirewallResourceDriver, self).__init__(provider, credentials)
        # Here for now to get tests passing...
        self.dummy_state = []

    def create(self, resource_definition):
        self.dummy_state.append(resource_definition)
        return resource_definition

    def apply(self, resource_definition):
        return self.dummy_state[0]

    def delete(self, resource_definition):
        self.dummy_state.pop()

    def get(self, resource_definition):
        return self.dummy_state

    def flags(self, resource_definition):
        return []
