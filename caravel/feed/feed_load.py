#!/usr/bin/env python2.7
"""Caravel ETL of real-time-feed with mappings
from source encodings to GTFS keys.

Load New Feeds
===================

1.  Get the next unprocessed feed.

    -   Discard unreadable feeds.
    -   Discard feeds with improper headings.

2.  Apply the mapping;
    create the sequence of position reports.
    It's not essential to persist the position reports.

    The LogTail application uses the following headings for a feed.

    ::

        String[] headings = {
            "Date", "Time", "Vehicle", "Lat", "Lon", "Location Valid/Invalid",
            "Adherence", "Adherence Valid/Invalid", "Route", "Direction", "Stop"
        };

3.  Clean up old feeds.

Components
===========

..  autofunction:: remove_damaged
..  autofunction:: remove_old
..  autofunction:: new_feed_iter
..  autofunction:: transform_new
"""
from __future__ import print_function
from caravel.feed.models import *
from caravel.status.models import *
from caravel.report import ReportReader_v3
import datetime
from collections import defaultdict

def remove_damaged( db, feed_iter ):
    """Remove feed documents which are so damaged we can't map them
    to Python objects.

    This is rare, and usually comes from poor unit testing on LogTail.

    Once in a while, something can go horribly wrong and the
    query needs to be changed to "feed/all" to check all feeds
    instead of "feed/new".

    :return: sequence of {id:..., rev:..., ok:true} status responses.
    """
    docs= []
    for row in feed_iter:
        # Is this even a proper Feed?
        print( row )
        try:
            feed= Feed.wrap( row['value'] )
            continue
        except ValueError as e:
            pass
        except AttributeError as e:
            pass
        print( "Unusable", row, e )
        resp= db.delete_doc( row['value'] )
        docs.append( resp )
    return docs

def remove_old( db, today=None ):
    """Remove old feed documents that we've processed.

    :return: sequence of {id:..., rev:..., ok:true} status responses.
    """
    if today is None:
        today = datetime.datetime.today().date()
    docs= []
    for f in Feed.view('feed/old'):
        if (today-f.timestamp.date()).days >= 1:
            print( "Remove", f )
            resp= db.delete_doc( f )
            docs.append( resp )
    return docs

feed_headings = [
    "Date", "Time", "Vehicle", "Lat", "Lon", "Location Valid/Invalid",
    "Adherence", "Adherence Valid/Invalid", "Route", "Direction", "Stop"
]

def new_feed_iter():
    """Query all real-time Feed uploads.
    Do a validation to assure that

    a. we can build a Feed object,
    b. there's a proper attachment.
    """
    for doc in Feed.view('feed/new'):
        try:
            seq, _, hash = doc['_rev'].partition('-')
            if int(seq) >= 2 and 'feed' in doc['_attachments']:
                yield doc
        except ResourceNotFound:
            # Ignore them, they may be updated momentarily.
            pass

def validate_and_open( feed ):
    reader= ReportReader_v3()
    try:
        att= feed.fetch_attachment( name="feed", stream=True )
        reader.open( att )
        return feed, reader
    except AssertionError as e:
        feed.status= "wrong format attachment"
        feed.save()
        print( "Wrong Format", feed, e )
    return feed, None

def transform_new( mappings, feed_iter, track_arrival, track_location, today=None ):
    if today is None:
        today = datetime.datetime.today().date()
    counts= defaultdict(int)
    for doc in feed_iter:
        print( doc )
        feed, reader= validate_and_open( doc )
        if reader:
            for report in reader:
                if report.rte and report.dir and report.stop:
                    # Report is an arrival
                    track_arrival( mappings, report )
                    counts['arrival'] += 1
                else:
                    # Report is a location
                    track_location( mappings, report )
                    counts['location'] += 1
                counts['all'] += 1
        feed.status= 'processed'
        feed.save()
    return counts