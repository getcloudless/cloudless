#!/usr/bin/env python
"""
This should really just be part of the ipaddress library.

Given a CIDR block, and some existing CIDR blocks, carves out subnets with the
given prefix, but skips subnets that overlap the existing CIDR blocks.
"""

import ipaddress

def generate_subnets(parent_cidr, existing_cidrs, prefix):
    parent_network = ipaddress.ip_network(str(parent_cidr))
    candidate_subnets = parent_network.subnets(new_prefix=prefix)
    for candidate_subnet in candidate_subnets:
        overlap = False
        for existing_cidr in existing_cidrs:
            if ipaddress.ip_network(str(existing_cidr)).overlaps(candidate_subnet):
                overlap = True
        if not overlap:
            yield candidate_subnet
