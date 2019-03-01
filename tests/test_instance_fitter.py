"""
Test instance fitter.
"""
import pytest
import cloudless
from cloudless.util.instance_fitter import get_fitting_instance
from cloudless.util.blueprint import ServiceBlueprint

LARGE_INSTANCE_BLUEPRINT = """
---
network:
  subnetwork_max_instance_count: 768

placement:
  availability_zones: 3

instance:
  public_ip: True
  memory: 16GB
  cpus: 4
  gpu: false
  disks:
    - size: 8GB
      type: standard
      device_name: /dev/sda1

image:
  name: "N/A - only to test instance fitter"

initialization:
  - path: "N/A - only to test instance fitter"
"""

SMALL_INSTANCE_BLUEPRINT = """
---
network:
  subnetwork_max_instance_count: 768

placement:
  availability_zones: 3

instance:
  public_ip: True
  memory: 2GB
  cpus: 1
  gpu: false
  disks:
    - size: 8GB
      type: standard
      device_name: /dev/sda1

image:
  name: "N/A - only to test instance fitter"

initialization:
  - path: "N/A - only to test instance fitter"
"""

def run_instance_fitter_test(profile=None, provider=None, credentials=None):
    """
    Test that we get the proper instance sizes for the given provider.
    """

    # Get the client for this test
    client = cloudless.Client(profile, provider, credentials)

    # If no memory, cpu, or storage is passed in, find the cheapest.
    if client.provider == "aws":
        assert get_fitting_instance(client.service,
                                    ServiceBlueprint(SMALL_INSTANCE_BLUEPRINT)) == "t2.small"
        assert get_fitting_instance(client.service,
                                    ServiceBlueprint(LARGE_INSTANCE_BLUEPRINT)) == "m5.xlarge"
    if client.provider == "gce":
        assert get_fitting_instance(client.service,
                                    ServiceBlueprint(SMALL_INSTANCE_BLUEPRINT)) == "n1-highcpu-4"
        assert get_fitting_instance(client.service,
                                    ServiceBlueprint(LARGE_INSTANCE_BLUEPRINT)) == "n1-highmem-4"

@pytest.mark.aws
def test_instance_fitter_aws():
    """
    Test instance fitter with AWS and global configuration.
    """
    run_instance_fitter_test(profile="aws-cloudless-test")

@pytest.mark.gce
def test_instance_fitter_gce():
    """
    Test instance fitter with GCE and below environment configuration.
    """
    run_instance_fitter_test(profile="gce-cloudless-test")
