"""
Backend Providers

Each directory in this directory should be a single supported backend provider.
"""

from butter.providers import aws, aws_mock, gce

PROVIDERS_MAP = {
    "aws": aws,
    "mock-aws": aws_mock,
    "gce": gce
    }


def get_provider(provider):
    """
    Given a provider string, returns the provider module object.
    """
    if provider in PROVIDERS_MAP:
        return PROVIDERS_MAP[provider]
    raise NotImplementedError("Provider %s not implemented" % provider)
