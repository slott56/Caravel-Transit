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
import math
import os
from contextlib import closing
from spike.arrival_at_stop import (
    StopFinder, InvalidReport, WriteStop,
    WriteNoStop, StopFinder_Route_Trip, StopFinder_Next_Stop,
    Candidate)
from test.test_transit_system import Sample_Transit_Data
from caravel.report import Location, Arrival
import caravel.transit_system.load

content = dict(
        agency= """\
agency_name,agency_url,agency_timezone
Hampton Roads Transit (HRT),http://www.gohrt.com/,America/New_York
""",
# Real Data
#        calendar= """\
#service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
#WE,1,1,1,1,1,0,0,20120122,20121229
#MR,1,1,1,1,0,0,0,20120122,20121229
#""",
        calendar= """\
service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
WE,1,1,1,1,1,0,0,20120122,20120601
MR,1,1,1,1,0,0,0,20120122,20120601
""",
        calendar_dates= """\
service_id,date,exception_type
WE,20120528,2
SA,20120528,1
""",
        fare_attributes= """\
fare_id,price,currency_type,payment_method,transfers
1,1.50,USD,0,2
""",
        fare_rules= """\
fare_id,route_id
1,001
""",
        routes= """\
route_id,route_short_name,route_long_name,route_desc,route_type,route_url
001,1,GRANBY ST, Downtown Norfolk Pembroke East ,3,http://www.gohrt.com/routes/route-1.pdf
004,4,CHURCH ST, Norfolk General Hospital/ODU/Downtown Norfolk ,3,http://www.gohrt.com/routes/route-4.pdf
090,90,ELIZABETH RIVER FERRY, Norfolk/Portsmouth Ferry,4,http://www.gohrt.com/services/paddlewheel-ferry#schedule
""",
        stop_times= """\
trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint
1,7:15:00,7:15:00,F001,1,1
53651,5:19:00,5:19:00,0020,7,0
53678,6:33:00,6:33:00,0001,4,0
53678,6:38:00,6:38:00,0406,5,0
""",
        stops= """\
stop_id,stop_name,stop_lat,stop_lon
0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732
0020,GRANBY & 33RD,36.87707,-76.28177
2111,WEAVER & MARTHA LEE,37.02489,-76.42312
0406,CHURCH & OLNEY,36.85400,-76.27973
F001,FERRY STOP - WATERSIDE,36.84403,-76.28941
""",
        trips= """\
route_id,service_id,trip_id,direction_id,block_id
090,WE,1,0,090 -  1
001,MR,53651,0,001 -  3
004,MR,53678,0,004 -  2
""",
    )

class MockAccessor( caravel.transit_system.load.Accessor ):
    def open( self, filename ):
        name, ext = os.path.splitext(filename)
        return closing( StringIO.StringIO( content[name] ) )

class Sample_Transit_Data( unittest.TestCase ):
    def setUp( self ):
        self.connection= MockAccessor( )
        self.half_mile= (.5 * 180/math.pi)/3961.3
        self.feet250= ((250./5280) * 180/math.pi)/3961.3

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
        self.assertEqual( '53678', best_fit.stop_time['trip_id'] )
        self.assertEqual( '0001', best_fit.stop_time['stop_id'] )

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
        self.assertEqual( '53678', best_fit.stop_time['trip_id'] )
        self.assertEqual( '0001', best_fit.stop_time['stop_id'] )
        #print( best_fit, best_fit.route, best_fit.trip )
        self.assertEqual( '004', best_fit.route['route_id'] )
        self.assertEqual( '53678', best_fit.trip['trip_id'] )

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
        self.assertEqual( '53678', best_fit.stop_time['trip_id'] )
        self.assertEqual( '0001', best_fit.stop_time['stop_id'] )
        #print( best_fit )
        self.assertEqual( '0406', best_fit.next['stop_id'] )

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
        stop= dict( stop_id='0001', stop_name='CHARLOTTE & MONTICELLO',
                   stop_lat=36.85192, stop_lon=-76.28732)
        stop_time= dict( trip_id='53678', arrival_time=23580, departure_time=23580,
            stop_id='0001', stop_sequence='4', timepoint='0')
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
        stop= dict( stop_id='0001', stop_name='CHARLOTTE & MONTICELLO',
                   stop_lat=36.85192,stop_lon=-76.28732)
        stop_time= dict(
            trip_id='53678', arrival_time=23580, departure_time=23580,
            stop_id='0001',stop_sequence='4',timepoint='0')
        route= dict(
            route_id='004', route_short_name='4', route_long_name='CHURCH ST',
            route_desc=' Norfolk General Hospital/ODU/Downtown Norfolk ',
            route_type='3', route_url='http://www.gohrt.com/routes/route-4.pdf' )
        trip= dict( route_id='004', service_id='MR', trip_id='53678',
            direction_id='0', block_id='004 -  2')
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
        stop= dict( stop_id='0001', stop_name='CHARLOTTE & MONTICELLO',
                   stop_lat=36.85192,stop_lon=-76.28732)
        stop_time= dict(
            trip_id='53678', arrival_time=23580, departure_time=23580,
            stop_id='0001',stop_sequence='4',timepoint='0')
        route= dict(
            route_id='004', route_short_name='4', route_long_name='CHURCH ST',
            route_desc=' Norfolk General Hospital/ODU/Downtown Norfolk ',
            route_type='3', route_url='http://www.gohrt.com/routes/route-4.pdf' )
        trip= dict( route_id='004', service_id='MR', trip_id='53678',
            direction_id='0', block_id='004 -  2')
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
