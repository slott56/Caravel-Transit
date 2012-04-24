#!/usr/bin/env python2.7
"""Test Caravel transit_system module.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import os
import zipfile
import datetime
from caravel.transit_system.models import Service, Stop_Definition, Route_Definition
import caravel.transit_system.load
import caravel.transit_system.query

import math

from couchdbkit import Server
from couchdbkit.designer import push

def setUpModule():

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
    try:
        os.remove( "test.zip" )
    except OSError:
        pass
    z= zipfile.ZipFile( "test.zip", 'w' )
    for c in content:
        z.writestr( c+".txt", content[c] )
    z.close()

    global connection, db
    connection = Server()
    db = connection.get_or_create_db('couchdbkit_test')
    push('_design/service', db)

    loader = caravel.transit_system.load.Loader()
    loader.load( "test.zip" )

def tearDownModule():
    try:
        os.remove( "test.zip" )
    except OSError:
        pass
    global connection
    del connection['couchdbkit_test']

class Sample_Transit_Data( unittest.TestCase ):
    def setUp( self ):
        super( Sample_Transit_Data, self ).setUp()
        self.half_mile= (.5 * 180/math.pi)/3961.3
        self.feet250= ((250./5280) * 180/math.pi)/3961.3

class Test_GetClosestStops( Sample_Transit_Data ):
    def test_should_rank_distances( self ):
        ranked= caravel.transit_system.query.get_closest_stops( (36.85192,-76.28732) )
        self.assertEqual( 5, len(ranked) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0, dist )
        self.assertEqual( '0001', stop.stop_id )
        dist, stop = ranked[1]
        self.assertEqual( '0406', stop.stop_id )
        dist, stop = ranked[2]
        self.assertEqual( 'F001', stop.stop_id )
        dist, stop = ranked[3]
        self.assertEqual( '0020', stop.stop_id )

        ranked= caravel.transit_system.query.get_closest_stops( (36.85192+self.half_mile,-76.28732) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0.5, dist )
        self.assertEqual( '0001', stop.stop_id )
    def test_should_filter_distance( self ):
        ranked= caravel.transit_system.query.get_closest_stops( (36.85192+self.half_mile,-76.28732), max_dist=0.6 )
        self.assertEqual( 2, len(ranked) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0.5, dist )
        self.assertEqual( '0001', stop.stop_id )

        ranked= caravel.transit_system.query.get_closest_stops( (36.85192+self.half_mile,-76.28732), max_dist=0.4 )
        self.assertEqual( 0, len(ranked) )
    def test_should_filter_direction( self ):
        ranked_iter= caravel.transit_system.query.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date( self ):
        #print(">>> test_should_filter_date")
        ranked= caravel.transit_system.query.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23) )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,29) )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date_and_time( self ):
        ranked= caravel.transit_system.query.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23), time=(6*60+33)*60 )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23), time=(7*60+15)*60 )
        self.assertEqual( 0, len(list(ranked)) )


class Test_GetClosestTimesInService( Sample_Transit_Data ):
    def test_should_rank_times( self ):
        ranked= caravel.transit_system.query.get_closest_times_in_service( '0001', 23580, ['MR'] )
        self.assertEqual( 1, len(ranked) )
        time, stop_time = ranked[0]
        #print( ">>> test_should_rank_times", time, stop_time )
        self.assertEqual( 0, time )
        self.assertEqual( 23580, stop_time['arrival_time'] )
        self.assertEqual( '4', stop_time['stop_sequence'] )

class Test_GetCandidateStops( Sample_Transit_Data ):
    def test_should_not_find_half_mile( self ):
        ranked= list(caravel.transit_system.query.get_candidate_stops( (36.85192+self.half_mile,-76.28732),  23580, ['MR'] ))
        self.assertEqual( 0, len(ranked) )
    def test_should_find_250feet( self ):
        ranked= list(caravel.transit_system.query.get_candidate_stops( (36.85192+self.feet250,-76.28732),  23580, ['MR'] ))
        self.assertEqual( 1, len(ranked) )
        dist, time, stop, stop_time = ranked[0]
        #print( ">>> test_should_find_250feet", dist, time, stop, stop_time )
        self.assertTrue( 249 <= dist <= 250 )
        self.assertEqual( 0, time )
        self.assertEqual( u'CHARLOTTE & MONTICELLO', stop.stop_name )
        self.assertEqual( 23580, stop_time['arrival_time'] )

class Test_GetClosestRoutes( Sample_Transit_Data ):
    def test_should_filter_direction( self ):
        ranked_iter= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_exclude_remote_routes( self ):
        ranked_iter= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '090', max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 0, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '090', max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date( self ):
        ranked= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,26) )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,28) )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date_and_time( self ):
        ranked= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,26), time=(6*60+33)*60 )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.query.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,26), time=(7*60+15)*60 )
        self.assertEqual( 0, len(list(ranked)) )

class Test_Other_Queries( Sample_Transit_Data ):
    def test_should_get_route( self ):
        r = caravel.transit_system.query.get_route_from_stop_time( 23580 )
        ##print( "test_should_get_route", r )
        self.assertEqual( '001', r[0].route_id )
        self.assertIn( '53651', r[0].trips['MR'])
    def test_should_get_all_routes( self ):
        rl = list( caravel.transit_system.query.get_route( ) )
        self.assertEqual( 3, len(rl) )
    def test_should_get_specific_route( self ):
        r = caravel.transit_system.query.get_route('090' )[0]
        trip_list = r.trips['WE']
        self.assertIn('1', trip_list)
        self.assertEqual( '090', r.route_id )
    def test_should_get_all_stops( self ):
        sl_iter = caravel.transit_system.query.get_stop()
        sl= list(sl_iter)
        self.assertEqual( 5, len(sl) )
    def test_should_get_specific_stop( self ):
        s = caravel.transit_system.query.get_stop( id='0001' )[0]
        self.assertEqual( '0001', s.stop_id )
    def test_should_get_stops_on_route( self ):
        r = caravel.transit_system.query.get_route_stops( '090', dir='0' )
        self.assertEqual( '090', r.route_id )
        sl= r.trips['WE']['1']['stops']
        self.assertEqual( 1, len(sl) )
        self.assertEqual( 'F001', sl[0]['stop_id'] )

        # No stops in this direction
        r = caravel.transit_system.query.get_route_stops( '090', dir='1' )
        self.assertEqual( '090', r.route_id )
        sl= r.trips['WE'] # No actual stuff... ['1']['stops']
        self.assertEqual( 0, len(sl) )
    def test_should_get_stops_on_date( self ):
        r = caravel.transit_system.query.get_route_stops( '090', date=datetime.date(2012,1,23) )
        self.assertEqual( '090', r.route_id )
        self.assertEqual( 1, len(r.trips) )
        self.assertEqual( 'F001', r.trips['WE']['1']['stops'][0]['stop_id'] )

    def test_should_get_stop_times( self ):
        s= caravel.transit_system.query.get_stop_times( '0001' )
        self.assertEqual( '0001', s.stop_id )
        self.assertEqual( 1, len(s.trips) )
    def test_should_get_stop_times_direction( self ):
        s= caravel.transit_system.query.get_stop_times( '0001', dir='0' )
        self.assertEqual( '0001', s.stop_id )
        self.assertEqual( 1, len(s.trips) )
    def test_should_get_stop_times_date( self ):
        s= caravel.transit_system.query.get_stop_times( '0001', date=datetime.date(2012,1,23) )
        self.assertEqual( '0001', s.stop_id )
        st_list= s.trips['MR']['53678']['times']
        self.assertEqual( 1, len(st_list) )

class Test_Next_Stop( Sample_Transit_Data ):
    def test_should_get_next_stop( self ):
        stop= list( Stop_Definition.view('service/stop',key='0001') )[0]
        stop_time= 23580
        stops = list( caravel.transit_system.query.get_next_stop_time( stop, stop_time, services=['WE','MR'],  ) )
        #print( ">>> test_should_get_next_stop", stops )
        self.assertEqual( '0001', stops[0]['stop_id'])
        self.assertEqual( '0406', stops[1]['stop_id'])

"""
..  todo:: Additional tests required for these helper functions

    These are part of :py:func:`transit_system.get_closest_stops_filtered`

    - filter_stops_by_dir
    - filter_stops_by_date
    - filter_stops_by_time
"""

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
