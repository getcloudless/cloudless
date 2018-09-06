"""
Mock AWS Provider

This module uses AWS as a backing provider with moto instead of boto3 so that no resources get
deployed.
"""
from cloudless.providers.aws_mock import (network, service, paths)
