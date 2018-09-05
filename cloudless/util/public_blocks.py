"""
Utility to get list of public CIDRs.
"""
import ipaddress

def get_public_blocks():
    """
    Get public cidrs.
    """
    def address_exclude_list(original, exclude):
        full_network_list = []
        if not exclude:
            return [original]
        if original.overlaps(exclude[0]):
            for new_block in original.address_exclude(exclude[0]):
                full_network_list.extend(address_exclude_list(new_block, exclude[1:]))
        else:
            full_network_list.extend(address_exclude_list(original, exclude[1:]))
        return full_network_list
    return address_exclude_list(
        ipaddress.IPv4Network("0.0.0.0/0"),
        [ipaddress.IPv4Network("10.0.0.0/8"), ipaddress.IPv4Network("127.0.0.0/8"),
         ipaddress.IPv4Network("172.16.0.0/12"), ipaddress.IPv4Network("192.168.0.0/16")])
