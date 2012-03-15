#!/usr/bin/env python2.7
"""Test Caravel couchdb interfaces for feed class instances
and the feed_load functions.

Requires couchdb be running.  Does **not** start it automatically.
"""
from __future__ import print_function, division
import unittest
import logging
import sys
import datetime
import csv
import StringIO
from couchdbkit import Server
from caravel.feed.models import Feed
from caravel.feed.feed_load import remove_damaged, remove_old, transform_new, new_feed_iter, validate_and_open
from couchdbkit.designer import push
from couchdbkit.exceptions import ResourceNotFound

def setUpModule():
    global connection, db
    connection = Server()
    db = connection.get_or_create_db('couchdbkit_test')
    push('_design/feed', db)

def tearDownModule():
    global connection
    del connection['couchdbkit_test']

class Test_Damaged_Feed_Doc(unittest.TestCase ):
    def setUp( self ):
        global db
        # Remove any left-over feeds
        for f in db.view("feed/all"):
            db.delete_doc( f['id'] )
        # Create a doc_type = "Feed", but otherwise damaged.
        db.save_doc( dict(
            doc_type= 'Feed',
            timestamp= '5-ish', )
                    )
    def test_should_remove_damaged( self ):
        self.assertEqual( 1, len( list( db.view("feed/all")) ) )
        remove_damaged( db, db.view("feed/all") )
        self.assertEqual( 0, len( list( db.view("feed/all")) ) )

class FeedPushTest( unittest.TestCase ):
    def push_feed( self, timestamp, status='new', feed_file=None ):
        global db
        Feed.set_db(db)
        feed= Feed(
            timestamp= timestamp,
            status= status,
        )
        db.save_doc( feed )
        if feed_file is not None:
            feed.put_attachment( feed_file, name="feed", content_type="text/csv" )
        return feed
    def remove_old( self ):
        global db
        # Remove any left-over feeds
        for f in db.view("feed/all"):
            db.delete_doc( f['id'] )

class Test_Remove_Old_Feed_Docs( FeedPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a new feed
        feed = StringIO.StringIO( "Invalid,Column,Names\n23,29\n31,37\n")
        self.push_feed( datetime.datetime(2012,3,15,7,8,9), 'erroneous', feed )
    def test_should_remove_old( self ):
        global db
        feeds = list( Feed.view("feed/old") )
        self.assertEqual( 1, len(feeds) )
        remove_old( db, today = datetime.date(2012,3,16) )
        feeds = list( Feed.view("feed/old") )
        self.assertEqual( 0, len(feeds) )

class Test_Bad_Feed_Doc( FeedPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a bad feed
        feed = StringIO.StringIO( "Invalid,Column,Names\n23,29\n31,37\n")
        self.push_feed( datetime.datetime(2012,3,15,7,8,9), 'new', feed )
    def test_should_see_bad_attachment( self ):
        global db
        feeds1 = list( Feed.view("feed/new") )
        self.assertEqual( 1, len(feeds1) )
        feeds2 = list( new_feed_iter() )
        self.assertEqual( 1, len(feeds2) )
        f, rdr= validate_and_open( feeds2[0] )
        self.assertIsNone( rdr )
        self.assertEquals( "wrong format attachment", f.status )

class Test_Good_Feed_Doc( FeedPushTest ):
    def setUp( self ):
        global db
        self.remove_old()
        # Push a good feed
        self.feed_headings = [
            "Date", "Time", "Vehicle", "Lat", "Lon", "Location Valid/Invalid",
            "Adherence", "Adherence Valid/Invalid", "Route", "Direction", "Stop"
        ]
        feed = StringIO.StringIO()
        wtr= csv.writer( feed )
        wtr.writerow(self.feed_headings)
        wtr.writerow( ["2012-03-15","02:03:04","123","36.12345","-76.23456", "V", "-1", "V", "2", "3", "5"] )
        self.push_feed( datetime.datetime(2012,3,15,7,8,9), 'new', feed )
    def test_should_open_and_read_feed( self ):
        global db
        feeds2 = list( new_feed_iter() )
        self.assertEqual( 1, len(feeds2) )
        f, rdr= validate_and_open( feeds2[0] )
        self.assertEqual( self.feed_headings, rdr.source.fieldnames )
        data = list( rdr )
        self.assertEqual( 1, len(data) )
        #print( data[0] )
        self.assertEqual( datetime.datetime(2012,3,15,2,3,4), data[0].timestamp )
        self.assertEqual( '123', data[0].id )
        self.assertAlmostEqual( 36.12345, data[0].lat )
        self.assertAlmostEqual( -76.23456, data[0].lon )
        self.assertEqual( "V", data[0].ll_valid )
        self.assertEqual( -1, data[0].adher )
        self.assertEqual( "V", data[0].adher_valid )
        self.assertEqual( "2", data[0].rte )
        self.assertEqual( "3", data[0].dir )
        self.assertEqual( "5", data[0].stop )
    def test_should_process_feed( self ):
        arrivals = []
        def track_arrival( mappings, report ):
            arrivals.append( report )
        locations = []
        def track_location( mappings, report ):
            locations.append( report )
        mappings = {}
        counts= transform_new(
            mappings, new_feed_iter(),
            track_arrival, track_location,
            today=datetime.date(2012,3,15) )
        self.assertEqual( 1, counts['all'] )
        self.assertEqual( 1, counts['arrival'] )
        self.assertEqual( 0, counts['location'] )
        self.assertEqual( 1, len(arrivals) )
        self.assertEqual( 0, len(locations) )
        feeds2 = list( new_feed_iter() )
        self.assertEqual( 0, len(feeds2) )
        old = list( Feed.view('feed/old') )
        self.assertEqual( 1, len(old) )
        self.assertEqual( "processed", old[0].status )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()
