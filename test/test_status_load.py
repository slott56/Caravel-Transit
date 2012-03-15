#!/usr/bin/env python2.7
"""Test Caravel couchdb interfaces for status class instances
and the status_load functions.

Requires couchdb be running.  Does **not** start it automatically.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import datetime
import csv
import StringIO
from collections import namedtuple
from couchdbkit import Server
from caravel.status.models import Route, RouteStop, Stop, Vehicle
from caravel.report import Arrival, Location
from caravel.status.status_load import update_route, update_route_stop, update_stop, update_vehicle
from caravel.status.status_load import track_arrival, track_location, old_status_removal
from couchdbkit.designer import push
from couchdbkit.exceptions import ResourceNotFound

def setUpModule():
    global connection, db
    connection = Server()
    db = connection.get_or_create_db('couchdbkit_test')
    push('_design/status', db)

def tearDownModule():
    global connection
    del connection['couchdbkit_test']

class Test_Should_Handle_Arrival( unittest.TestCase ):
    def setUp( self ):
        global db

        self.loc= Location(
            timestamp= datetime.datetime.now(),
            id= '1.1.1234',
            lat= 36.0,
            lon= -76.0,
        )
        self.arr= Arrival(
            timestamp= datetime.datetime.now(),
            id= '1.1.2345',
            lat= 36.1,
            lon= -76.2,
            time= 25678,
            rte= '1',
            dir= '2',
            stop= '3',
        )

        Route.set_db(db)
        RouteStop.set_db(db)
        Stop.set_db(db)
        Vehicle.set_db(db)

    def tearDown( self ):
        global db
        for r in Route.view('status/route'):
            db.delete_doc(r)
        for rs in RouteStop.view('status/routestop'):
            db.delete_doc( rs )
        for s in Stop.view('status/stop'):
            db.delete_doc( s )
        for v in Vehicle.view('status/vehicle'):
            db.delete_doc( v )

    def confirm( self ):
        r1= Route.get( '005-Outbound' )
        #print( r1 )
        self.assertEqual( datetime.date(2012,3,15), r1.date )
        self.assertEqual( '005', r1.route )
        self.assertEqual( 'Outbound', r1.direction )
        self.assertEqual( 1, len(r1.history))

        update_route_stop( self.arr )
        rs1 = RouteStop.get( '005-Outbound-0007')
        #print( rs1 )
        self.assertEqual( datetime.date(2012,3,15), rs1.date )
        self.assertEqual( '005', rs1.route )
        self.assertEqual( 'Outbound', rs1.direction )
        self.assertEqual( '0007', rs1.stop )
        self.assertEqual( 1, len(rs1.history))

        update_stop( self.arr )
        s1= Stop.get( '0007' )
        #print( s1 )
        self.assertEqual( datetime.date(2012,3,15), s1.date )
        self.assertEqual( '0007', s1.stop )
        self.assertEqual( 1, len(s1.history))

        update_vehicle( self.arr )
        v1= Vehicle.get( '5011' )
        #print( v1 )
        self.assertEqual( datetime.date(2012,3,15), v1.date )
        self.assertEqual( '5011', v1.vehicle )

    def test_should_update_status( self ):
        global db
        self.arr.route= '005'
        self.arr.direction= 'Outbound'
        self.arr.stop= '0007'
        self.arr.vehicle= '5011'
        update_route( self.arr )
        self.confirm()

    def test_should_track( self ):
        global db
        Handler= namedtuple( 'Handler', ['map'] )
        mappings = {
            'route': Handler( { '1': '005' } ),
            'stop': Handler( { '3': '0007' } ),
            'vehicle': Handler( { '2345': '5011' } ),
        }
        track_arrival( mappings, self.arr )
        self.confirm()

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
