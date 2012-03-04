#!/usr/bin/env python2.7
"""Test Caravel transit_system module.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import datetime
import StringIO
import pprint
from caravel.arrival_at_stop import (
    StopFinder, InvalidReport, WriteStop,
    WriteNoStop, StopFinder_Route_Trip, StopFinder_Next_Stop)
from test.test_transit_system import Sample_Transit_Data
from caravel.transit_system import Candidate, Stop, Stop_Time, Route, Trip
from caravel.report import Location, Arrival

class Test_StopFinder( Sample_Transit_Data ):
    def setUp( self ):
        super( Test_StopFinder, self ).setUp()
        timestamp= datetime.datetime( 2012, 2, 28, 6, 33, 0 )
        lat, lon = 36.85192-self.feet250,-76.28732
        time= (timestamp.hour*60+timestamp.minute)*60+timestamp.second
        self.arr= Arrival(
            timestamp=timestamp,
            id='3247',
            lat=lat, lon=lon, ll_valid='V',
            adhere= '-1', adhere_valid='V',
            time=time, rte='28', dir='1', stop='30' )
        self.loc= Location(
            timestamp=timestamp,
            lat=lat, lon=lon, ll_valid='V',
            adhere= '-1', adhere_valid='V' )
        self.stop_finder= StopFinder_Route_Trip( self.connection )
    def test_timing( self ):
        start= datetime.datetime.now()
        for i in range(100):
            for misses in range(270):
                try:
                    self.stop_finder.process_report( self.loc )
                    self.fail( "Invalid" )
                except InvalidReport:
                    pass
            for hits in range(30):
                best_fit= self.stop_finder.process_report( self.arr )
        end= datetime.datetime.now()
        print( "{2} did {0} stops in {1} seconds".format( 100*300, end-start, self.stop_finder.__class__.__name__ ) )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
