"""
Functions to convert from a network graph to a list of route tables, and
potentially back if possible.
"""

from itertools import tee


def net_to_routes(net):
    routes = {}

    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)

    for path in net:
        assert len(path) > 1
        src = path[0]
        dest = path[-1]
        for first, second in pairwise(path):
            if first not in routes:
                routes[first] = []
            if second not in routes:
                routes[second] = []
            routes[first].append({
                "destination": dest,
                "target": second
                })
            routes[second].append({
                "destination": src,
                "target": first
                })
        del routes["external"]
    return routes


def routes_to_net(routes):
    """
    TODO: I can't really tell the difference between to/from routes...
    """
    net = []
    # XXX: I don't know if this is the right thing...  It only tells us the
    # ultimate targets.  Although I think that might be what we want.  Does
    # this work with multiple routes?
    endpoints = set()
    for _, route in routes.items():
        for rule in route:
            endpoints.add(rule["destination"])
        endpoints.remove("external")
    for endpoint in endpoints:
        def build_path(start, end, routes):
            if start in routes:
                for rule in routes[start]:
                    if rule["destination"] == end:
                        return [start] + build_path(rule["target"],
                                                    end, routes)
            return [start]
        # TODO: This external is hard coded.  I should do something better to
        # find all paths that are contained in these route tables.  Can I do
        # that?  Is it possible?  Yeah, it should be, but yeah I have the
        # duplicate routes problem (back routes, specifically).  I think I
        # might need to know which things aren't in the route table because
        # they're external versus which things are not there because they're
        # actually missing.
        net.append(build_path(endpoint, "external", routes))
    return net
