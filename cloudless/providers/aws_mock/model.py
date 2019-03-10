"""
Cloudless Model on Mock AWS
"""
import os
import cloudless.model
from cloudless.providers.aws_mock import firewall, network_model

def get_model(credentials):
    """
    Create model object and register all available resource drivers.
    """
    model = cloudless.model.Model()
    models_dir = "%s/../../cloudless-core-model/models" % os.path.dirname(
        os.path.realpath(__file__))
    model.register("Firewall",
                   "%s/firewall.json" % models_dir,
                   firewall.MockFirewallResourceDriver("mock_aws", credentials))
    model.register("Network",
                   "%s/network.json" % models_dir,
                   network_model.MockNetworkResourceDriver("mock_aws", credentials))
    return model
