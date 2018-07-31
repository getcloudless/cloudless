#!/usr/bin/env python

import butter
import butter.testutils.blueprint_tester
aws = butter.Client("aws", {})
print("""
 *************************
 * Testing Blueprint! *
 *************************
 """)
butter.testutils.blueprint_tester.blueprint_tester(aws, ".")
print("""
 *********************
 * All Tests Passed! *
 *********************
 """)
