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
53678,6:33:00,6:33:00,0001,4,0
53678,6:38:00,6:38:00,0406,5,0
""",
        stops= """\
stop_id,stop_name,stop_lat,stop_lon
0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732
0020,GRANBY & 33RD,36.87707,-76.28177
0406,CHURCH & OLNEY,36.85400,-76.27973
F001,FERRY STOP - WATERSIDE,36.84403,-76.28941
""",
        trips= """\
route_id,service_id,trip_id,direction_id,block_id
090,WE,1,0,090 -  1
004,MR,53678,0,004 -  2
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
        self.loader = caravel.transit_system.Loader()
        self.loader.load( "test.zip" )
    def tearDown( self ):
        try:
            os.remove( "test.zip" )
        except OSError:
            pass
    def test_should_load_calendar( self ):
        start= list( caravel.transit_system.Service.view('service/bydate', key='2012-01-23') )[0]
        self.assertEqual( datetime.date(2012,1,23), start.date )
        self.assertEqual( u'Monday', start.day_of_week )
        self.assertEqual( ['MR', 'WE'], start.services )

        end= list( caravel.transit_system.Service.view('service/bydate', key='2012-12-28') )[0]
        self.assertEqual( datetime.date(2012,12,28), end.date )
        self.assertEqual( u'Friday', end.day_of_week )
        self.assertEqual( ['WE'], end.services )

    def test_should_load_calendar_dates( self ):
        special= list( caravel.transit_system.Service.view('service/bydate', key='2012-05-28') )[0]
        self.assertEqual( datetime.date(2012,5,28), special.date )
        self.assertEqual( u'Monday', special.day_of_week )
        self.assertEqual( ['MR', 'SA'], special.services )

    def test_should_load_routes( self ):
        route= list( caravel.transit_system.Route_Definition.view('service/route', key='001') )[0]
        self.assertEqual( '001', route.route_id )
        self.assertEqual( '1', route.route_short_name )
        self.assertEqual( 'GRANBY ST', route.route_long_name )
        self.assertEqual( ' Downtown Norfolk Pembroke East ', route.route_desc )
        self.assertEqual( '3', route.route_type )
        self.assertEqual( 'http://www.gohrt.com/routes/route-1.pdf', route.route_url )
    def test_should_load_trips( self ):
        route= list( caravel.transit_system.Route_Definition.view('service/route', key='004') )[0]
        self.assertIn( '53678', route.trips['MR'] )
        self.assertEqual( '0', route.trips['MR']['53678']['direction_id'] )
    def test_should_load_stops( self ):
        stop= list( caravel.transit_system.Stop_Definition.view('service/stop', key='0001') )[0]
        self.assertEqual( '0001', stop.stop_id )
        self.assertEqual( 'CHARLOTTE & MONTICELLO', stop.stop_name )
        self.assertAlmostEqual( 36.85192, stop.stop_lat )
        self.assertAlmostEqual( -76.28732, stop.stop_lon )
    def test_should_load_stop_times_and_trip_times( self ):
        route= list( caravel.transit_system.Route_Definition.view('service/route', key='004') )[0]
        trip= route.trips['MR']
        self.assertTrue( '53678' in trip )
        stops= trip['53678']['stops']
        self.assertEqual( 23580, stops[0]['arrival_time'] )
        self.assertEqual( 23580, stops[0]['departure_time'] )

        #trip_times = {
        #    '53678': [caravel.transit_system.Stop_Time('53678',23580,23580,'0001','4','0')],
        #    '1': [caravel.transit_system.Stop_Time('1',26100,26100,'F001','1','1')]
        #}

        stop= list( caravel.transit_system.Stop_Definition.view('service/stop', key='0001'))[0]
        times= stop.trips['MR']['53678']['times']
        self.assertEqual( 23580, times[0]['arrival_time'] )
        self.assertEqual( 23580, times[0]['departure_time'] )
        #stop_times = {
        #    '0001': [caravel.transit_system.Stop_Time('53678',23580,23580,'0001','4','0')],
        #    'F001': [caravel.transit_system.Stop_Time('1',26100,26100,'F001','1','1')]
        #}

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
        self.loader= caravel.transit_system.Loader()
        start= datetime.datetime.strptime('20120122',"%Y%m%d").date()
        end= datetime.datetime.strptime('20121229',"%Y%m%d").date()
        #self.loader.calendar = [
        #    caravel.transit_system.Calendar( 'WE','1','1','1','1','1','0','0',start,end ),
        #    caravel.transit_system.Calendar( 'SA','0','0','0','0','0','1','0',start,end ),
        #    ]
        #date= datetime.datetime.strptime('20120102',"%Y%m%d").date()
        #self.loader.calendar_dates= {
        #    date: caravel.transit_system.Calendar_Date( 'MR',date,'2' ), }

    def test_should_get_override( self ):
        date = datetime.date( 2012, 5,28 ) # Holiday Override
        self.assertEqual( ['MR', 'SA'], list(caravel.transit_system.get_services_today(  date )) )
    def test_should_get_default( self ):
        date = datetime.date( 2012, 1, 22 ) # Sunday
        self.assertEqual( [], list(caravel.transit_system.get_services_today( date )) )
        date = datetime.date( 2012, 1, 23 ) # Monday-Thursday, Weekday.
        self.assertEqual( ['MR', 'WE'], list(caravel.transit_system.get_services_today( date )) )

