import ipaddress
from butter.util.subnet_generator import generate_subnets


def test_generate_subnets():
    subnets = generate_subnets("10.0.0.0/8",
                               ["10.0.0.0/9", "10.128.0.0/10"], 10)
    assert list(subnets) == [ipaddress.ip_network(u"10.192.0.0/10")]
