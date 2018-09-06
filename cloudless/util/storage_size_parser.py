"""
Utility to parse strings with storage specifiers, like "GB", "MiB", etc. into an
integer number of bytes.
"""
import re

STORAGE_UNITS = {
    "B": 1,
    "KB": 10**3,
    "KiB": 2**10,
    "MB": 10**6,
    "MiB": 2**20,
    "GB": 10**9,
    "GiB": 2**30,
    "TB": 10**12,
    "TiB": 2**40
    }

def parse_storage_size(size):
    """
    Given a storage size string, e.g. "8 GiB", returns an integer number of
    bytes.
    """
    match = re.match(r"(\d+(?:\.\d+)?)\s*(B|KB|KiB|MB|MiB|GB|GiB|TB|TiB)", size)
    if not match:
        raise SyntaxError("Storage size string: \"%s\" is invalid." % size)
    number = match.group(1)
    unit = match.group(2)
    return int(float(number)*STORAGE_UNITS[unit])
