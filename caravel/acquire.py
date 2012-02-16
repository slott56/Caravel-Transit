#!/usr/bin/env python2.7
"""Caravel raw file acquire.

Checks FTP status and downloads latest versions of source files.

..  autofunction:: get_files

"""
from __future__ import print_function, division
import ftplib
from contextlib import closing
import datetime
from collections import namedtuple
import os.path
import logging

logger= logging.getLogger( __name__ )

Directory = namedtuple( "Directory", ['name', 'timestamp', 'size'] )

def get_files( connection=None, target_dir='.', **access ):
    """Get the lastest files.

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