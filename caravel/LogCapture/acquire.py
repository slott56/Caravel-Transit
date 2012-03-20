#!/usr/bin/env python2.7
"""Caravel FTP-based Data Acquisition

Gather raw position reports by polling an FTP server.

The position reports should be pushed into a queue for processing.
This can be a conceptual queue in a single-threaded applicaiton, or an
actual multi-processing queue to improve performance.

FTP Source

::

    host='216.54.15.3'
    user='anonymous'
    passwd='slott56@gmail.com'

..  autofunction:: report_reader
..  autofunction:: get_report_files

..  deprecated:: FTP Polling is no longer preferred.
"""
from __future__ import print_function, division
import ftplib
import urllib2
from contextlib import closing
import datetime
from collections import namedtuple
import urlparse
import os.path
import logging

URL_Positions = "ftp://216.54.15.3/Anrd/hrtrtf.txt"
URL_Vehicle_ID = "ftp://216.54.15.3/Anrd/vid.csv"

logger= logging.getLogger( __name__ )

def report_reader( connection=None, url=None ):
    """Open the position report file for reading.
    This is a file-like object which must be closed properly.

    ::

        with closing( report_reader() ):
            for line in data:
                process line

    :param connection: Override to the default of urllib2
    :param host: URL for the real-time data.
    """
    if not connection:
        connection= urllib2.build_opener()
    if not url:
        url= URL_Positions

    return connection.open( url )

def get_report_files( connection=None, target_dir='.', **access ):
    """Get the lastest position report "file" and save it to the
    target directory.

    Check for latest versions of "Anrd/vid.csv" and download it only if it changed.

    Download the current version of  ``Anrd/hrtrtf.txt`` file;
    naming it with a ``YYYYMMDDHHMM.rpt`` name.

    :param connection: Override to the default of ftplib.FTP
    :param target_dir: Working directory for result files
    :param host: IP address or name of the FTP host.
    :param user: FTP username
    :param passwd: FTP password
    """
    if not connection:
        connection= ftplib.FTP
    if not access:
        access= dict(
            host= "216.54.15.3",
            user="anonymous",
            passwd="s_lott@yahoo.com",
        )

    Directory = namedtuple( "Directory", ['name', 'timestamp', 'size'] )

    file_status = {}

    def get_directory( line ):
        if not line: return
        date, time, size_str, name = line.strip().split()
        timestamp= datetime.datetime.strptime( date+time, "%m-%d-%y%I:%M%p" )
        size= int(size_str)
        file_status[name]= Directory( name, timestamp, size )

    def get_newest( server, source, destination ):
        name= os.path.join(target_dir, destination)
        try:
            local_timestamp= datetime.datetime.fromtimestamp(os.path.getmtime(name) )
        except OSError:
            local_timestamp= None
        if not local_timestamp or file_status[destination].timestamp > local_timestamp:
            logger.info( "Getting newer {0}".format(source) )
            with open( name, 'wb') as target:
                server.retrbinary("RETR {0}".format(source), target.write)

    def get_current( server, source, destination ):
        with open(destination, 'w' ) as target:
            logger.info( "Getting {0}".format(name) )
            server.retrlines("RETR {0}".format(source),
                lambda line: print( line, file=target ) )

    with closing(connection(**access)) as server:
        server.dir("Anrd", get_directory)
        try:
            get_newest( server, "Anrd/vid.csv", 'vid.csv' )
        except ftplib.error_perm:
            pass
        except KeyError:
            pass

        name= os.path.join(target_dir,
            file_status['hrtrtf.txt'].timestamp.strftime( "%Y%m%d%H%M.rpt") )
        get_current( server, "Anrd/hrtrtf.txt", name )

    return name
