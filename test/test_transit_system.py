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
import caravel.transit_system
import math
from test.test_acquire import MockHTTP

class Test_Get_Source( unittest.TestCase ):
    def setUp( self ):
        self.http_class= MockHTTP
        try:
            os.remove( 'test/google_transit.zip' )
        except OSError as e:
            self.assertEqual( 2, e.errno )
    def runTest( self ):
        self.name= caravel.transit_system.get_source_data( self.http_class(), target_dir='test' )
        self.assertTrue( os.path.exists( 'test/google_transit.zip' ) )
        with open('test/google_transit.zip','rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "New Lines Of Data", new_data )
        self.assertEqual( [("http://googletf.gohrt.com/google_transit.zip",)], self.http_class.history )
    def tearDown( self ):
        try:
            os.remove( 'test/google_transit.zip' )
        except OSError as e:
            self.assertEqual( 2, e.errno )

class Test_AccessZip( unittest.TestCase ):
    content= """\
service_id,date,exception_type
MR,20120102,2
"""
    def setUp( self ):
        try:
            os.remove( "test.zip" )
        except OSError:
            pass
        z= zipfile.ZipFile( "test.zip", 'w' )
        z.writestr( "calendar_dates.txt", Test_AccessZip.content )
        z.close()
        self.accessor = caravel.transit_system.AccessZip( "test.zip" )
    def tearDown( self ):
        try:
            os.remove( "test.zip" )
        except OSError:
            pass
    def test_should_access( self ):
        with self.accessor.open( "calendar_dates.txt" ) as aFile:
            content= aFile.read()
        self.assertEqual( Test_AccessZip.content, content )

class Test_AccessDir( Test_AccessZip ):
    def setUp( self ):
        try:
            os.mkdir( "test.dir" )
        except OSError:
            pass
        with open( os.path.join( "test.dir", "calendar_dates.txt" ), "wb" ) as target:
            target.write( Test_AccessZip.content )
        self.accessor = caravel.transit_system.AccessDir( "test.dir" )
    def tearDown( self ):
        try:
            os.remove( os.path.join( "test.dir", "calendar_dates.txt" ) )
        except OSError:
            pass
        try:
            os.rmdir( "test.dir" )
        except OSError:
            pass

class Test_Load( unittest.TestCase ):
    content = dict(
        agency= """\
agency_name,agency_url,agency_timezone
Hampton Roads Transit (HRT),http://www.gohrt.com/,America/New_York
""",
        calendar= """\
service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
WE,1,1,1,1,1,0,0,20120122,20121229
""",
        calendar_dates= """\
service_id,date,exception_type
MR,20120102,2
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
""",
        stop_times= """\
trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint
1,7:15:00,7:15:00,F001,1,1
53678,6:33:00,6:33:00,0001,4,0
""",
        stops= """\
stop_id,stop_name,stop_lat,stop_lon
0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732
""",
        trips= """\
route_id,service_id,trip_id,direction_id,block_id
090,WE,1,0,090 -  1
""",
    )
    def setUp( self ):
        try:
            os.remove( "test.zip" )
        except OSError:
            pass
        z= zipfile.ZipFile( "test.zip", 'w' )
        for c in Test_Load.content:
            z.writestr( c+".txt", Test_Load.content[c] )
        z.close()
        self.connection = caravel.transit_system.Connection()
    def tearDown( self ):
        try:
            os.remove( "test.zip" )
        except OSError:
            pass
    def test_should_load_calendar( self ):
        start= datetime.datetime.strptime('20120122',"%Y%m%d").date()
        end= datetime.datetime.strptime('20121229',"%Y%m%d").date()
        self.connection.open( "test.zip" )
        cal= [ caravel.transit_system.Calendar( 'WE','1','1','1','1','1','0','0',start,end ),
            ]
        self.assertEqual( cal, self.connection.calendar )
    def test_should_load_calendar_dates( self ):
        date= datetime.datetime.strptime('20120102',"%Y%m%d").date()
        self.connection.open( "test.zip" )
        cal_date= { date: caravel.transit_system.Calendar_Date( 'MR',date,'2' ), }
        self.assertEqual( cal_date, self.connection.calendar_dates )
    def test_should_load_routes( self ):
        self.connection.open( "test.zip" )
        routes = {
            '001': caravel.transit_system.Route( '001','1','GRANBY ST',' Downtown Norfolk Pembroke East ','3','http://www.gohrt.com/routes/route-1.pdf'),
            }
        self.assertEqual( routes, self.connection.routes )
    def test_should_load_trips( self ):
        self.connection.open( "test.zip" )
        trips = {
            '1':  caravel.transit_system.Trip('090','WE','1','0','090 -  1'),
        }
        self.assertEqual( trips, self.connection.trips )
    def test_should_load_stops( self ):
        self.connection.open( "test.zip" )
        stops = {
            '0001': caravel.transit_system.Stop('0001','CHARLOTTE & MONTICELLO',36.85192,-76.28732),
        }
        self.assertEqual( stops, self.connection.stops )
    def test_should_load_stop_times_and_trip_times( self ):
        self.connection.open( "test.zip" )
        stop_times = {
            '0001': [caravel.transit_system.Stop_Time('53678',23580,23580,'0001','4','0')],
            'F001': [caravel.transit_system.Stop_Time('1',26100,26100,'F001','1','1')]
        }
        trip_times = {
            '53678': [caravel.transit_system.Stop_Time('53678',23580,23580,'0001','4','0')],
            '1': [caravel.transit_system.Stop_Time('1',26100,26100,'F001','1','1')]
        }
        self.assertEqual( stop_times, self.connection.stop_times )
        self.assertEqual( trip_times, self.connection.trip_times )

class Test_Distance( unittest.TestCase ):
    def test_radians( self ):
        self.assertAlmostEqual( 0, caravel.transit_system.radians(0) )
        self.assertAlmostEqual( math.pi/2, caravel.transit_system.radians(90) )
        self.assertAlmostEqual( math.pi*(-76/180), caravel.transit_system.radians(-76) )
    def test_distance( self ):
        sm=3961.3*math.pi*1/180 # 1 degree in statue miles
        self.assertAlmostEqual( 0, caravel.transit_system.dist_approx( (36.85192,-76.28732), (36.85192,-76.28732) )  )
        self.assertAlmostEqual( sm, caravel.transit_system.dist_approx( (36.85192,-76.28732), (35.85192,-76.28732) )  )
        self.assertAlmostEqual( sm*math.cos(math.pi*36.85192/180), caravel.transit_system.dist_approx( (36.85192,-76.28732), (36.85192,-77.28732) )  )
        self.assertAlmostEqual( sm*math.sqrt( 1 + math.cos(math.pi*36.85192/180)**2 ), caravel.transit_system.dist_approx( (36.85192-.5,-76.28732), (36.85192+.5,-77.28732) )  )

class Test_GetServicesToday( unittest.TestCase ):
    def setUp( self ):
        self.connection= caravel.transit_system.Connection()
        start= datetime.datetime.strptime('20120122',"%Y%m%d").date()
        end= datetime.datetime.strptime('20121229',"%Y%m%d").date()
        self.connection.calendar = [
            caravel.transit_system.Calendar( 'WE','1','1','1','1','1','0','0',start,end ),
            caravel.transit_system.Calendar( 'SA','0','0','0','0','0','1','0',start,end ),
            ]
        date= datetime.datetime.strptime('20120102',"%Y%m%d").date()
        self.connection.calendar_dates= {
            date: caravel.transit_system.Calendar_Date( 'MR',date,'2' ), }

    def test_should_get_override( self ):
        date = datetime.date( 2012, 1, 2 )
        self.assertEqual( ["MR"], list(caravel.transit_system.get_services_today( self.connection, date )) )
    def test_should_get_default( self ):
        date = datetime.date( 2012, 1, 22 ) # Sunday
        self.assertEqual( [], list(caravel.transit_system.get_services_today( self.connection, date )) )
        date = datetime.date( 2012, 1, 23 ) # Monday
        self.assertEqual( ['WE'], list(caravel.transit_system.get_services_today( self.connection, date )) )
        date = datetime.date( 2012, 12, 29 ) # Saturday
        self.assertEqual( ['SA'], list(caravel.transit_system.get_services_today( self.connection, date )) )

class Sample_Transit_Data( unittest.TestCase ):
    def setUp( self ):
        start= datetime.datetime.strptime('20120122',"%Y%m%d").date()
        end= datetime.datetime.strptime('20121229',"%Y%m%d").date()
        self.connection= caravel.transit_system.Connection()
        self.connection.calendar_dates = {}
        self.connection.calendar = [
            caravel.transit_system.Calendar( 'WE','1','1','1','1','1','0','0',start,end ),
            caravel.transit_system.Calendar( 'MR','1','1','1','1','0','0','0',start,end ),
        ]
        self.connection.stops = {
            '0001': caravel.transit_system.Stop('0001','CHARLOTTE & MONTICELLO',36.85192,-76.28732),
            '0020': caravel.transit_system.Stop('0020','GRANBY & 33RD',36.87707,-76.28177),
            '2111': caravel.transit_system.Stop('2111','WEAVER & MARTHA LEE',37.02489,-76.42312),
            'F001': caravel.transit_system.Stop('F001','FERRY STOP - WATERSIDE',36.84403,-76.28941),
            '0406': caravel.transit_system.Stop('0406','CHURCH & OLNEY',36.85400,-76.27973),
        }
        self.connection.stop_times = {
            '0001': [caravel.transit_system.Stop_Time('53678',23580,23580,'0001','4','0')],
            '0406': [caravel.transit_system.Stop_Time('53678',23880,23880,'0406','5','0')],
            '0020': [caravel.transit_system.Stop_Time('53651',19140,19140,'0020','7','0')],
            'F001': [caravel.transit_system.Stop_Time('1',26100,26100,'F001','1','1')],
            '2111': [caravel.transit_system.Stop_Time('63864',29160,29160,'2111','18','1')],
        }
        self.connection.trips = {
            '1':  caravel.transit_system.Trip('090','WE','1','0','090 -  1'),
            '53678': caravel.transit_system.Trip('004','MR','53678','0','004 -  2'),
        }
        self.connection.routes = {
            '004': caravel.transit_system.Route( '004','4','CHURCH ST',' Norfolk General Hospital/ODU/Downtown Norfolk ','3','http://www.gohrt.com/routes/route-4.pdf' ),
            '090': caravel.transit_system.Route( '090','90','ELIZABETH RIVER FERRY',' Norfolk/Portsmouth Ferry','4','http://www.gohrt.com/services/paddlewheel-ferry#schedule' ),
        }
        self.connection.build_indices()
        self.half_mile= (.5 * 180/math.pi)/3961.3
        self.feet250= ((250./5280) * 180/math.pi)/3961.3

class Test_GetClosestStops( Sample_Transit_Data ):
    def test_should_rank_distances( self ):
        ranked= caravel.transit_system.get_closest_stops( self.connection, (36.85192,-76.28732) )
        self.assertEqual( 5, len(ranked) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0, dist )
        self.assertEqual( self.connection.stops['0001'], stop )
        dist, stop = ranked[1]
        self.assertEqual( self.connection.stops['0406'], stop )
        dist, stop = ranked[2]
        self.assertEqual( self.connection.stops['F001'], stop )
        dist, stop = ranked[3]
        self.assertEqual( self.connection.stops['0020'], stop )

        ranked= caravel.transit_system.get_closest_stops( self.connection, (36.85192+self.half_mile,-76.28732) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0.5, dist )
        self.assertEqual( self.connection.stops['0001'], stop )
    def test_should_filter_distance( self ):
        ranked= caravel.transit_system.get_closest_stops( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6 )
        self.assertEqual( 2, len(ranked) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0.5, dist )
        self.assertEqual( self.connection.stops['0001'], stop )

        ranked= caravel.transit_system.get_closest_stops( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.4 )
        self.assertEqual( 0, len(ranked) )
    def test_should_filter_direction( self ):
        ranked_iter= caravel.transit_system.get_closest_stops_filtered( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_stops_filtered( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date( self ):
        ranked= caravel.transit_system.get_closest_stops_filtered( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23) )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_stops_filtered( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,22) )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date_and_time( self ):
        ranked= caravel.transit_system.get_closest_stops_filtered( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23), time=(6*60+33)*60 )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_stops_filtered( self.connection, (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23), time=(7*60+15)*60 )
        self.assertEqual( 0, len(list(ranked)) )


