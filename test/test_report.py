#!/usr/bin/env python2.7
"""Test Caravel Report module.
"""
from __future__ import print_function
import unittest
import logging
import sys
import datetime
import json
import StringIO
import caravel.report

location="07:04:42 02/15  V.1.2233  H.0.0  MT_LOCATION    Lat/Lon:370620935/-763413842 [Valid]  Adher:-1 [Valid]  Odom:2668 [Valid]  DGPS:On  FOM:2"

class Test_Parse_Good_Location( unittest.TestCase ):
    def setUp( self ):
        self.reader= caravel.report.ReportReader_v1()
        self.json_enc= caravel.report.JSONEncoder()
        self.json_dec= caravel.report.JSONDecoder()

    def test_should_parse_good( self ):
        rpt= self.reader.factory( location )
        self.assertEqual( datetime.datetime(2012,2,15,7,4,42), rpt.timestamp )
        self.assertEqual( '2233', rpt.id )
        self.assertAlmostEqual( 37.0620935, rpt.lat )
        self.assertAlmostEqual( -76.3413842, rpt.lon )
        self.assertIsNone( rpt.rte )
        self.assertIsNone( rpt.dwell )
        txt= self.json_enc.encode(rpt)
        ##print( txt )
        obj= self.json_dec.decode( txt )
        self.assertEqual( rpt.lat, obj.lat )
        self.assertEqual( rpt.lon, obj.lon )
        self.assertEqual( rpt.timestamp, obj.timestamp )

trunc_location="09:32:04 02/15  V.1.3505  H.0.0  MT_LOCATION    Lat/Lon:368652212/-762994236 [Valid]  Adher:-2 [Valid]  Odom:4869 [Invalid]  DGPS:On"

class Test_Parse_Bad_Location( unittest.TestCase ):
    def setUp( self ):
        self.reader= caravel.report.ReportReader_v1()
        self.fields= trunc_location.rstrip().split()
    def test_should_reject_bad( self ):
        rpt= self.reader.factory( self.fields )
        self.assertIsNone( rpt )

arrival="07:04:42 02/15  V.1.2236  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:36  Arrival  Rte:4  Dir:2  TP:329  Stop:45  Svc:1  Blk:221  Lat/Lon:370315618/-763461352 [Valid]  Adher:2 [Valid]  Odom:1924 [Valid]  DGPS:On  FOM:2"

class Test_Parse_Arrive( unittest.TestCase ):
    def setUp( self ):
        self.reader= caravel.report.ReportReader_v1()
        self.json_enc= caravel.report.JSONEncoder()
        self.json_dec= caravel.report.JSONDecoder()
    def test_should_parse( self ):
        rpt= self.reader.factory( arrival )
        self.assertEqual( datetime.datetime(2012,2,15,7,4,42), rpt.timestamp )
        self.assertEqual( '2236', rpt.id )
        self.assertAlmostEqual( 37.0315618, rpt.lat )
        self.assertAlmostEqual( -76.3461352, rpt.lon )
        self.assertEqual( '4', rpt.rte )
        self.assertIsNone( rpt.dwell )
        self.assertEqual( 2, rpt.dir )
        self.assertEqual( '45', rpt.stop )
        txt= self.json_enc.encode(rpt)
        ##print( txt )
        obj= self.json_dec.decode( txt )
        self.assertEqual( rpt.lat, obj.lat )
        self.assertEqual( rpt.lon, obj.lon )
        self.assertEqual( rpt.timestamp, obj.timestamp )
        self.assertEqual( rpt.rte, obj.rte )
        self.assertEqual( rpt.dir, obj.dir)
        self.assertEqual( rpt.stop, obj.stop )
        self.assertIsNone( obj.dwell )

dwell="07:04:42 02/15  V.1.3515  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:37  Dwell:22  Rte:65  Dir:2  TP:352  Stop:69  Svc:1  Blk:203  Lat/Lon:370425333/-764286136 [Valid]  Adher:-1 [Valid]  Odom:1712 [Valid]  DGPS:On  FOM:2"

