from butter.util import netgraph

net = {
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

firewalls = {
        "0": [{
            "source": "1",
            "protocol": "tcp",
            "port": "443",
            "type": "egress"
            }],
        "1": [{
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
    assert firewalls == netgraph.net_to_firewalls(net)


def test_firewalls_to_net():
    assert net == netgraph.firewalls_to_net(firewalls)
