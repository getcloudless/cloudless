#!/usr/bin/env python

from butter.util.instance_fitter import InstanceFitter


def test_datacenter():
    instance_fitter = InstanceFitter()

    # If no memory, cpu, or storage is passed in, find the cheapest.
    assert instance_fitter.get_fitting_instance("aws", None) == "t2.micro"
    assert instance_fitter.get_fitting_instance("gce", None) == "f1-micro"
