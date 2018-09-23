"""
The AWS provider will provision resources using Amazon Web Services.

You should not use this directly, but instead pass in the string "aws" as the "provider" in the top
level `cloudless.Client` object.
"""
from cloudless.providers.aws import (network, service, paths, image)
