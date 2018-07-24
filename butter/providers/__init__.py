"""
Backend Providers

Each directory in this directory should be a single supported backend provider.
"""

import logging

from butter.providers import aws, gce

logger = logging.getLogger(__name__)

providers_map = {
    "aws": aws,
    "gce": gce
    }


def get_provider(provider):
    if provider in providers_map:
        return providers_map[provider]
    raise NotImplementedError("Provider %s not implemented" % provider)
