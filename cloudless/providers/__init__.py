"""
These providers are what actually provide the resources that cloudless manages.  Changing the
provider should change where things are provisioned, but not change anything about the usage of the
core API.

The currently supported providers are "gce" for Google Compute Engine, "aws" for Amazon Web
Services, and "mock-aws" for Mock Amazon Web Services.

Mock AWS is useful for trying cloudless locally without provisioning any resources.

Example usage:

    import cloudless
    mock_aws = cloudless.client(provider="mock-aws", credentials={})
    mock_aws.network.create(name="example", blueprint="blueprint.yml")
    mock_aws.network.list()

This creates a network named example using the "mock-aws" client.  This doesn't actually create the
network, but cloudless will think it exists for the duration of the session so the
`mock_aws.network.list()` command will show it.
"""

from cloudless.providers import aws, aws_mock, gce

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
