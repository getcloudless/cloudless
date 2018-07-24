#!/usr/bin/env python

from butter.util.firewall_compiler import FirewallCompiler


def test_firewall_compiler():
    firewall_compiler = FirewallCompiler()
    assert firewall_compiler.generate_rules() == ["0.0.0.0/0"]
