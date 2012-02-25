#!/usr/bin/env python2.7
"""Test Caravel Statistics module.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import math
import caravel.statistics

class Test_FQ_Table( unittest.TestCase ):
    def setUp( self ):
        self.table= caravel.statistics.FQTable()
        self.table[3] += 1
        self.table[5] += 1
        self.table[3] += 1
    def test_load( self ):
        self.assertEqual( 2, self.table[3] )
        self.assertEqual( 1, self.table[5] )
        self.assertEqual( 0, self.table[7] )
    def test_mean( self ):
        mean= (3+3+5)/3
        self.assertAlmostEqual( mean, self.table.mean() )
        sd = math.sqrt( ((3-mean)**2 + (3-mean)**2 + (5-mean)**2)/2 )
        self.assertAlmostEqual( sd, self.table.sd() )
        self.assertEqual( 3, self.table.count )
    def test_reset( self ):
        mean= (3+3+5)/3
        self.assertAlmostEqual( mean, self.table.mean() )
        self.assertEqual( 3, self.table.count )
        self.table.reset()
        self.assertIsNone( self.table.count )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
