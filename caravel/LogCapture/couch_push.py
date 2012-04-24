#!/usr/bin/env python2.7
"""Caravel Push a Mapping.

Push Mapping data to HRT CouchDB.

Synopsis
===========

::

    python2.7 -m caravel.LogCapture.couch_push --mapping_type type --effective_date date [--verbose] source.csv

Description
===========

    Push the given mapping file to the HRTransit CouchDB.

Options
===========

    ..  program:: couch_push

    ..  option:: --mapping_type name, -m name

        Mapping type.  Must be one of "vehicle", "route" or "stop".

    ..  option:: --effective_date date, -e date

        Effective date for this mapping.  Must be in the form "YYYY-MM-DD".

    .. option:: --vebose, -v

    .. option:: source.csv

        The CSV file with the mapping.  The CSV file must have
        column names and the column names must match the mapping type.

    The file formats have mandatory column names as shown below.

    ======= =============================
    Type    Column Names
    ======= =============================
    vehicle "vid","bus"
    route   "rid","Route"
    stop    "sid","Stop"
    ======= =============================

    Yes, the upper-case/lower-case rules are inconsistent.

Configuration File
====================

This will read a configuration file, :file:`settings.py`

This file provides the CouchDB server name.

Module API
============

This module can be invoked from a script as follows:

::

    from caravel.LogCapture.couch_push import push, config
    config( db_url="http://localhost:5984/database" )
    push( "vehicle", "2012-03-01", "vehicle.csv" )
    push( "route", "2012-03-01", "route.csv" )
    push( "stop", "2012-03-01", "stop.csv" )

Database Schema
==================

A mapping file must be CSV format (with well-defined headings.
They are attached to a document with the following
attributes

::

    timestamp      : year-mm-ddThh:mm:ssZ
    effective_date : year-mm-dd
    mapping_type   : "vehicle", "route" or "stop"
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

Components
=============

..  autofunction:: upload_mapping
..  autofunction:: validate
..  autofunction:: push
..  autofunction:: get_args
"""
from __future__ import print_function
import logging
import sys
import datetime
import os
import urllib2
import urlparse
from contextlib import closing
import sched
import time
import argparse
from couchdbkit import Server
from caravel.conf import settings
from caravel.feed.models import Mapping

logger= logging.getLogger( "couch_push" )

def upload_mapping( mapping_type, effective_date, filename ):
    """Upload a specific mapping file with a given effective date.

    The effective date must be a datetime.date object.

    :param mapping_type: "vehicle", "route" or "stop" mapping type
    :param effective_date: datetime.date at which this mapping becomes effective.
        Mappings remain effective until a mapping with a later effective date
        is pushed and validated.
    :param filename: a file to read and push.
    """
    Mapping.set_db(settings.db)
    mapping= Mapping(
        timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
        effective_date= effective_date,
        mapping_type= mapping_type,
    )
    settings.db.save_doc( mapping )
    with open(filename,'r') as source:
        mapping.put_attachment( source, name="content", content_type="text/csv" )
    return mapping

def validate( mapping_type, effective_date, filename ):
    """Validate the arguments.

    :param mapping_type: "vehicle", "route" or "stop" mapping type
    :param effective_date: datetime.date at which this mapping becomes effective.
        Mappings remain effective until a mapping with a later effective date
        is pushed and validated.
    :param filename: a file to read and push.

    :returns: a dict with cleansed argument values.
    """
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
    """Module API.   Validates the argument values and pushes the file.

    :param mapping_type: "vehicle", "route" or "stop" mapping type
    :param effective_date: datetime.date at which this mapping becomes effective.
        Mappings remain effective until a mapping with a later effective date
        is pushed and validated.
    :param filename: a file to read and push.
    """
    try:
        cleaned= validate( mapping_type, date_str, filename )
    except Exception, e:
        logger.error( "Invalid File: {0!r}".format(e) )
        return
    mapping= upload_mapping( **cleaned )
    logger.info( "{0!s} {1!r}".format(mapping, mapping._id) )

def get_args():
    """Parse command-line arguments.

    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'source', action='store', nargs=1 )
    parser.add_argument( '--mapping_type', '-m', action='store', choices=["vehicle","route","stop"] )
    parser.add_argument( '--effective_date', '-e', action='store' )
    parser.add_argument( '--verbose', '-v', action='store_true', default=False )
    args= parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    args= get_args()
    if args.verbose:
        logging.getLogger().setLevel( logging.DEBUG )
    push( args.mapping_type, args.effective_date, args.source[0] )
    logging.shutdown()
