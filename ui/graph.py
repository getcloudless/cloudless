#!/usr/bin/env python

import os
import sys
import cloudless

def print_graph(provider):
    """
    Print a graph of all services for provider.
    """
    if provider == "aws":
        client = cloudless.Client("aws", {})
    elif provider == "gce":
        client = cloudless.Client("gce", {
            "user_id": os.environ['CLOUDLESS_GCE_USER_ID'],
            "key": os.environ['CLOUDLESS_GCE_CREDENTIALS_PATH'],
            "project": os.environ['CLOUDLESS_GCE_PROJECT_NAME']})
    else:
        raise NotImplementedError("Provider %s not supported" % provider)
    print(client.graph())
print_graph(sys.argv[1])
