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
        self.arr= Arrival( timestamp=timestamp, id='3247',
                          lat=lat, lon=lon, ll_valid='V',
                          adher=-1, adher_valid='V',
                time=time, rte='28', dir='1', stop='30' )
        self.loc= Location( timestamp=timestamp, id='3247',
                        lat=lat, lon=lon, ll_valid='V',
                        adher=-1, adher_valid='V', )
        self.stop_finder= StopFinder( self.connection )
    def test_should_reject( self ):
        self.assertRaises( InvalidReport, self.stop_finder.process_report, ( self.loc ) )
    def test_should_accept( self ):
        best_fit= self.stop_finder.process_report( self.arr )
        self.assertTrue( 249 <= best_fit.distance <= 251 )
        self.assertEqual( '53678', best_fit.stop_time.trip_id )
        self.assertEqual( '0001', best_fit.stop_time.stop_id )

class Test_StopFinder_Route_Trip( Sample_Transit_Data ):
    def setUp( self ):
        super( Test_StopFinder_Route_Trip, self ).setUp()
        timestamp= datetime.datetime( 2012, 2, 28, 6, 33, 0 )
        lat, lon = 36.85192-self.feet250,-76.28732
        time= (timestamp.hour*60+timestamp.minute)*60+timestamp.second
        self.arr= Arrival( timestamp=timestamp, id='3247',
                        lat=lat, lon=lon, ll_valid='V',
                        adher=-1, adher_valid='V',
                time=time, rte='28', dir='1', stop='30' )
        self.loc= Location( timestamp=timestamp, id='3247',
                          lat=lat, lon=lon, ll_valid='V',
                          adher=-1, adher_valid='V',
        )
        self.stop_finder= StopFinder_Route_Trip( self.connection )
    def test_should_reject( self ):
        self.assertRaises( InvalidReport, self.stop_finder.process_report, ( self.loc ) )
    def test_should_accept( self ):
        best_fit= self.stop_finder.process_report( self.arr )
        self.assertTrue( 249 <= best_fit.distance <= 251 )
        self.assertEqual( '53678', best_fit.stop_time.trip_id )
        self.assertEqual( '0001', best_fit.stop_time.stop_id )
        #print( best_fit )
        self.assertEqual( self.connection.routes['004'], best_fit.route )
        self.assertEqual( self.connection.trips['53678'], best_fit.trip )

class Test_StopFinder_Next_Stop( Sample_Transit_Data ):
    def setUp( self ):
        super( Test_StopFinder_Next_Stop, self ).setUp()
        timestamp= datetime.datetime( 2012, 2, 28, 6, 33, 0 )
        lat, lon = 36.85192-self.feet250,-76.28732
        time= (timestamp.hour*60+timestamp.minute)*60+timestamp.second
        self.arr= Arrival( timestamp=timestamp, id='3247',
                        lat=lat, lon=lon, ll_valid='V',
                        adher=-1, adher_valid='V',
                time=time, rte='28', dir='1', stop='30' )
        self.loc= Location( timestamp=timestamp, id='3247',
                        lat=lat, lon=lon, ll_valid='V',
                        adher=-1, adher_valid='V', )
        self.stop_finder= StopFinder_Next_Stop( self.connection )
    def test_should_reject( self ):
        self.assertRaises( InvalidReport, self.stop_finder.process_report, ( self.loc ) )
    def test_should_accept( self ):
        best_fit= self.stop_finder.process_report( self.arr )
        self.assertTrue( 249 <= best_fit.distance <= 251 )
        self.assertEqual( '53678', best_fit.stop_time.trip_id )
        self.assertEqual( '0001', best_fit.stop_time.stop_id )
        #print( best_fit )
        self.assertEqual( '0406', best_fit.next.stop_id )

class Test_StopFinder_Write( unittest.TestCase ):
    def setUp( self ):
        timestamp= datetime.datetime( 2012, 2, 28, 6, 33, 0 )
        lat, lon = 36.85192,-76.28732
        time= (timestamp.hour*60+timestamp.minute)*60+timestamp.second
        self.arr= Arrival( timestamp=timestamp, id='3247',
                          lat=lat, lon=lon, ll_valid='V',
                          adher=-1, adher_valid='V',
                time=time, rte='28', dir='1', stop='30' )
        self.buffer= StringIO.StringIO()
        sf= StopFinder( None )
        self.stop= WriteStop( sf, self.buffer )
    def test_should_write_csv( self ):
        stop= Stop('0001','CHARLOTTE & MONTICELLO',36.85192,-76.28732)
        stop_time= Stop_Time('53678',23580,23580,'0001','4','0')
        self.stop( self.arr, Candidate(2,3,stop,stop_time) )
        lines= self.buffer.getvalue().splitlines()
        titles= ['adher', 'adher_valid', 'blk', 'dgps', 'dir',
        'dwell', 'fom', 'id', 'lat', 'll_valid', 'lon', 'odom', 'odom_valid',
        'rte', 'stop', 'svc', 'time', 'timestamp', 'tp', 'distance', 'time',
        'stop_stop_id', 'stop_stop_name', 'stop_stop_lat', 'stop_stop_lon',
        'stop_time_trip_id', 'stop_time_arrival_time',
        'stop_time_departure_time', 'stop_time_stop_id',
        'stop_time_stop_sequence', 'stop_time_timepoint']
        self.assertEqual( set(titles), set(self.stop.fieldnames) )
        self.assertEqual( "2012-02-28 06:33:00,3247,36.85192,-76.28732,V,-1,V,,,,,3,,28,1,30,,,,2,3,0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732,53678,23580,23580,0001,4,0", lines[1] )