class Test_Parse_Dwell( unittest.TestCase ):
    def setUp( self ):
        self.reader= caravel.report.ReportReader_v1()
        self.json_enc= caravel.report.JSONEncoder()
        self.json_dec= caravel.report.JSONDecoder()
    def test_should_parse( self ):
        rpt= self.reader.factory( dwell )
        self.assertEqual( datetime.datetime(2012,2,15,7,4,42), rpt.timestamp )
        self.assertEqual( '3515', rpt.id )
        self.assertAlmostEqual( 37.0425333, rpt.lat )
        self.assertAlmostEqual( -76.4286136, rpt.lon )
        self.assertEqual( '65', rpt.rte )
        self.assertEqual( 22, rpt.dwell )
        self.assertEqual( 2, rpt.dir )
        self.assertEqual( '69', rpt.stop )
        txt= self.json_enc.encode(rpt)
        ##print(rpt.as_dict())
        ##print( txt )
        obj= self.json_dec.decode( txt )
        self.assertEqual( rpt.lat, obj.lat )
        self.assertEqual( rpt.lon, obj.lon )
        self.assertEqual( rpt.timestamp, obj.timestamp )
        self.assertEqual( rpt.rte, obj.rte )
        self.assertEqual( rpt.dir, obj.dir)
        self.assertEqual( rpt.stop, obj.stop )
        self.assertEqual( rpt.dwell, obj.dwell )

class TestIterable_V1( unittest.TestCase ):
    def setUp( self ):
        self.reader= caravel.report.ReportReader_v1()
        self.text= "\n".join( (location, arrival, dwell, '') )
    def test_should_iterate( self ):
        file_like_object= StringIO.StringIO( self.text )
        self.reader.open(file_like_object,year=2012)
        rpts = list( self.reader )
        self.assertAlmostEqual( 37.0620935, rpts[0].lat )
        self.assertAlmostEqual( -76.3413842, rpts[0].lon )
        self.assertAlmostEqual( 37.0315618, rpts[1].lat )
        self.assertAlmostEqual( -76.3461352, rpts[1].lon )
        self.assertAlmostEqual( 37.0425333, rpts[2].lat )
        self.assertAlmostEqual( -76.4286136, rpts[2].lon )

class TestIterable_V2( unittest.TestCase ):
    def setUp( self ):
        self.reader= caravel.report.ReportReader_v2()
        self.text= """\
Time,Date,RID,Lat/Lon,Location Valid/Invalid,Adherence,Adherence Valid/Invalid[,Route,Direction,StopID]
07:00:38,02/28,3247,368147270/-762487811,V,-1,V
07:00:38,02/28,2129,368160471/-760704451,V,0,I
07:00:41,02/28,2109,368099480/-763510804,V,-1,V,28,1,30
"""
    def test_should_iterate( self ):
        file_like_object= StringIO.StringIO( self.text )
        self.reader.open(file_like_object, year=2012)
        rpts = list( self.reader )
        self.assertAlmostEqual( 36.8147270, rpts[0].lat )
        self.assertAlmostEqual( -76.2487811, rpts[0].lon )
        self.assertEqual( None, rpts[0].time )
        self.assertAlmostEqual( 36.8160471, rpts[1].lat )
        self.assertAlmostEqual( -76.0704451, rpts[1].lon )
        self.assertEqual( None, rpts[1].time )
        self.assertAlmostEqual( 36.8099480, rpts[2].lat )
        self.assertAlmostEqual( -76.3510804, rpts[2].lon )
        self.assertEqual( 25241, rpts[2].time )

class TeestAbstractSuperclass( unittest.TestCase ):
    def test_should_not_instantiate( self ):
        self.assertRaisesRegexp( TypeError, "Can't instantiate abstract class ReportReader with abstract methods.*", caravel.report.ReportReader, () )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.FATAL )
    unittest.main()