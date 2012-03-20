#!/usr/bin/env python2.7
"""Caravel Log Capture.

This does a tail-transform-push of an active log.

See https://github.com/CfABrigadeHamptonRoads/HRT-Log-Capture

Synopsis
===========

::

    python2.7 -m caravel.LogCapture.log_capture [--verbose] path/to/some.log

Description
===========

    Tail the log file.  Transform the raw log to CSV format to create a feed.
    Push the feed file to the HRTransit CouchDB.

Options
===========

    ..  program:: log_capture

    .. option:: --vebose, -v

    .. option:: path/to/some.log

        The log file to be tailed.

Configuration File
====================

This will read a configuration file, :file:`hrtail_conf.py`

This file provides the CouchDB server name as well as temporary
file names and other configuration options.

::

    #hrtail_conf

    #Couch Push
    #Test Database
    couchpush = { "db_url": "http://localhost:5984/couchdbkit_test" }
    #Production Database
    #couchpush = { "db_url": "http://hrt.iriscouch.com:5984/feed" }

    #Log Tail
    logtail = { "tail_status_filename": "logtail.history",
        "file_size_limit": 1000000 }

    # Reformat

    # Capture
    capture = { "extract_filename": "hrtrtf.txt",
        "csv_filename": "hrtrtf.csv" }

Module API
============

This module can be invoked from a script as follows:

::

    from caravel.LogCapture.log_capture import config, capture
    config( db_url="http://localhost:5984/database/" )
    settings = {
        "logtail" : { "tail_status_filename": "logtail.history",
        "file_size_limit": 1000000 },
        "capture" : { "extract_filename": "hrtrtf.txt",
        "csv_filename": "hrtrtf.csv" }
    }
    capture( "some.log", 60.0, settings )

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

..  autofunction:: config
..  autoclass:: Timer
..  autofunction:: capture
..  autofunction:: tail_format_push
..  autofunction:: tail
..  autofunction:: reformat
..  autofunction:: upload_feed
..  autofunction:: get_args
..  autofunction:: get_config
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

from caravel.feed.models import Feed
from caravel.report import ReportReader_v1, headings

logger= logging.getLogger( "log_capture" )

def config( **kwargs ):
    """Configure this operation by opening the given
    CouchDB Server and Database.

    The kwargs must include ``db_url`` with the full URL
    to the CouchDB server and database.
    """
    global db
    db_url= kwargs.pop("db_url")
    p = urlparse.urlparse(db_url)
    server= "{0.scheme}://{0.netloc}".format( p )
    connection = Server(server)
    db = connection.get_or_create_db(p.path)
    logger.debug( "Connection {0!r} {1!r}".format(server, p.path) )
    return db

def upload_feed( filename ):
    """Upload a specific feed file.

    This depends on a previous invocation of :func:`config` to set
    the global database variable, :data:`db`.

    :param filename: a file to read and push.
    """
    global db
    Feed.set_db(db)
    feed= Feed(
        timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
        status= "new",
    )
    db.save_doc( feed )
    with open(filename,'r') as source:
        feed.put_attachment( source, name="feed", content_type="text/csv" )
    return feed

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
            except Exception, e:
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

def capture( source, seconds, config ):
    """Use :class:`Timer` class to schedule a recurring tail-format-push worker.
    This uses :func:`tail_format_push` to do the real work.

    :param source: The log file to tail.
    :param seconds: The cycling interval.  60 seconds makes a lot of sense.
    :param config: A global configuration as read by :func:`get_config`.
    """
    timer= Timer()
    if seconds == 0.0:
        timer.schedule( 2.0, tail_format_push, (source, config)  )
    else:
        now= timer.time()
        timer.schedule_fixed_rate( (60-now)%60, seconds, tail_format_push, (source, config)  )

def tail_format_push( source, config ):
    """Tail the source file to an extract; reformat the extract
    to CSV; push the CSV.

    This relies on :func:`tail`, :func:`reformat` and :func:`upload_feed`.

    :param source: The log file to tail.
    :param config: A global configuration as read by :func:`get_config`.
    """
    extract_filename= config['capture'].get('extract_filename','hrtrtf.txt')
    csv_filename= config['capture'].get('csv_filename','hrtrtf.csv')
    tail( source, extract_filename, config )
    with open( extract_filename, "r" ) as source:
        with open( csv_filename, "w" ) as target:
            reformat( source, target )
    upload_feed( csv_filename )

def tail( source_filename, extract_filename, config ):
    """Tail a log, writing an extract file, and maintaining state
    in a history file.  This allows tailing via a seek to the end of the file.

    :param source_filename: The log to tail.
    :param extract_filename: A temporary file to be written with the tailings.
    :param config: A global configuration as read by :func:`get_config`.
    """
    tail_status_filename= config['logtail'].get("tail_status_filename", "logtail.history")
    file_size_limit= int(config['logtail'].get("file_size_limit", "1000000"))

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

def reformat(extract_file, target_file):
    """Reformat an extract from a log file.

    :param extract_file: A file-like object suitable for reading.
    :param target_file: A file-like object which can be used by :mod:`csv`
        to create a CSV file.
    """
    reader= ReportReader_v1()
    reader.open( extract_file )
    wtr= csv.DictWriter( target_file, headings )
    wtr.writeheader()
    for item in reader:
        logger.debug( item )
        if item is not None:
            wtr.writerow( item.as_dict() )


def get_args():
    """Parse command-line arguments.

    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'source', action='store', nargs=1 )
    parser.add_argument( '-1', action='store_const', const=0.0, dest="cycle" )
    parser.add_argument( '--cycle', '-c', action='store', default=60.0, type=float )
    parser.add_argument( '--verbose', '-v', action='store_true', default=False )
    args= parser.parse_args()
    return args

def get_config():
    """Read the config file, :file:`hrtail_conf.py`
    to get the ``couchpush`` value.

    Usually, the content is this.

    ::

        couchpush = { "db_url": "http://localhost:5984/couchdbkit_test" }
        logtail = { "tail_status_filename": "logtail.history",
            "file_size_limit": 1000000 }
        capture = { "extract_filename": "hrtrtf.txt",
            "csv_filename": "hrtrtf.csv" }

    In principle, we should check ./hrtail_conf.py and ~/hrtail_conf.py.
    We only check the local directory, however.
    """
    settings = {}
    execfile( "hrtail_conf.py", settings )
    return settings

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    settings= get_config()
    args= get_args()
    if args.verbose:
        logging.getLogger().setLevel( logging.DEBUG )
    config( **settings['couchpush'] )
    try:
        capture( args.source[0], 60.0 if args.cycle is None else args.cycle, settings )
    except (KeyboardInterrupt,SystemExit) as e:
        logger.info( "Stopped" )
    except Exception as e:
        logger.exception( e )
    logging.shutdown()

