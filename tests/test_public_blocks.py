"""
Test library to get public CIDRs.
"""
import ipaddress
import butter.util.public_blocks

def test_public_blocks():
    """
    Test that the logic that tells us whether something is internet accessible is correct.
    """
    public_address_overlap = False
    public_blocks = butter.util.public_blocks.get_public_blocks()
    assert public_blocks
    for block in public_blocks:
        assert not ipaddress.IPv4Network("172.16.0.0/12").overlaps(block)
        assert not ipaddress.IPv4Network("10.0.0.0/8").overlaps(block)
        assert not ipaddress.IPv4Network("127.0.0.0/8").overlaps(block)
        assert not ipaddress.IPv4Network("192.168.0.0/16").overlaps(block)
        assert ipaddress.IPv4Network("0.0.0.0/0").overlaps(block)
        if ipaddress.IPv4Network("8.8.8.8/32").overlaps(block):
            public_address_overlap = True
    assert public_address_overlap
