import os
from butter.util.instance_fitter import get_fitting_instance


# TODO: Find a way to consolidate these.  The main issue is that the base
# images have different names in different providers.
blueprints_dir = os.path.join(os.path.dirname(__file__), "blueprints")
AWS_SERVICE_BLUEPRINT = os.path.join(blueprints_dir, "service.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(blueprints_dir, "service-ubuntu.yml")


def test_instance_fitter():
    # If no memory, cpu, or storage is passed in, find the cheapest.
    assert get_fitting_instance("aws", AWS_SERVICE_BLUEPRINT) == "t2.nano"
    assert get_fitting_instance("gce", GCE_SERVICE_BLUEPRINT) == "f1-micro"
