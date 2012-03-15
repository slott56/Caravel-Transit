#!/usr/bin/env python2.7
"""Test Caravel couchdb interfaces for mapping class instances
and the mapping_load functions.

Requires couchdb be running.  Does **not** start it automatically.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import datetime
import StringIO
from couchdbkit import Server
from caravel.feed.models import Mapping
from caravel.feed.mapping_load import validate, mapping_attachment, Invalid_Mapping, validate_new
from caravel.feed.mapping_load import Vehicle_Attachment, assemble_timeline, fetch_current, refresh_mapping_cache
from couchdbkit.designer import push
from couchdbkit.exceptions import ResourceNotFound

def setUpModule():
    global connection, db
    connection = Server()
    db = connection.get_or_create_db('couchdbkit_test')
    push('_design/mapping', db)

def tearDownModule():
    global connection
    del connection['couchdbkit_test']

class MappingPushTest( unittest.TestCase ):
    def push_mapping( self, mapping_type, effective_date, timestamp, content_file ):
        global db
        Mapping.set_db(db)
        mapping= Mapping(
            timestamp= timestamp,
            mapping_type= mapping_type,
            effective_date= effective_date,
        )
        db.save_doc( mapping )
        if content_file is not None:
            mapping.put_attachment( content_file, name="content", content_type="text/csv" )
        return mapping
    def remove_old( self ):
        global db
        # Remove any left-over mappings
        for m in db.view("mapping/all"):
            db.delete_doc( m['id'] )

class Test_Bad_Mapping_Handlers( MappingPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a new vehicle mapping
        vehicle = StringIO.StringIO( "Invalid,Column,Names\n23,29\n31,37\n")
        self.push_mapping( "vehicle", datetime.date(2012,3,16), datetime.datetime(2012,3,15,7,8,9), vehicle )
    def test_handler_see_bad_attachment( self ):
        global db
        mappings = list( Mapping.view("mapping/new") )
        self.assertEqual( 1, len(mappings) )
        handler= mapping_attachment(mappings[0])
        self.assertEqual( set(["Invalid","Column","Names"]), set(handler.reader.fieldnames) )
        self.assertFalse( set( (Vehicle_Attachment.source_name, Vehicle_Attachment.gtf_name) ) <= set(handler.reader.fieldnames) )

class BadMappingTest( MappingPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a new route, stop and vehicle mapping
        self.push_mapping( "route", datetime.date(2012,3,16), datetime.datetime(2012,3,15,1,2,3), None )
        stop = StringIO.StringIO( "sid,Stop\n11,13\n17,19\n")
        self.push_mapping( "invalid_type", datetime.date(2012,3,16), datetime.datetime(2012,3,15,4,5,6), stop )
        vehicle = StringIO.StringIO( "Invalid,Column,Names\n23,29\n31,37\n")
        self.push_mapping( "vehicle", datetime.date(2012,3,16), datetime.datetime(2012,3,15,7,8,9), vehicle )

class Test_Bad_Mapping_Validation( BadMappingTest ):
    def test_should_see_invalid_mappings( self ):
        global db
        mappings = list( Mapping.view("mapping/new") )
        self.assertEqual( 3, len(mappings) )
        try:
            self.assertFalse( validate( mappings[0] ) )
            self.fail( "Did not raise exception" )
        except ResourceNotFound as ex:
            self.assertEqual( "Document is missing attachment", ex.message )
        try:
            self.assertFalse( validate( mappings[1] ) )
            self.fail( "Did not raise exception" )
        except Invalid_Mapping as ex:
            self.assertEqual( 'unknown type: invalid_type', ex.message )
        try:
            self.assertFalse( validate( mappings[2] ) )
            self.fail( "Did not raise exception" )
        except Invalid_Mapping as ex:
            self.assertEqual( "bad columns: ('vid', 'bus') not in ['Invalid', 'Column', 'Names']", ex.message )

class Test_Duplicate_Mapping_Validation( MappingPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a new route, stop and vehicle mapping
        route = StringIO.StringIO( "rid,Route\n2,3\n5,7\n")
        self.push_mapping( "route", datetime.date(2012,3,16), datetime.datetime(2012,3,15,1,2,3), route )
        self.push_mapping( "route", datetime.date(2012,3,16), datetime.datetime(2012,3,15,1,2,3), route )
    def test_should_see_duplicate( self ):
        global db
        mappings = list( Mapping.view("mapping/new") )
        self.assertEqual( 2, len(mappings) )
        self.assertTrue( validate(mappings[0]) )
        mappings[0].status= 'valid'
        mappings[0].save()
        try:
            self.assertFalse( validate( mappings[1] ) )
            self.fail( "Did not raise exception" )
        except Invalid_Mapping as ex:
            self.assertEqual( "duplicate type and effective date", ex.message )

class GoodMappingTest( MappingPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a new route, stop and vehicle mapping
        route = StringIO.StringIO( "rid,Route\n2,3\n5,7\n")
        self.push_mapping( "route", datetime.date(2012,3,16), datetime.datetime(2012,3,15,1,2,3), route )
        stop = StringIO.StringIO( "sid,Stop\n11,13\n17,19\n")
        self.push_mapping( "stop", datetime.date(2012,3,16), datetime.datetime(2012,3,15,4,5,6), stop )
        vehicle = StringIO.StringIO( "vid,bus\n23,29\n31,37\n")
        self.push_mapping( "vehicle", datetime.date(2012,3,16), datetime.datetime(2012,3,15,7,8,9), vehicle )

class Test_Bad_Mapping_Status( BadMappingTest ):
    def test_should_mark_invalid( self ):
        response= validate_new( Mapping.view('mapping/new', descending=True) )
        self.assertEqual( 0, len( response ) )
        status= set( m.status for m in Mapping.view('mapping/all', descending=True) )
        expected = set( [u"bad columns: ('vid', 'bus') not in ['Invalid', 'Column', 'Names']", None, u'unknown type: invalid_type'] )
        self.assertEqual( expected, status )

class Test_Good_Mapping_Status( GoodMappingTest ):
    def test_should_see_valid( self ):
        global db
        mappings = list( Mapping.view("mapping/new") )
        self.assertEqual( 3, len(mappings) )
        self.assertEqual( "route", mappings[0].mapping_type )
        self.assertTrue( validate(mappings[0]) )
        self.assertEqual( "stop", mappings[1].mapping_type )
        self.assertTrue( validate(mappings[1]) )
        self.assertEqual( "vehicle", mappings[2].mapping_type )
        self.assertTrue( validate(mappings[2]) )
    def test_should_mark_valid( self ):
        response= validate_new( Mapping.view('mapping/new', descending=True) )
        self.assertEqual( 3, len( response ) )
        self.assertEqual( 1, len( response['route'] ) )
        self.assertEqual( 1, len( response['stop'] ) )
        self.assertEqual( 1, len( response['vehicle'] ) )
        status= set( m.status for m in Mapping.view('mapping/all', descending=True) )
        self.assertEqual( set(['valid']), status )

class Test_Good_Mapping_Timeline_And_Fetch( MappingPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push route mappings
        route1 = StringIO.StringIO( "rid,Route\n2,1\n5,7\n")
        self.push_mapping( "route", datetime.date(2012,4,1), datetime.datetime(2012,3,15,1,1,1), route1 )
        route3 = StringIO.StringIO( "rid,Route\n2,3\n5,13\n")
        self.push_mapping( "route", datetime.date(2012,4,3), datetime.datetime(2012,3,15,3,3,3), route3 )
        route2 = StringIO.StringIO( "rid,Route\n2,2\n5,17\n")
        self.push_mapping( "route", datetime.date(2012,4,2), datetime.datetime(2012,3,15,2,2,2), route2 )
    def test_should_mark_date_ranges_and_fetch( self ):
        response1= validate_new( Mapping.view('mapping/new', descending=True) )
        self.assertEqual( 3, len( response1['route'] ) )
        status= set( m.status for m in Mapping.view('mapping/all', descending=True) )
        self.assertEqual( set(['valid']), status )
        response2= assemble_timeline( 'route' )
        self.assertEqual( 3, len( response2 ) )
        self.assertEqual( datetime.date(2012,4,1), response2[0].effective_date )
        self.assertEqual( response2[0].ending_date, response2[1].effective_date )
        self.assertEqual( response2[1].ending_date, response2[2].effective_date )
        self.assertEqual( 2200, response2[2].ending_date.year )
        response3= fetch_current( 'route', datetime.date(2012,4,2) )
        self.assertTrue( response3.effective_date <=  datetime.date(2012,4,2) < response3.ending_date)
        response4= fetch_current( 'route', datetime.date(2012,3,15) )
        self.assertIsNone( response4 )
    def test_should_set_mappings( self ):
        cache= {}
        mappings = refresh_mapping_cache( cache, Mapping.view('mapping/new', descending=True), today=datetime.date(2012,4,2) )
        self.assertNotIn( 'vehicle', mappings )
        self.assertNotIn( 'stop', mappings )
        self.assertIn( 'route', mappings )
        self.assertEqual( cache, mappings )
        expected= {'2': '2', '5': '17'} # route 2 on the
        self.assertEqual( expected, mappings['route'].map )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