class Sample_Transit_Data( unittest.TestCase ):
    def setUp( self ):
        start= datetime.datetime.strptime('20120122',"%Y%m%d").date()
        end= datetime.datetime.strptime('20121229',"%Y%m%d").date()
        self.loader= caravel.transit_system.Loader()
        #self.loader.calendar_dates = {}
        #self.loader.calendar = [
        #    caravel.transit_system.Calendar( 'WE','1','1','1','1','1','0','0',start,end ),
        #    caravel.transit_system.Calendar( 'MR','1','1','1','1','0','0','0',start,end ),
        #]
        #self.loader.stops = {
        #    '0001': caravel.transit_system.Stop('0001','CHARLOTTE & MONTICELLO',36.85192,-76.28732),
        #    '0020': caravel.transit_system.Stop('0020','GRANBY & 33RD',36.87707,-76.28177),
        #    '2111': caravel.transit_system.Stop('2111','WEAVER & MARTHA LEE',37.02489,-76.42312),
        #    'F001': caravel.transit_system.Stop('F001','FERRY STOP - WATERSIDE',36.84403,-76.28941),
        #    '0406': caravel.transit_system.Stop('0406','CHURCH & OLNEY',36.85400,-76.27973),
        #}
        #self.loader.stop_times = {
        #    '0001': [caravel.transit_system.Stop_Time('53678',23580,23580,'0001','4','0')],
        #    '0406': [caravel.transit_system.Stop_Time('53678',23880,23880,'0406','5','0')],
        #    '0020': [caravel.transit_system.Stop_Time('53651',19140,19140,'0020','7','0')],
        #    'F001': [caravel.transit_system.Stop_Time('1',26100,26100,'F001','1','1')],
        #    '2111': [caravel.transit_system.Stop_Time('63864',29160,29160,'2111','18','1')],
        #}
        #self.loader.trips = {
        #    '1':  caravel.transit_system.Trip('090','WE','1','0','090 -  1'),
        #    '53678': caravel.transit_system.Trip('004','MR','53678','0','004 -  2'),
        #}
        #self.loader.routes = {
        #    '004': caravel.transit_system.Route( '004','4','CHURCH ST',' Norfolk General Hospital/ODU/Downtown Norfolk ','3','http://www.gohrt.com/routes/route-4.pdf' ),
        #    '090': caravel.transit_system.Route( '090','90','ELIZABETH RIVER FERRY',' Norfolk/Portsmouth Ferry','4','http://www.gohrt.com/services/paddlewheel-ferry#schedule' ),
        #}
        self.half_mile= (.5 * 180/math.pi)/3961.3
        self.feet250= ((250./5280) * 180/math.pi)/3961.3

