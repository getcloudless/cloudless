"""
Types related to networking.
"""
import ipaddress

# pylint: disable=too-few-public-methods
class CidrBlock:
    """
    Simple container to hold a CIDR network block.
    """
    def __init__(self, cidr_block):
        self.cidr_block = ipaddress.IPv4Network(cidr_block)

    # https://stackoverflow.com/questions/1436703/difference-between-str-and-repr#2626364
    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
