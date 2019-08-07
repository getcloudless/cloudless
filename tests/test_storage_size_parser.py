"""
Test storage size parser.

This was a helper to convert a size string to bytes.
"""
import pytest
from cloudless.util.storage_size_parser import parse_storage_size


def test_storage_size_parser():
    """
    Test that our parser properly converts the given strings to bytes.
    """
    assert parse_storage_size("10 MiB") == 10485760
    assert parse_storage_size("10MB") == 10000000
    with pytest.raises(SyntaxError):
        parse_storage_size("10 GIGAWATTS")
        pytest.fail("Expected sytax error with bad size")
