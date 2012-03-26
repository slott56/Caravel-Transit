#!/usr/bin/env python2.7
"""Caravel Log Capture via Tail.

This does a tail-transform-push of an active log.

See https://github.com/CfABrigadeHamptonRoads/HRT-Log-Capture

Synopsis
===========

::

    python2.7 -m caravel.LogCapture.log_capture [--verbose] [-t task] [-c 60] path/to/some.log

Description
===========

    Tail the log file.  Transform the raw log to CSV format to create a feed.
    Push the feed file to the HRTransit CouchDB.

Options
===========

    ..  program:: log_capture

    ..  option:: --vebose, -v

    ..  option:: --task task_name, -t task_name

        The task is either ``Tail_Only`` or ``Tail_Format_Push``.

    ..  option:: --cycle time, -c time

        The cycle interval.  Default is 60 seconds.

    The positional argument, :file:`path/to/some.log`,
    identifies The log file to be tailed.

Configuration File
====================

This will read a configuration file, :file:`settings.py`

This file provides the CouchDB server name as well as temporary
file names and other configuration options.

::

    #hrtail_conf

    #Couch Push
    #Test Database
    db_url= "http://localhost:5984/couchdbkit_test"
    #Production Database
    #db_url= "http://hrt.iriscouch.com:5984/feed"

    #Log Tail
    logtail_status_filename= "logtail.history"
    logtail_size_limit= 1*1000*1000

    # Reformat

    # Capture
    capture_extract_filename= "hrtrtf.txt"
    capture_csv_filename= "hrtrtf.csv"

Module API
============

This module can be invoked from a script as follows:

::

    from caravel.conf import settings
    from caravel.LogCapture.log_capture import capture
    capture( "Tail_Format_Push", 60.0, "some.log" )

Database Schema
==================

A feed file must be CSV format (with well-defined headings.
They are attached to a document with the following
attributes

::

    timestamp      : year-mm-ddThh:mm:ssZ
    status         : "new"
    feed           : the file

Example JSON document

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

With curl, it's a sequence like the following

::

    curl -X POST http://username:password@hrt.iriscouch.com:5984/couchdbkit_test/
    --user <user:password>
    -H "Content-Type: application/json"
    -d '{"timestamp":"2012-03-02T16:16:00Z", "doc_type":"Feed", "status":"new"}'

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

::

    curl -X PUT http://hrt.iriscouch.com:5984/couchdbkit_test/09833a88a1cbb06f64c555d0245f1af3/feed/?rev=1-7750ef2dbce77303f957de17c754852a
    --user <user:password>
    -H "Content-Type: text/csv" @hrtrtf.csv

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

Components
=============

..  autoclass:: Timer
..  autofunction:: capture
..  autofunction:: tail_only
..  autofunction:: tail_format_push
..  autofunction:: tail
..  autofunction:: transform
..  autofunction:: reformat
..  autofunction:: upload_feed
..  autofunction:: get_args
"""
from __future__ import print_function
import logging
import sys
import datetime
import os
import json
import csv
import urlparse
import time
import argparse
from couchdbkit import Server

from caravel.conf import settings
from caravel.feed.models import Feed
from caravel.report import ReportReader_v1, headings

logger= logging.getLogger( "log_capture" )

class Timer( object ):
    """A cycling version of :mod:`sched`.

    Once created, this will invoke a specific function on a given cycling
    interval.  It tries to be very accurate in doing the scheduling.
    """
    def __init__( self ):
        """Initialize the Timer."""
        self.running= True
    def cancel( self ):
        """Cancel the timing loop."""
        self.running= False
    def delay( self, amount ):
        """Pause for ``amount`` seconds.

        :param amount: seconds of delay.
        """
        time.sleep( amount )
    def time( self ):
        """Return the current time in seconds."""
        return time.time()
    def schedule_fixed_rate( self, pause, interval, worker, args ):
        """Schedule a worker function at a fixed interval.

        The worker function can signal a normal exit by raising
        :exc:`StopIteration`.

        :param pause: Initial delay in seconds.
        :param interval: Scheduling interval in seconds.
        :param worker: a function to call.
        :param args: a sequence of args to pass to the function.
        """
        while self.running:
            self.delay( pause )
            try:
                start= self.time()
                worker(*args)
                end= self.time()
            except StopIteration:
                end= start
                self.cancel()
            except Exception as e:
                logger.exception( e )
                self.cancel()
                raise
            pause= (start-end) % interval
    def schedule( self, pause, worker, args ):
        """Schedule a worker function once after an initial delay.

        :param pause: Initial delay in seconds.
        :param worker: a function to call.
        :param args: a sequence of args to pass to the function.
        """
        self.delay( pause )
        worker( *args )

def capture( task_name, seconds, source ):
    """Use :class:`Timer` class to schedule a recurring tail-format-push worker.
    This uses :func:`tail_format_push` or :func:`tail_only` to do the real work.

    :param task_name: Name of the task to perform.
    :param seconds: The cycling interval.  60 seconds makes a lot of sense.
    :param source: The log file to tail.
    """
    task= { 'tail_format_push' : tail_format_push,
           'tail_only': tail_only }[task_name.lower()]
    timer= Timer()
    if seconds == 0.0:
        timer.schedule( 2.0, task, (source,)  )
    else:
        now= timer.time()
        timer.schedule_fixed_rate( (60-now)%60, seconds, task, (source,)  )

