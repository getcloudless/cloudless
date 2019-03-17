"""
Cloudless Model on AWS
"""
import os
import cloudless.model
from cloudless.providers.aws import firewall, network_model, image_model, subnet_model

def get_model(credentials):
    """
    Create model object and register all available resource drivers.
    """
    model = cloudless.model.Model()
    models_dir = "%s/../../cloudless-core-model/models" % os.path.dirname(
        os.path.realpath(__file__))
    model.register("Firewall",
                   "%s/firewall.json" % models_dir,
                   firewall.FirewallResourceDriver("aws", credentials))
    model.register("Network",
                   "%s/network.json" % models_dir,
                   network_model.NetworkResourceDriver("aws", credentials))
    model.register("Image",
                   "%s/image.json" % models_dir,
                   image_model.ImageResourceDriver("aws", credentials))
    model.register("Subnet",
                   "%s/subnet.json" % models_dir,
                   subnet_model.SubnetResourceDriver("aws", credentials, model))
    return model
