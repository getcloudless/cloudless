#!/usr/bin/env python
"""
This is a class that takes a list of "X should be able to access Y" and turns
that into actual ingress and egress rules.

So what's the algorithm.

For each node N.
Iterate the edges E.

And just generate the ingress/egress rules.

Is there any real work that needs to be done here?

I think a little.  If only to just change the format.
"""

import attr


@attr.s
class FirewallCompiler(object):

    def generate_rules(self):
        return ["0.0.0.0/0"]
