"""
Test instance fitter.
"""
import os
import pytest
import butter
from butter.util.instance_fitter import get_fitting_instance


BLUEPRINTS_DIR = os.path.join(os.path.dirname(__file__), "instance_fitter_blueprints")
SMALL_INSTANCE_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "instance-fitter-small.yml")
LARGE_INSTANCE_BLUEPRINT = os.path.join(BLUEPRINTS_DIR, "instance-fitter-large.yml")


def run_instance_fitter_test(provider, credentials):
    """
    Test that we get the proper instance sizes for the given provider.
    """

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # If no memory, cpu, or storage is passed in, find the cheapest.
    if provider == "aws":
        assert get_fitting_instance(client.instances, SMALL_INSTANCE_BLUEPRINT) == "t2.small"
        assert get_fitting_instance(client.instances, LARGE_INSTANCE_BLUEPRINT) == "m4.xlarge"
    if provider == "gce":
        assert get_fitting_instance(client.instances, SMALL_INSTANCE_BLUEPRINT) == "n1-highcpu-4"
        assert get_fitting_instance(client.instances, LARGE_INSTANCE_BLUEPRINT) == "n1-highmem-4"

@pytest.mark.aws
def test_instance_fitter_aws():
    """
    Test instance fitter with AWS and global configuration.
    """
    run_instance_fitter_test(provider="aws", credentials={})

@pytest.mark.gce
def test_instance_fitter_gce():
    """
    Test instance fitter with GCE and below environment configuration.
    """
    run_instance_fitter_test(provider="gce", credentials={
        "user_id": os.environ['BUTTER_GCE_USER_ID'],
        "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
        "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
