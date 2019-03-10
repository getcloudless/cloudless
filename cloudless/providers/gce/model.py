"""
Cloudless Model on GCE
"""
import os
import cloudless.model
from cloudless.providers.gce import firewall

def get_model(credentials):
    """
    Create model object and register all available resource drivers.
    """
    model = cloudless.model.Model()
    models_dir = "%s/../../cloudless-core-model/models" % os.path.dirname(
        os.path.realpath(__file__))
    model.register("Firewall",
                   "%s/firewall.json" % models_dir,
                   firewall.FirewallResourceDriver("gce", credentials))
    return model
