#!/usr/bin/env python2.7
"""Test Caravel Report module.
"""
from __future__ import print_function
import unittest
import logging
import sys
import datetime
import caravel.report
import json

location="07:04:42 02/15  V.1.2233  H.0.0  MT_LOCATION    Lat/Lon:370620935/-763413842 [Valid]  Adher:-1 [Valid]  Odom:2668 [Valid]  DGPS:On  FOM:2"

class Test_Parse_Good_Location( unittest.TestCase ):
    def setUp( self ):
        self.factory= caravel.report.ReportFactory()
        self.fields= tuple( f.strip() for f in location.rstrip().split() )
        self.json_enc= caravel.report.JSONEncoder()
        self.json_dec= caravel.report.JSONDecoder()

    def test_should_parse_good( self ):
        rpt= self.factory( self.fields )
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
        self.factory= caravel.report.ReportFactory()
        self.fields= tuple( f.strip() for f in trunc_location.rstrip().split() )
    def test_should_reject_bad( self ):
        rpt= self.factory( self.fields )
        self.assertIsNone( rpt )

arrival="07:04:42 02/15  V.1.2236  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:36  Arrival  Rte:4  Dir:2  TP:329  Stop:45  Svc:1  Blk:221  Lat/Lon:370315618/-763461352 [Valid]  Adher:2 [Valid]  Odom:1924 [Valid]  DGPS:On  FOM:2"

class Test_Parse_Arrive( unittest.TestCase ):
    def setUp( self ):
        self.factory= caravel.report.ReportFactory()
        self.fields= tuple( f.strip() for f in arrival.rstrip().split() )
        self.json_enc= caravel.report.JSONEncoder()
        self.json_dec= caravel.report.JSONDecoder()
    def test_should_parse( self ):
        rpt= self.factory( self.fields )
        self.assertEqual( datetime.datetime(2012,2,15,7,4,42), rpt.timestamp )
        self.assertEqual( '2236', rpt.id )
        self.assertAlmostEqual( 37.0315618, rpt.lat )
        self.assertAlmostEqual( -76.3461352, rpt.lon )
        self.assertEqual( 4, rpt.rte )
        self.assertIsNone( rpt.dwell )
        self.assertEqual( 2, rpt.dir )
        self.assertEqual( 45, rpt.stop )
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
        self.factory= caravel.report.ReportFactory()
        self.fields= tuple( f.strip() for f in dwell.rstrip().split() )
        self.json_enc= caravel.report.JSONEncoder()
        self.json_dec= caravel.report.JSONDecoder()
    def test_should_parse( self ):
        rpt= self.factory( self.fields )
        self.assertEqual( datetime.datetime(2012,2,15,7,4,42), rpt.timestamp )
        self.assertEqual( '3515', rpt.id )
        self.assertAlmostEqual( 37.0425333, rpt.lat )
        self.assertAlmostEqual( -76.4286136, rpt.lon )
        self.assertEqual( 65, rpt.rte )
        self.assertEqual( 22, rpt.dwell )
        self.assertEqual( 2, rpt.dir )
        self.assertEqual( 69, rpt.stop )
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

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr )
    unittest.main()