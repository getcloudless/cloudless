import os
import pytest
from moto import mock_ec2, mock_autoscaling
import butter

from butter.testutils.blueprint_tester import setup as do_setup
from butter.testutils.blueprint_tester import verify as do_verify
from butter.testutils.blueprint_tester import teardown as do_teardown
from butter.testutils.blueprint_tester import run_all
from butter.testutils.blueprint_tester import get_state

# Get the blueprint locations relative to the test script
BLUEPRINT_DIR = os.path.join(os.path.dirname(__file__), "blueprint_tester_fixture")

def run_blueprint_tester_test(provider, credentials):

    # Get the client for this test
    client = butter.Client(provider, credentials)

    # First make sure we have no state if we teardown
    do_teardown(client, BLUEPRINT_DIR)
    state = get_state(BLUEPRINT_DIR)
    assert not state

    # Then, make sure the full run works
    run_all(client, BLUEPRINT_DIR)

    # Now make sure the state got cleared
    state = get_state(BLUEPRINT_DIR)
    assert not state

    # Now do just the setup and teardown
    do_setup(client, BLUEPRINT_DIR)
    state = get_state(BLUEPRINT_DIR)
    assert state
    assert client.network.discover(state["network_name"])
    assert client.instances.discover(state["network_name"],
                                     state["service_name"])
    assert state["setup_info"]
    do_teardown(client, BLUEPRINT_DIR)
    state = get_state(BLUEPRINT_DIR)
    assert not state

    # Now do setup, multiple verifies and teardown
    do_setup(client, BLUEPRINT_DIR)
    state = get_state(BLUEPRINT_DIR)
    assert state
    assert client.network.discover(state["network_name"])
    assert client.instances.discover(state["network_name"],
                                     state["service_name"])
    assert state["setup_info"]
    do_verify(client, BLUEPRINT_DIR)
    do_verify(client, BLUEPRINT_DIR)
    do_teardown(client, BLUEPRINT_DIR)
    state = get_state(BLUEPRINT_DIR)
    assert not state


@mock_ec2
@mock_autoscaling
@pytest.mark.mock_aws
def test_blueprint_tester_mock():
    run_blueprint_tester_test(provider="aws", credentials={})
