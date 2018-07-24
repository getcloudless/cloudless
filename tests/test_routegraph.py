from butter.util import routegraph

net = [["0", "1", "external"]]

routes = {
        "0": [{
            "destination": "external",
            "target": "1"
            }],
        "1": [{
            "destination": "0",
            "target": "0"
            },
            {
            "destination": "external",
            "target": "external"
            }]
        }


def test_net_to_routes():
    assert routes == routegraph.net_to_routes(net)


def test_routes_to_net():
    assert net == routegraph.routes_to_net(routes)
