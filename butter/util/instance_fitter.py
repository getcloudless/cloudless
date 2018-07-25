#!/usr/bin/env python

import attr


@attr.s
class InstanceFitter(object):
    """
    Finds the cheapest instance that satisfies the requirements specified in
    the given blueprint.
    """

    # pylint: disable=unused-argument
    def get_fitting_instance(self, provider, blueprint):
        # TODO: Actually get instances based on cloud and based on the sizes
        # passed in the given blueprint.
        if provider == "aws":
            return "t2.micro"
        if provider == "gce":
            return "f1-micro"
        raise NotImplementedError
