#!/usr/bin/env python2.7
"""Caravel Log Capture via Monitor for Filesystem Changes.

This does a transform-push of an extract of a log.

The idea is that some other program has done the tail and copied the
file to a monitored directory.  This program is notified of the change
and does the transform-push operation.

See https://github.com/CfABrigadeHamptonRoads/HRT-Log-Capture

Synopsis
===========

::

    python2.7 -m caravel.LogCapture.monitor_capture [--verbose] path/to/directory

Description
===========

    Monitor the directory for changes.  When changes are detected,
    transform the raw log to CSV format to create a feed.
    Push the feed file to the HRTransit CouchDB.

Options
===========

    ..  program:: monitor_capture

    ..  option:: --vebose, -v

    The positional argument, :file:`path/to/directory`,
    identifies the directory to be watched for changes.

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
    from caravel.LogCapture.monitor_capture import monitor
    monitor( "directory" )

Directory Monitor
====================

The directory monitoring is best accomplished with the following projects.

    https://github.com/shaurz/fsmonitor
    http://sourceforge.net/projects/pywin32/

Both are required.

An alternative is watchdog.  It does more and has a more complex installation
and dependencies.

    http://packages.python.org/watchdog/

For background and more details, see

    http://blog.philippklaus.de/2011/08/watching-directories-for-changes-using-python\_-\_an-overview/

For Win32 **only**, there are some hacks that can be used.

    http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html

For Linux2 **only**, this can be used.

    http://pyinotify.sourceforge.net/

Components
=============

..  autofunction:: monitor
..  autofunction:: format_push
..  autofunction:: get_args
"""
from __future__ import print_function
import logging
import sys
import os
import datetime
import json
import argparse

from caravel.conf import settings
from caravel.LogCapture.log_capture import reformat, upload_feed
from fsmonitor import FSMonitor

logger= logging.getLogger( "monitor_capture" )

def monitor( directory ):
    """Monitor the given directory for changes.  When a new feed file
    arrives, perform the format and push operations.

    The config identifies specific filenames to be watched in the given
    directory.

    The ``'"capture" : { "extract_filename": "hrtrtf.txt", }'`` file
    is specifically targeted as the source for a feed.

    :param source: The file name to monitor for changes.
    :param config: A global configuration as read by :func:`get_config`.
    """
    m = FSMonitor()
    watch= m.add_dir_watch( directory )
    filename= settings.capture_extract_filename
    try:
        while True:
            for evt in m.read_events():
                if evt.action_name in ( "modify", "create", "move to" ) and evt.name == filename:
                    source= os.path.join( directory, filename )
                    mtime, size= os.path.getmtime(source), os.path.getsize(source)
                    dt= datetime.datetime.fromtimestamp(mtime)
                    logger.info( "Event: {0.action_name} {0.name}: {1}, {2}".format(evt, dt, size) )
                    format_push( source )
                else:
                    logger.debug( "Ignoring {0.action_name} {0.path}/{0.name}".format( evt ) )
    except (SystemExit, KeyboardInterrupt) as ex:
        pass

def format_push( source ):
    """Tail the source file to an extract; reformat the extract
    to CSV; push the CSV.

    This relies on :func:`tail`, :func:`reformat` and :func:`upload_feed`.

    :param source: The log file to tail.
    :param config: A global configuration as read by :func:`get_config`.
    """
    extract_filename= settings.capture_extract_filename
    csv_filename= settings.capture_csv_filename
    with open( extract_filename, "r" ) as source:
        with open( csv_filename, "w" ) as target:
            reformat( source, target )
    upload_feed( csv_filename )

def get_args():
    """Parse command-line arguments.

    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'source', action='store', nargs=1 )
    parser.add_argument( '--verbose', '-v', action='store_true', default=False )
    args= parser.parse_args()
    if not os.path.isdir( args.source[0] ):
        raise argparse.ArgumentTypeError( "Must monitor a directory" )
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    args= get_args()
    if args.verbose:
        logger.setLevel( logging.DEBUG )
    try:
        monitor( args.source[0] )
    except (KeyboardInterrupt,SystemExit) as e:
        logger.info( "Stopped" )
    except Exception as e:
        logger.exception( e )
    logging.shutdown()
