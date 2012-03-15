#!/usr/bin/env python2.7
"""Caravel Push a Mapping.

Push Mapping data to HRT CouchDB.

A mapping file must be CSV format (with well-defined headings.
They are attached to a document with the following
attributes

::

    timestamp      : year-mm-ddThh:mm:ssZ
    effective_date : year-mm-dd
    mapping_type   : vehicle, route or stop
    doc_type       : "Mapping" -- used by couchdbkit.
    content        : the file

Example JSON document

::

    {
       "doc_type" : "Mapping",
       "timestamp" : "yyyy-mm-ddThh:mm:ssZ",
       "effective_date" : "yyyy-mm-dd",
       "mapping_type" : "vehicle",
       "status" : "new",
       "_attachments" : {
          "content" : {
             "content-type" : "text/csv",
             "data" : "the,csv,data\\n...",
             },
       },
    }

With curl, it's a sequence like the following

::

    curl -X POST http://username:password@hrt.iriscouch.com:5984/couchdbkit_test/
    --user <user:password>
    -H "Content-Type: application/json"
    -d '{"timestamp":"2012-03-02T16:16:00Z", "mapping_type":"vehicle", "effective_date": "2012-03-03", "doc_type":"Mapping"}'

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

::

    curl -X PUT http://hrt.iriscouch.com:5984/couchdbkit_test/09833a88a1cbb06f64c555d0245f1af3/content/?rev=1-7750ef2dbce77303f957de17c754852a
    --user <user:password>
    -H "Content-Type: text/csv" @new_vehicle_mapping.csv

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"2-748151ff136b0001671fb0fa14eb886d"}

Checking for new feeds is this

::

    curl http://hrt.iriscouch.com:5984/couchdbkit_test/_design/mapping/_view/new

Response is a JSON document like this::

    {"total_rows":2,"offset":0,"rows":[
    {"id":"09833a88a1cbb06f64c555d0245f1af3","key":"09833a88a1cbb06f64c555d0245f1af3","value":null},
    {"id":"09833a88a1cbb06f64c555d0245f1d98","key":"09833a88a1cbb06f64c555d0245f1d98","value":null}
    ]}

Individual documents are available::

    curl http://username:password@hrt.iriscouch.com:5984/couchdbkit_test/09833a88a1cbb06f64c555d0245f1af3/content/

"""
from __future__ import print_function

import datetime
import os
import urllib2
from contextlib import closing
import sched
import time

import caravel.settings
from caravel.feed.models import Mapping

def upload_mapping( db, mapping_type, effective_date, filename ):
    """Upload a specific mapping file with a given effective date.

    The effective date must be a datetime.date object.

    :param db: The database
    :param mapping_type: "vehicle", "route" or "stop" mapping type
    :param effective_date: datetime.date at which this mapping becomes effective.
        Mappings remain effective until a mapping with a later effective date
        is pushed and validated.
    :param filename: a file to read and push.
    """
    Mapping.set_db(db)
    mapping= Mapping(
        timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
        effective_date= effective_date,
        mapping_type= mapping_type,
    )
    db.save_doc( mapping )
    with open(filename,'r') as source:
        mapping.put_attachment( source, name="content", content_type="text/csv" )
    return mapping

def validate( mapping_type, effective_date, filename ):
    date= datetime.datetime.strptime( effective_date, "%Y-%m-%d").date()
    if not os.path.exists( filename ):
        raise Exception( "File Not Found {0}".format(filename) )
    if mapping_type not in ( "vehicle", "route", "stop", "trip" ):
        raise ValueError( "Invalid mapping_type='{0}'".format(mapping_type) )
    return  dict(
        mapping_type=mapping_type,
        effective_date=date,
        filename=filename
        )

def push( mapping_type, date_str, filename ):
    cleaned= validate( mapping_type, date_str, filename )
    mapping= upload_mapping( caravel.settings.db, **cleaned )
    print( mapping, mapping._id )

if __name__ == "__main__":
    push( "vehicle", "2012-03-01", "vehicle.csv" )
    push( "route", "2012-03-01", "route.csv" )
    push( "stop", "2012-03-01", "stop.csv" )
