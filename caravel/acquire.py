#!/usr/bin/env python2.7
"""Caravel raw file acquire.

Checks FTP status and downloads latest versions of locations.

::

    host='216.54.15.3'
    user='anonymous'
    passwd='slott56@gmail.com'

Also.  Gets route information from http://googletf.gohrt.com/google_transit.zip

..  autofunction:: get_reports

..  autofunction:: get_route

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

logger= logging.getLogger( __name__ )

Directory = namedtuple( "Directory", ['name', 'timestamp', 'size'] )

def get_reports( connection=None, target_dir='.', **access ):
    """Get the lastest position report "file".

    Check for latest versions of "vid.csv" and download it only if it changed.

    Download the current version of  ``hrtrtf.txt`` file;
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
        access = dict(host='216.54.15.3', user='anonymous', passwd='slott56@gmail.com')

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

    with closing(connection(**access)) as server:
        server.dir("Anrd", get_directory)

        get_newest( server, "Anrd/vid.csv", 'vid.csv' )

        name= os.path.join(target_dir,
            file_status['hrtrtf.txt'].timestamp.strftime( "%Y%m%d%H%M.rpt") )
        with open(name, 'w' ) as target:
            logger.info( "Getting {0}".format(name) )
            server.retrlines("RETR Anrd/hrtrtf.txt", lambda line: print( line, file=target ) )
    return name


def get_route( connection=None, target_dir='.', url="http://googletf.gohrt.com/google_transit.zip" ):
    """Get the lastest Route Definition ZIP Archive.

    :param connection: Override to the default of urllib2.OpenerDirector.
    :param target_dir: Working directory for result file
    :param url: URL for the file (http://googletf.gohrt.com/google_transit.zip)
    """
    if not connection:
        connection= urllib2.build_opener()

    download=  urlparse.urlparse(url)
    dir, name = os.path.split( download.path )

    with closing( connection.open( url ) ) as source:
        with open(os.path.join(target_dir,name),'wb') as target:
            target.write( source.read() )
    return name