class Test_StopFinder_Route_Trip_Write( unittest.TestCase ):
    def setUp( self ):
        timestamp= datetime.datetime( 2012, 2, 28, 6, 33, 0 )
        lat, lon = 36.85192,-76.28732
        time= (timestamp.hour*60+timestamp.minute)*60+timestamp.second
        self.arr= Arrival( timestamp=timestamp, id='3247',
                          lat=lat, lon=lon, ll_valid='V',
                          adher=-1, adher_valid='V',
                time=time, rte='28', dir='1', stop='30' )
        self.buffer= StringIO.StringIO()
        sf= StopFinder_Route_Trip( None )
        self.stop= WriteStop( sf, self.buffer )
    def test_should_write_csv( self ):
        stop= Stop('0001','CHARLOTTE & MONTICELLO',36.85192,-76.28732)
        stop_time= Stop_Time('53678',23580,23580,'0001','4','0')
        route= Route( '004','4','CHURCH ST',' Norfolk General Hospital/ODU/Downtown Norfolk ','3','http://www.gohrt.com/routes/route-4.pdf' )
        trip= Trip('004','MR','53678','0','004 -  2')
        self.stop( self.arr, StopFinder_Route_Trip.Best_Fit(2,3,stop,stop_time,route,trip) )
        lines= self.buffer.getvalue().splitlines()
        titles= ['adher', 'adher_valid', 'blk', 'dgps', 'dir',
        'dwell', 'fom', 'id', 'lat', 'll_valid', 'lon', 'odom', 'odom_valid',
        'rte', 'stop', 'svc', 'time', 'timestamp', 'tp', 'distance', 'time',
        'stop_stop_id', 'stop_stop_name', 'stop_stop_lat', 'stop_stop_lon',
        'stop_time_trip_id', 'stop_time_arrival_time',
        'stop_time_departure_time', 'stop_time_stop_id',
        'stop_time_stop_sequence', 'stop_time_timepoint', 'route_route_id',
        'route_route_short_name', 'route_route_long_name', 'route_route_desc',
        'route_route_type', 'route_route_url', 'trip_route_id',
        'trip_service_id', 'trip_trip_id', 'trip_direction_id', 'trip_block_id']
        self.assertEqual(set(titles), set(self.stop.fieldnames) )
        self.assertEqual( '2012-02-28 06:33:00,3247,36.85192,-76.28732,V,-1,V,,,,,3,,28,1,30,,,,2,3,0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732,53678,23580,23580,0001,4,0,004,4,CHURCH ST, Norfolk General Hospital/ODU/Downtown Norfolk ,3,http://www.gohrt.com/routes/route-4.pdf,004,MR,53678,0,004 -  2', lines[1] )

class Test_StopFinder_Next_Stop_Write( unittest.TestCase ):
    def setUp( self ):
        timestamp= datetime.datetime( 2012, 2, 28, 6, 33, 0 )
        lat, lon = 36.85192,-76.28732
        time= (timestamp.hour*60+timestamp.minute)*60+timestamp.second
        self.arr= Arrival( timestamp=timestamp, id='3247',
                          lat=lat, lon=lon, ll_valid='V',
                          adher=-1, adher_valid='V',
                time=time, rte='28', dir='1', stop='30' )
        self.buffer= StringIO.StringIO()
        sf= StopFinder_Next_Stop( None )
        self.stop= WriteStop( sf, self.buffer )
    def test_should_write_csv( self ):
        stop= Stop('0001','CHARLOTTE & MONTICELLO',36.85192,-76.28732)
        stop_time= Stop_Time('53678',23580,23580,'0001','4','0')
        route= Route( '004','4','CHURCH ST',' Norfolk General Hospital/ODU/Downtown Norfolk ','3','http://www.gohrt.com/routes/route-4.pdf' )
        trip= Trip('004','MR','53678','0','004 -  2')
        self.stop( self.arr, StopFinder_Next_Stop.Best_Fit(2,3,stop,stop_time,route,stop) )
        lines= self.buffer.getvalue().splitlines()
        titles= ['adher', 'adher_valid', 'blk', 'dgps', 'dir',
        'dwell', 'fom', 'id', 'lat', 'll_valid', 'lon', 'odom', 'odom_valid',
        'rte', 'stop', 'svc', 'time', 'timestamp', 'tp', 'distance', 'time',
        'stop_stop_id', 'stop_stop_name', 'stop_stop_lat', 'stop_stop_lon',
        'stop_time_trip_id', 'stop_time_arrival_time',
        'stop_time_departure_time', 'stop_time_stop_id',
        'stop_time_stop_sequence', 'stop_time_timepoint', 'route_route_id',
        'route_route_short_name', 'route_route_long_name', 'route_route_desc',
        'route_route_type', 'route_route_url', 'next_stop_id', 'next_stop_name',
        'next_stop_lat', 'next_stop_lon']
        self.assertEqual(set(titles), set(self.stop.fieldnames) )
        self.assertEqual( '2012-02-28 06:33:00,3247,36.85192,-76.28732,V,-1,V,,,,,3,,28,1,30,,,,2,3,0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732,53678,23580,23580,0001,4,0,004,4,CHURCH ST, Norfolk General Hospital/ODU/Downtown Norfolk ,3,http://www.gohrt.com/routes/route-4.pdf,0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732', lines[1] )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