class Test_GetClosestTimesInService( Sample_Transit_Data ):
    def test_should_rank_times( self ):
        ranked= caravel.transit_system.get_closest_times_in_service( self.connection, '0001', 23580, ['MR'] )
        self.assertEqual( 1, len(ranked) )
        time, stop_time = ranked[0]
        self.assertEqual( 0, time )
        self.assertEqual( self.connection.stop_times['0001'][0], stop_time )

class Test_GetCandidateStops( Sample_Transit_Data ):
    def test_should_not_find_half_mile( self ):
        ranked= list(caravel.transit_system.get_candidate_stops( self.connection, (36.85192+self.half_mile,-76.28732),  23580, ['MR'] ))
        self.assertEqual( 0, len(ranked) )
    def test_should_find_250feet( self ):
        ranked= list(caravel.transit_system.get_candidate_stops( self.connection, (36.85192+self.feet250,-76.28732),  23580, ['MR'] ))
        self.assertEqual( 1, len(ranked) )
        dist, time, stop, stop_time = ranked[0]
        self.assertEqual( 0, time )
        self.assertEqual( self.connection.stop_times['0001'][0], stop_time )
        self.assertTrue( 249 <= dist <= 250 )
        self.assertEqual( self.connection.stops['0001'], stop )

class Test_GetClosestRoutes( Sample_Transit_Data ):
    def test_should_filter_direction( self ):
        ranked_iter= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 1, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_exclude_remote_routes( self ):
        ranked_iter= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '090', max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 0, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '090', max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date( self ):
        ranked= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,23) )
        self.assertEqual( 1, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,22) )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date_and_time( self ):
        ranked= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,23), time=(6*60+33)*60 )
        self.assertEqual( 1, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( self.connection, (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,23), time=(7*60+15)*60 )
        self.assertEqual( 0, len(list(ranked)) )

class Test_Other_Queries( Sample_Transit_Data ):
    def test_should_get_route( self ):
        r = caravel.transit_system.get_route_from_stop_time( self.connection, self.connection.stop_times['0001'][0] )
        self.assertEqual( r, self.connection.routes['004'] )
    def test_should_get_trip( self ):
        t = caravel.transit_system.get_trip_from_stop_time( self.connection, self.connection.stop_times['0001'][0] )
        self.assertEqual( t, self.connection.trips['53678'] )
    def test_should_get_all_routes( self ):
        rl = list( caravel.transit_system.get_route( self.connection ) )
        self.assertEqual( 2, len(rl) )
    def test_should_get_specific_route( self ):
        r, trip_list_iter = caravel.transit_system.get_route( self.connection, '090' )
        trip_list = list(trip_list_iter)
        self.assertEqual( '090', r.route_id )
        self.assertEqual( 1, len(trip_list) )
    def test_should_get_all_stops( self ):
        sl_iter = caravel.transit_system.get_stop( self.connection )
        sl= list(sl_iter)
        self.assertEqual( 5, len(sl) )
    def test_should_get_specific_stop( self ):
        s, st_list = caravel.transit_system.get_stop( self.connection, id='0001' )
        self.assertEqual( '0001', s.stop_id )
    def test_should_get_stops_on_route( self ):
        r, sl_iter = caravel.transit_system.get_route_stops( self.connection, '090', dir='0' )
        self.assertEqual( '090', r.route_id )
        sl= list(sl_iter)
        self.assertEqual( 1, len(sl) )
        self.assertEqual( 'F001', sl[0].stop_id )

        # No stops in this direction
        r, sl_iter = caravel.transit_system.get_route_stops( self.connection, '090', dir='1' )
        self.assertEqual( '090', r.route_id )
        sl= list(sl_iter)
        self.assertEqual( 0, len(sl) )
    def test_should_get_stops_on_date( self ):
        r, sl_iter = caravel.transit_system.get_route_stops( self.connection, '090', date=datetime.date(2012,1,23) )
        self.assertEqual( '090', r.route_id )
        sl= list(sl_iter)
        self.assertEqual( 1, len(sl) )
        self.assertEqual( 'F001', sl[0].stop_id )
    def test_should_get_stops_on_date_and_time( self ):
        r, sl_iter = caravel.transit_system.get_route_stops( self.connection, '090', date=datetime.date(2012,1,23), time=(7*60+15)*60 )
        self.assertEqual( '090', r.route_id )
        sl= list(sl_iter)
        self.assertEqual( 1, len(sl) )
        self.assertEqual( 'F001', sl[0].stop_id )

        r, sl_iter = caravel.transit_system.get_route_stops( self.connection, '090', date=datetime.date(2012,1,23), time=(8*60+15)*60 )
        self.assertEqual( '090', r.route_id )
        sl= list(sl_iter)
        self.assertEqual( 0, len(sl) )
    def test_should_get_stop_times( self ):
        s, st_list= caravel.transit_system.get_stop_times( self.connection, '0001' )
        self.assertEqual( '0001', s.stop_id )
        self.assertEqual( 1, len(st_list) )
    def test_should_get_stop_times_direction( self ):
        s, st_list_iter= caravel.transit_system.get_stop_times( self.connection, '0001', dir='0' )
        self.assertEqual( '0001', s.stop_id )
        st_list= list(st_list_iter)
        self.assertEqual( 1, len(st_list) )
    def test_should_get_stop_times_date( self ):
        s, st_list_iter= caravel.transit_system.get_stop_times( self.connection, '0001', date=datetime.date(2012,1,23) )
        self.assertEqual( '0001', s.stop_id )
        st_list= list(st_list_iter)
        self.assertEqual( 1, len(st_list) )
    def test_should_get_stop_times_date_time( self ):
        s, st_list_iter= caravel.transit_system.get_stop_times( self.connection, '0001', date=datetime.date(2012,1,23), time=(8*60+15)*60 )
        self.assertEqual( '0001', s.stop_id )
        st_list= list(st_list_iter)
        self.assertEqual( 1, len(st_list) )

class Test_Next_Stop( Sample_Transit_Data ):
    def test_should_get_next_stop( self ):
        stop_time= self.connection.stop_times['0001'][0]
        st_iter = caravel.transit_system.get_next_stop_time( self.connection, stop_time, services=['WE','MR'],  )
        st_list= list(st_iter)
        self.assertEqual( '0406', st_list[0].stop_id )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
