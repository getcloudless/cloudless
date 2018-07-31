import pytest
from butter.util.storage_size_parser import parse_storage_size


def test_storage_size_parser():
    assert parse_storage_size("10 MiB") == 10485760
    assert parse_storage_size("10MB") == 10000000
    with pytest.raises(SyntaxError,
                       message="Expected sytax error with bad size"):
        parse_storage_size("10 GIGAWATTS")
