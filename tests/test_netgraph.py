"""
Test conversions between different firewall representations.
"""
from cloudless.util import netgraph

NET = {
    "0": {
        "1": [{
            "protocol": "tcp",
            "port": "443"
            }]
        },
    "external": {
        "1": [{
            "protocol": "tcp",
            "port": "443"
            }]
        }
    }

FIREWALLS = {
    "0": [{
        "source": "1",
        "protocol": "tcp",
        "port": "443",
        "type": "egress"
        }],
    "1": [
        {
            "source": "0",
            "protocol": "tcp",
            "port": "443",
            "type": "ingress"
        },
        {
            "source": "external",
            "protocol": "tcp",
            "port": "443",
            "type": "ingress"
        }]
    }


def test_net_to_firewalls():
    """
    Test conversion from a graph based to a list based format.
    """
    assert FIREWALLS == netgraph.net_to_firewalls(NET)


def test_firewalls_to_net():
    """
    Test conversion from a list based to a graph based format.
    """
    assert NET == netgraph.firewalls_to_net(FIREWALLS)