class Test_GetClosestStops( Sample_Transit_Data ):
    def test_should_rank_distances( self ):
        ranked= caravel.transit_system.get_closest_stops( (36.85192,-76.28732) )
        self.assertEqual( 4, len(ranked) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0, dist )
        self.assertEqual( '0001', stop.stop_id )
        dist, stop = ranked[1]
        self.assertEqual( '0406', stop.stop_id )
        dist, stop = ranked[2]
        self.assertEqual( 'F001', stop.stop_id )
        dist, stop = ranked[3]
        self.assertEqual( '0020', stop.stop_id )

        ranked= caravel.transit_system.get_closest_stops( (36.85192+self.half_mile,-76.28732) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0.5, dist )
        self.assertEqual( '0001', stop.stop_id )
    def test_should_filter_distance( self ):
        ranked= caravel.transit_system.get_closest_stops( (36.85192+self.half_mile,-76.28732), max_dist=0.6 )
        self.assertEqual( 2, len(ranked) )
        dist, stop = ranked[0]
        self.assertAlmostEqual( 0.5, dist )
        self.assertEqual( '0001', stop.stop_id )

        ranked= caravel.transit_system.get_closest_stops( (36.85192+self.half_mile,-76.28732), max_dist=0.4 )
        self.assertEqual( 0, len(ranked) )
    def test_should_filter_direction( self ):
        ranked_iter= caravel.transit_system.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date( self ):
        #print(">>> test_should_filter_date")
        ranked= caravel.transit_system.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23) )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,29) )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date_and_time( self ):
        ranked= caravel.transit_system.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23), time=(6*60+33)*60 )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_stops_filtered( (36.85192+self.half_mile,-76.28732), max_dist=0.6, date=datetime.date(2012,1,23), time=(7*60+15)*60 )
        self.assertEqual( 0, len(list(ranked)) )


class Test_GetClosestTimesInService( Sample_Transit_Data ):
    def test_should_rank_times( self ):
        ranked= caravel.transit_system.get_closest_times_in_service( '0001', 23580, ['MR'] )
        self.assertEqual( 1, len(ranked) )
        time, stop_time = ranked[0]
        #print( ">>> test_should_rank_times", time, stop_time )
        self.assertEqual( 0, time )
        self.assertEqual( 23580, stop_time['arrival_time'] )
        self.assertEqual( '4', stop_time['stop_sequence'] )

class Test_GetCandidateStops( Sample_Transit_Data ):
    def test_should_not_find_half_mile( self ):
        ranked= list(caravel.transit_system.get_candidate_stops( (36.85192+self.half_mile,-76.28732),  23580, ['MR'] ))
        self.assertEqual( 0, len(ranked) )
    def test_should_find_250feet( self ):
        ranked= list(caravel.transit_system.get_candidate_stops( (36.85192+self.feet250,-76.28732),  23580, ['MR'] ))
        self.assertEqual( 1, len(ranked) )
        dist, time, stop, stop_time = ranked[0]
        #print( ">>> test_should_find_250feet", dist, time, stop, stop_time )
        self.assertTrue( 249 <= dist <= 250 )
        self.assertEqual( 0, time )
        self.assertEqual( u'CHARLOTTE & MONTICELLO', stop.stop_name )
        self.assertEqual( 23580, stop_time['arrival_time'] )

