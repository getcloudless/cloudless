"""
The GCE Provider will provision resources using Google Compute Engine.

You should not use this directly, but instead pass in the string "gce" as the "provider" in the top
level `cloudless.Client` object.
"""
from cloudless.providers.gce import (network, service, paths, image)
