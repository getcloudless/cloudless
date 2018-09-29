"""
Model Tests
"""
import pytest
import cloudless

@pytest.fixture
def model():
    """
    Pytest fixture to create a mock model.
    """
    network = cloudless.types.common.Network(
        name="test",
        network_id="id-999999",
        cidr_block="10.0.0.0/16",
        region="us-east-1")
    service = cloudless.types.common.Service(
        network=network,
        name="foo",
        subnetworks=[cloudless.types.common.Subnetwork(
            subnetwork_id="id-8888888",
            name="foo",
            cidr_block="10.0.0.0/24",
            region="us-east-1",
            availability_zone="us-east-1a",
            instances=[cloudless.types.common.Instance(
                instance_id="id-777777",
                public_ip="183.23.34.51",
                private_ip="10.0.0.8",
                state="running",
                availability_zone="us-east-1a")])])
    internet = cloudless.types.common.Service(
        network=None,
        name=None,
        subnetworks=[cloudless.types.common.Subnetwork(
            subnetwork_id=None,
            name=None,
            cidr_block="0.0.0.0/0",
            region=None,
            availability_zone=None,
            instances=[])])
    path = cloudless.types.common.Path(
        network=network,
        source=internet,
        destination=service,
        protocol="tcp",
        port=80)
    return cloudless.model.ProjectModel(
        networks=[network],
        services=[service],
        paths=[path])

@pytest.fixture
def base_model_yaml():
    """
    The YAML output for the base model without changes.
    """
    return """- name: test
  id: id-999999
  block: 10.0.0.0/16
  region: us-east-1
  services:
  - name: foo
    has_access_to:
    - default-all-outgoing-allowed
    is_accessible_from:
    - external:0.0.0.0/0:80
    subnetworks:
    - name: foo
      id: id-8888888
      block: 10.0.0.0/24
      region: us-east-1
      availability_zone: us-east-1a
      instances:
      - id: id-777777
        public_ip: 183.23.34.51
        private_ip: 10.0.0.8
        state: running
        availability_zone: us-east-1a
"""

# pylint:disable=redefined-outer-name
@pytest.fixture
def new_add_service_model_yaml(base_model_yaml):
    """
    The YAML output for the base model without changes.
    """
    return base_model_yaml.rstrip() + """
  - name: bar
    has_access_to:
    - default-all-outgoing-allowed
    is_accessible_from: []
    subnetworks:
    - name: bar
      id: id-5555555
      block: 10.0.1.0/24
      region: us-east-1
      availability_zone: us-east-1b
      instances:
      - id: id-4444444
        public_ip: 183.23.34.51
        private_ip: 10.0.1.8
        state: running
        availability_zone: us-east-1b
"""

# pylint:disable=redefined-outer-name
@pytest.fixture
def new_add_network_model_yaml(base_model_yaml):
    """
    The YAML output for the base model without changes.
    """
    return base_model_yaml.rstrip() + """
- name: test2
  id: id-0000000
  block: 10.1.0.0/16
  region: us-west-2
  services: []
"""

# pylint:disable=redefined-outer-name
@pytest.fixture
def add_service_model_yaml(base_model_yaml):
    """
    The YAML output for the base model without changes.
    """
    lines = []
    for line in base_model_yaml.split("\n"):
        lines.append("  %s" % line)
    return "\n".join(lines).rstrip() + """
+   - name: bar
+     has_access_to:
+     - default-all-outgoing-allowed
+     is_accessible_from: []
+     subnetworks:
+     - name: bar
+       id: id-5555555
+       block: 10.0.1.0/24
+       region: us-east-1
+       availability_zone: us-east-1b
+       instances:
+       - id: id-4444444
+         public_ip: 183.23.34.51
+         private_ip: 10.0.1.8
+         state: running
+         availability_zone: us-east-1b
  """

# pylint:disable=redefined-outer-name
@pytest.fixture
def add_network_model_yaml(base_model_yaml):
    """
    The YAML output for the base model without changes.
    """
    lines = []
    for line in base_model_yaml.split("\n"):
        lines.append("  %s" % line)
    return "\n".join(lines).rstrip() + """
+ - name: test2
+   id: id-0000000
+   block: 10.1.0.0/16
+   region: us-west-2
+   services: []
  """

# pylint:disable=redefined-outer-name
def test_add_service_to_model(model, base_model_yaml, new_add_service_model_yaml,
                              add_service_model_yaml):
    """
    Test that model works properly.
    """
    assert len(model.networks) == 1
    assert model.networks[0].name == "test"
    assert model.to_yaml() == base_model_yaml
    network = model.networks[0]
    service = cloudless.types.common.Service(
        network=network,
        name="bar",
        subnetworks=[cloudless.types.common.Subnetwork(
            subnetwork_id="id-5555555",
            name="bar",
            cidr_block="10.0.1.0/24",
            region="us-east-1",
            availability_zone="us-east-1b",
            instances=[cloudless.types.common.Instance(
                instance_id="id-4444444",
                public_ip="183.23.34.51",
                private_ip="10.0.1.8",
                state="running",
                availability_zone="us-east-1b")])])
    model.add_service(service)
    with pytest.raises(cloudless.util.exceptions.DisallowedOperationException,
                       message="Should not be allowed to do another operation"):
        model.add_network(network)
    assert model.to_yaml() == base_model_yaml
    assert model.to_yaml(include_new=True) == new_add_service_model_yaml
    assert model.to_yaml_diff() == add_service_model_yaml

# pylint:disable=redefined-outer-name
def test_add_network_to_model(model, base_model_yaml, new_add_network_model_yaml,
                              add_network_model_yaml):
    """
    Test that adding a network to our model works properly.
    """
    network = cloudless.types.common.Network(
        name="test2",
        network_id="id-0000000",
        cidr_block="10.1.0.0/16",
        region="us-west-2")
    model.add_network(network)
    with pytest.raises(cloudless.util.exceptions.DisallowedOperationException,
                       message="Should not be allowed to do another operation"):
        model.add_service(cloudless.types.common.Service(None, None, None))
    assert model.to_yaml() == base_model_yaml
    assert model.to_yaml(include_new=True) == new_add_network_model_yaml
    assert model.to_yaml_diff() == add_network_model_yaml
