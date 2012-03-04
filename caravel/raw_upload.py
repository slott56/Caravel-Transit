#!/usr/bin/env python2.7
"""Caravel Raw File Upload.

Push HRT data to HRT CouchDB.  This includes methods for real-time extract
and also includes the various mappings that may be required.

Real-time feed CSV files are attached to a document with the following
attributes

    timestamp : year-mm-ddThh:mm:ssZ
    status    : "new", "in-process", "transformed"
    feed      : the file

Other mapping CSV files are attached to a document with the following
attributes

    timestamp      : year-mm-ddThh:mm:ssZ
    effective_date : year
    mapping_type   : vehicle, route or stop
    content        : the file

::

    {
       "doc_type" : "Feed",
       "timestamp" : "yyyy-mm-ddThh:mm:ssZ",
       "status" : "new",
       "_attachments" : {
          "feed" : {
             "content-type" : "text/csv",
             "data" : "the,csv,data\n...",
             },
       },
    }

With curl, it's a sequence like the following

::

    curl -X POST http://username:password@hrt.iriscouch.com:5984/couchdbkit_test/ --user <user:password> -H "Content-Type: application/json" -d '{"timestamp":"2012-03-02T16:16:00Z", "status":"new", "doc_type":"Feed"}'

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

::

    curl -X PUT http://hrt.iriscouch.com:5984/couchdbkit_test/09833a88a1cbb06f64c555d0245f1af3/feed/?rev=1-7750ef2dbce77303f957de17c754852a --user <user:password> -H "Content-Type: text/csv" @201203022302.rpt

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"2-748151ff136b0001671fb0fa14eb886d"}

Checking for new feeds is this

::

    curl http://hrt.iriscouch.com:5984/couchdbkit_test/_design/feed/_view/new

Response is a JSON document like this::

    {"total_rows":2,"offset":0,"rows":[
    {"id":"09833a88a1cbb06f64c555d0245f1af3","key":"09833a88a1cbb06f64c555d0245f1af3","value":null},
    {"id":"09833a88a1cbb06f64c555d0245f1d98","key":"09833a88a1cbb06f64c555d0245f1d98","value":null}
    ]}

Individual documents are available::

    curl http://username:password@hrt.iriscouch.com:5984/couchdbkit_test/09833a88a1cbb06f64c555d0245f1af3/feed/

"""
from __future__ import print_function
from couchdbkit import Server
from couchdbkit import Document, ResourceNotFound
from couchdbkit import schema
from couchdbkit.designer import push

import datetime
import os
import urllib2
from contextlib import closing
import sched
import time

test= True
if test:
    database_uri= "http://127.0.0.1:5984/"
    database_name= 'couchdbkit_test'
    URL_Positions = "ftp://216.54.15.3/Anrd/hrtrtf.txt"
else:
    database_uri= "http://http://hrt.iriscouch.com:5984/"
    database_name= 'release_1'
    URL_Positions = "ftp://216.54.15.3/Anrd/hrtrtf.txt"

connection = Server(database_uri)
db = connection.get_or_create_db(database_name)

def define_views( db ):
    """Purely administrative.  Done once (or so) to set the views.

    Similar to the way that couchapp works.

    https://github.com/couchapp/couchapp/tree/
    """
    push('_design/feed', db)
    push('_design/mapping', db)

class Feed( Document ):
    """A Feed file; the "feed" attachment is the raw CSV feed data."""
    timestamp= schema.DateTimeProperty()
    status= schema.StringProperty() # initially "new"
    def __repr__( self ):
        return "Feed( timestamp={0:s}, status={1:s} )".format( self.timestamp.strftime("%x %X"), self.status )

class Mapping( Document ):
    """A Mapping file; the "content" attachment is the raw CSV mapping data."""
    timestamp= schema.DateTimeProperty()
    effective_date= schema.DateProperty()
    mapping_type= schema.StringProperty()

def upload_rtf( db, filename ):
    """Upload the Real-Time Feed from a given filename.

    The following sequence of curl requests have the same effect.

    ::

        curl -X POST http://localhost:5984/couchdbkit_test/ -H "Content-Type: application/json" -d '{"timestamp":"2012-03-02T16:16:00Z", "status":"new", "doc_type":"Feed"}'

    The response is::

        {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

    ::

        curl -X PUT http://localhost:5984/couchdbkit_test/09833a88a1cbb06f64c555d0245f1af3/feed/?rev=1-7750ef2dbce77303f957de17c754852a -H "Content-Type: text/csv" --data-ascii @201203022302.rpt

    The response is::

        {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"2-748151ff136b0001671fb0fa14eb886d"}
    """
    Feed.set_db(db)
    feed = Feed(
        timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
        status = "new",
    )
    feed.save()
    with open(filename,'r') as source:
        feed.put_attachment( source, name="feed", content_type="text/csv" )
    print( feed, feed._id )

def all_rtf( db ):
    """Query all real-time Feed uploads."""
    Feed.set_db(db)
    for f in Feed.view('feed/all'):
        try:
            att= f.fetch_attachment( name="feed", stream=False )
        except ResourceNotFound:
            att= None
        print( f, att )

#    for obj in db.temp_view( """
#{ "map" : "function(doc){ if(doc.doc_type=='Feed') { emit(doc._id, null )} }"
#}
#"""):

def upload_mapping( db, mapping_type, effective_date, filename ):
    """Upload a specific mapping file with a given effective date.

    The effective date must be a datetime.date object.
    """
    Mapping.set_db(db)
    mapping= Mapping(
        timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
        effective_date= effective_date,
        mapping_type= mapping_type,
    )
    mapping.save()
    mapping.put_attachment( filename, name="content", content_type="text/csv" )

def all_mapping( db ):
    """Locate all mappings in the database."""
    Mapping.set_db(db)
    for m in Mapping.view('mapping/all'):
        print( m )

def get_and_upload(db):
    """Locate the current FTP file, and upload it to couchDB."""
    with closing( urllib2.build_opener().open( URL_Positions ) ) as source:
        data= source.read()
    now= datetime.datetime.now()
    name= now.strftime( "%Y%m%d%H%M.rpt")
    with open( name, 'w' ) as target:
        target.write( data )
    upload_rtf( db, name )

def polling_loop(db, duration=12):
    """Poll for files on a one-minute cycle.

    :param duration: number of hours to run."""
    for i in range(duration*60):
        time.sleep(60)
        get_and_upload(db)

if __name__ == "__main__":

    define_views( db )
    get_and_upload( db )
    all_rtf( db )