"""
Functions to convert from a network graph to a list of firewall rules, and
potentially back if possible.
"""


def net_to_firewalls(net):
    """
    TODO: Really figure out this format.  Perhaps my sources and targets can be
    comma separated ids or something, to make it easier to build this for
    multiple subnets.  That actually makes peered subnets reasonably
    straightforward, since I can reference the same list.
    """
    firewalls = {}
    for source, targets in net.items():
        if source not in firewalls and source != "external":
            firewalls[source] = []
        for target, configs in targets.items():
            if target not in firewalls and target != "external":
                firewalls[target] = []
            ingress_rules = [{
                "source": source,
                "protocol": config["protocol"],
                "port": config["port"],
                "type": "ingress"
                } for config in configs]
            egress_rules = [{
                "source": target,
                "protocol": config["protocol"],
                "port": config["port"],
                "type": "egress"
                } for config in configs]
            if target != "external":
                firewalls[target].extend(ingress_rules)
            if source != "external":
                firewalls[source].extend(egress_rules)
    return firewalls


def firewalls_to_net(firewalls):
    """
    TODO: This isn't fully correct, just a POC to get the test passing.

    What I need:

    - Do ingress and egress properly
    - Figure out what to do when I have conflicting rules
    """
    net = {}
    for source, rules in firewalls.items():
        for rule in rules:
            if rule["type"] == "ingress":
                if rule["source"] not in net:
                    net[rule["source"]] = {}
                if source not in net[rule["source"]]:
                    net[rule["source"]][source] = []
                net[rule["source"]][source].append({
                    "protocol": rule["protocol"],
                    "port": rule["port"]
                    })
    return net
