import os
import pytest
import butter
from butter.util.instance_fitter import get_fitting_instance


# TODO: Find a way to consolidate these.  The main issue is that the base
# images have different names in different providers.
BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "blueprints")
AWS_SERVICE_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "service.yml")
GCE_SERVICE_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "service-ubuntu.yml")
LARGE_INSTANCE_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "instance-fitter-large.yml")


def run_instance_fitter_test(provider, credentials):

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # If no memory, cpu, or storage is passed in, find the cheapest.
    if provider == "aws":
        assert get_fitting_instance(client.instances, AWS_SERVICE_BLUEPRINT) == "t2.small"
        assert get_fitting_instance(client.instances, LARGE_INSTANCE_BLUEPRINT) == "m4.xlarge"
    if provider == "gce":
        assert get_fitting_instance(client.instances, GCE_SERVICE_BLUEPRINT) == "n1-highcpu-4"
        assert get_fitting_instance(client.instances, LARGE_INSTANCE_BLUEPRINT) == "n1-highmem-4"

@pytest.mark.aws
def test_instance_fitter_aws():
    run_instance_fitter_test(provider="aws", credentials={})

@pytest.mark.gce
def test_instance_fitter_gce():
    run_instance_fitter_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
