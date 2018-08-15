"""
Test helper to carve subnets out of a CIDR,
"""
from butter.util.subnet_generator import generate_subnets


def test_generate_subnets():
    """
    Test that we get the right subnets back given parent cidr and existing subnets.
    """
    subnets = generate_subnets("10.0.0.0/8",
                               ["10.0.0.0/9", "10.128.0.0/10"], 10, 1)
    assert list(subnets) == ["10.192.0.0/10"]
