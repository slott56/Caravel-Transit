#!/usr/bin/env python2.7
"""Test Caravel couchdb interfaces for report class instances.

Requires couchdb be running.  Does **not** start it automatically.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import datetime
from couchdbkit import Server
from caravel.report import Arrival, Dwell, Location

def setUpModule():
    global connection, db
    connection = Server()
    db = connection.get_or_create_db('couchdbkit_test')

def tearDownModule():
    global connection
    del connection['couchdbkit_test']

class Test_Sanity( unittest.TestCase ):
    def setUp( self ):
        self.doc= { 'string': 'test', 'number': 4 }
    def test_api_should_crud( self ):
        global db
        db.save_doc(self.doc)
        docid = self.doc['_id']
        doc2 = db.get(docid)
        self.assertEqual( self.doc['string'], doc2['string'] )
        self.assertEqual( self.doc['number'], doc2['number'] )
        del db[docid]
        self.assertFalse( docid in db )

class Test_Persist_Location( unittest.TestCase ):
    def setUp( self ):
        self.loc= Location(
            timestamp= datetime.datetime.now(),
            id= '1234',
            lat= 36.0,
            lon= -76.0,
        )
        self.arr= Arrival(
            timestamp= datetime.datetime.now(),
            id= '2345',
            lat= 36.1,
            lon= -76.2,
            time= 25678,
            rte= '1',
            dir= '2',
            stop= '3',
        )
    def test_should_crud_location( self ):
        global db
        loc_id= db.save_doc(self.loc)
        self.assertEqual( loc_id['id'], self.loc._id )
        loc2= db.get( self.loc._id ) # JSON
        self.assertEqual( self.loc.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"), loc2['timestamp'] )
        loc3= Location.get( self.loc._id, db=db ) # Location class.
        self.assertEqual( repr(self.loc), repr(loc3) )
    def test_should_crud_arrival( self ):
        global db
        arr_id= db.save_doc(self.arr)
        self.assertEqual( arr_id['id'], self.arr._id )
        arr2= Arrival.get( self.arr._id, db=db ) # Arrival class.
        self.assertEqual( repr(self.arr), repr(arr2) )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
