#!/usr/bin/env python2.7

# ##################
# Main Test Script
# ##################
#
# This module imports the other test modules and builds a complete suite
# from the individual modules.
#
# ::

"""Caravel test script."""
from __future__ import print_function
import unittest
import sys

import test.test_feed_load
import test.test_ftp_acquire
import test.test_gts_load
import test.test_mapping_load
import test.test_report
import test.test_report_CRUD
import test.test_statistics
import test.test_status_load
import test.test_transit_system


# Construction of an overall suite built from individual test modules.
#
# ::

def suite():
    s= unittest.TestSuite()
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_feed_load) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_ftp_acquire) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_gts_load) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_mapping_load) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_report) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_report_CRUD) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_statistics) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_status_load) )
    s.addTests( unittest.defaultTestLoader.loadTestsFromModule(test.test_transit_system) )
    return s

if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