def tail_only( source ):
    """Tail the source file to an extract.

    This relies on :func:`tail`.

    :param source: The log file to tail.
    """
    extract_filename= settings.capture_extract_filename
    tail( source, extract_filename )

def tail_format_push( source ):
    """Tail the source file to an extract; reformat the extract
    to CSV; push the CSV.

    This relies on :func:`tail`, :func:`reformat` and :func:`upload_feed`.

    :param source: The log file to tail.
    """
    extract_filename= settings.capture_extract_filename
    csv_filename= settings.capture_csv_filename
    tail( source, extract_filename, config )
    with open( extract_filename, "r" ) as source:
        with open( csv_filename, "w" ) as target:
            reformat( source, target )
    upload_feed( csv_filename )

def tail( source_filename, extract_filename ):
    """Tail a log, writing an extract file, and maintaining state
    in a history file.  This allows tailing via a seek to the end of the file.

    :param source_filename: The log to tail.
    :param extract_filename: A temporary file to be written with the tailings.
    """
    tail_status_filename= settings.logtail_status_filename
    file_size_limit= settings.logtail_size_limit

    try:
        with open(tail_status_filename,"r") as tail_status_file:
            status= json.load( tail_status_file )
    except Exception:
        status= {}

    prev_size= int( status.get( 'size.'+source_filename, '0' ) )
    sequence= int( status.get( 'seq.'+source_filename, '0' ) )
    logger.info( "Tailing {0} to {1}\nCount {2}, Bytes {3}".format(source_filename, extract_filename, sequence, prev_size ))
    sequence += 1

    current_size= os.path.getsize( source_filename )
    if current_size == prev_size:
        pass
    else:
        with open( source_filename, 'r' ) as source:
            if current_size < prev_size:
                # Truncated.  Read from beginning.
                sequence= 0
                prev_size= 0
            else:
                # Got bigger
                source.seek( prev_size )
            if current_size - prev_size > file_size_limit:
                # Got a lot bigger.
                read_size= limit
                source.seek( current_size - limit )
            else:
                read_size = current_size - prev_size
            with open( extract_filename.format(sequence), 'w' ) as target:
                target.write( source.read(read_size) )
    status['size.'+source_filename] = current_size
    status['seq.'+source_filename] = sequence
    with open(tail_status_filename,"w") as tail_status_file:
        json.dump( status, tail_status_file, indent=2 )
    return extract_filename

# HRT-Log-Capture headings used by status package and capture package.
capture_headings = [
        "Date", "Time", "Vehicle", "Lat", "Lon", "Location Valid/Invalid",
        "Adherence", "Adherence Valid/Invalid", "Route", "Direction", "Stop"
]

def transform( report ):
    """Transform a :class:`Report` instance into a dictionary
    with column names that match HRT-Log-Capture.
    """
    return {
        "Date": report.timestamp.date(),
        "Time": report.timestamp.time(),
        "Vehicle": report.id,
        "Lat": report.lat,
        "Lon": report.lon,
        "Location Valid/Invalid": report.ll_valid,
        "Adherence": report.adher,
        "Adherence Valid/Invalid": report.adher_valid,
        "Route": report.rte,
        "Direction": report.dir,
        "Stop": report.stop,
    }

def reformat(extract_file, target_file):
    """Reformat an extract from a log file.

    The output file has headings defined by the report module.
    These are also used by the status package.

    These must be compatible with the HRT-Log-Capture headings.
    The :func:`transform` function reformats the source data
    into the result strcuture.

    :param extract_file: A file-like object suitable for reading.
    :param target_file: A file-like object which can be used by :mod:`csv`
        to create a CSV file.
    """
    reader= ReportReader_v1()
    reader.open( extract_file )
    wtr= csv.DictWriter( target_file, capture_headings )
    wtr.writeheader()
    for item in reader:
        logger.debug( item )
        if item is not None:
            wtr.writerow( transform(item) )

def upload_feed( filename ):
    """Upload a specific feed file.

    This depends on a previous invocation of :func:`config` to set
    the global database variable, :data:`settings.db`.

    :param filename: a file to read and push.
    """
    Feed.set_db(settings.db)
    feed= Feed(
        timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
        status= "new",
    )
    settings.db.save_doc( feed )
    with open(filename,'r') as source:
        feed.put_attachment( source, name="feed", content_type="text/csv" )
    return feed

def get_args():
    """Parse command-line arguments.

    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'source', action='store', nargs=1 )
    parser.add_argument( '-1', action='store_const', const=0.0, dest="cycle" )
    parser.add_argument( '--task', '-t', action='store', choices=["Tail_Only", "Tail_Format_Push"] )
    parser.add_argument( '--cycle', '-c', action='store', default=60.0, type=float )
    parser.add_argument( '--verbose', '-v', action='store_true', default=False )
    args= parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    args= get_args()
    if args.verbose:
        logger.setLevel( logging.DEBUG )
    try:
        capture( args.task, 60.0 if args.cycle is None else args.cycle, args.source[0] )
    except (KeyboardInterrupt,SystemExit) as e:
        logger.info( "Stopped" )
    except Exception as e:
        logger.exception( e )
    logging.shutdown()