class Test_GetClosestRoutes( Sample_Transit_Data ):
    def test_should_filter_direction( self ):
        ranked_iter= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_exclude_remote_routes( self ):
        ranked_iter= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '090', max_dist=0.6, dir='0' )
        ranked= list(ranked_iter)
        #print( ranked )
        self.assertEqual( 0, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '090', max_dist=0.6, dir='1' )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date( self ):
        ranked= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,26) )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,28) )
        self.assertEqual( 0, len(list(ranked)) )
    def test_should_filter_date_and_time( self ):
        ranked= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,26), time=(6*60+33)*60 )
        self.assertEqual( 2, len(list(ranked)) )
        ranked= caravel.transit_system.get_closest_routes_filtered( (36.85192+self.half_mile,-76.28732), '004', max_dist=0.6, date=datetime.date(2012,1,26), time=(7*60+15)*60 )
        self.assertEqual( 0, len(list(ranked)) )

class Test_Other_Queries( Sample_Transit_Data ):
    def test_should_get_route( self ):
        r = caravel.transit_system.get_route_from_stop_time( 23580 )
        self.assertEqual( '004', r[0].route_id )
        self.assertIn( '53678', r[0].trips['MR'])
    def test_should_get_all_routes( self ):
        rl = list( caravel.transit_system.get_route( ) )
        self.assertEqual( 3, len(rl) )
    def test_should_get_specific_route( self ):
        r = caravel.transit_system.get_route('090' )[0]
        trip_list = r.trips['WE']
        self.assertIn('1', trip_list)
        self.assertEqual( '090', r.route_id )
    def test_should_get_all_stops( self ):
        sl_iter = caravel.transit_system.get_stop()
        sl= list(sl_iter)
        self.assertEqual( 4, len(sl) )
    def test_should_get_specific_stop( self ):
        s = caravel.transit_system.get_stop( id='0001' )[0]
        self.assertEqual( '0001', s.stop_id )
    def test_should_get_stops_on_route( self ):
        r = caravel.transit_system.get_route_stops( '090', dir='0' )
        self.assertEqual( '090', r.route_id )
        sl= r.trips['WE']['1']['stops']
        self.assertEqual( 1, len(sl) )
        self.assertEqual( 'F001', sl[0]['stop_id'] )

        # No stops in this direction
        r = caravel.transit_system.get_route_stops( '090', dir='1' )
        self.assertEqual( '090', r.route_id )
        sl= r.trips['WE'] # No actual stuff... ['1']['stops']
        self.assertEqual( 0, len(sl) )
    def test_should_get_stops_on_date( self ):
        r = caravel.transit_system.get_route_stops( '090', date=datetime.date(2012,1,23) )
        self.assertEqual( '090', r.route_id )
        self.assertEqual( 1, len(r.trips) )
        self.assertEqual( 'F001', r.trips['WE']['1']['stops'][0]['stop_id'] )

    def test_should_get_stop_times( self ):
        s= caravel.transit_system.get_stop_times( '0001' )
        self.assertEqual( '0001', s.stop_id )
        self.assertEqual( 1, len(s.trips) )
    def test_should_get_stop_times_direction( self ):
        s= caravel.transit_system.get_stop_times( '0001', dir='0' )
        self.assertEqual( '0001', s.stop_id )
        self.assertEqual( 1, len(s.trips) )
    def test_should_get_stop_times_date( self ):
        s= caravel.transit_system.get_stop_times( '0001', date=datetime.date(2012,1,23) )
        self.assertEqual( '0001', s.stop_id )
        st_list= s.trips['MR']['53678']['times']
        self.assertEqual( 1, len(st_list) )

class Test_Next_Stop( Sample_Transit_Data ):
    def test_should_get_next_stop( self ):
        stop= list( caravel.transit_system.Stop_Definition.view('service/stop',key='0001') )[0]
        stop_time= 23580
        stops = list( caravel.transit_system.get_next_stop_time( stop, stop_time, services=['WE','MR'],  ) )
        #print( ">>> test_should_get_next_stop", stops )
        self.assertEqual( '0001', stops[0]['stop_id'])
        self.assertEqual( '0406', stops[1]['stop_id'])

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
