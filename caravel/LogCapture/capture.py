#!/usr/bin/env python2.7
"""Caravel Capture the Feed and Push into CouchDB.

Real-time feed CSV files are attached to a document with the following
attributes

::

    timestamp : year-mm-ddThh:mm:ssZ
    status    : "new", "in-process", "transformed"
    doc_type  : "Feed" -- used by couchdbkit.
    The attached file must be named "feed"

An example in JSON.

::

    {
       "doc_type" : "Feed",
       "timestamp" : "yyyy-mm-ddThh:mm:ssZ",
       "status" : "new",
       "_attachments" : {
          "feed" : {
             "content-type" : "text/csv",
             "data" : "the,csv,data\\n...",
             },
       },
    }

With curl, it's a sequence like the following.

Step 1 -- POST.

::

    curl -X POST http://username:password@hrt.iriscouch.com:5984/couchdbkit_test/ --user <user:password> -H "Content-Type: application/json" -d '{"timestamp":"2012-03-02T16:16:00Z", "status":"new", "doc_type":"Feed"}'

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

Step 2 -- PUT.

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

..  todo:: Deprecated

    The FTP interface is obsolete.

    And it needs to have argparse added so that it runs from the
    command line properly.

"""
from __future__ import print_function

import datetime
import os
import urllib2
from contextlib import closing
import sched
import time

import caravel.settings
from caravel.feed.models import Feed
import caravel.LogCapture.acquire # want URL_Positions

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

def ftp_get_and_upload(db, source_url=None):
    """Locate the current FTP file, and upload it to couchDB.
    This expects to be polling the legacy FTP server.
    """
    if source_url is None:
        source_url= caravel.LogCapture.acquire.URL_Positions
    with closing( urllib2.build_opener().open( source_url ) ) as source:
        data= source.read()
    now= datetime.datetime.now()
    name= now.strftime( "%Y%m%d%H%M.rpt")
    with open( name, 'w' ) as target:
        target.write( data )
    upload_rtf( db, name )

def ftp_polling_loop(db, source_url=None, duration=10):
    """Poll the legacy FTP server for files on a one-minute cycle.

    :param duration: number of hours to run."""
    for i in range(duration*60):
        time.sleep(60)
        ftp_get_and_upload(db, source_url )

if __name__ == "__main__":

    get_and_upload( settings.db )
