#!/usr/bin/env python

import butter
aws = butter.Client("aws", {})
print(aws.paths.graph())
