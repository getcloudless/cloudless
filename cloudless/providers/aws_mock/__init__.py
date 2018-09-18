"""
The Mock AWS provider will provision resources using a library called `moto`, which is a mock client
for Amazon Web Services.  This means that no resources will get provisioned, but cloudless will see
what you create for the duration of your session.

You should not use this directly, but instead pass in the string "mock-aws" as the "provider" in the
top level `cloudless.Client` object.
"""
from cloudless.providers.aws_mock import (network, service, paths, image)
