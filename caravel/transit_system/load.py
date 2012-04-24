#!/usr/bin/env python2.7
"""Caravel Transit System Database Load.

This reads the various files that define the transit system to
create a CouchDB database.

-   calendar.txt
-   calendar_dates.txt

-   routes.txt
-   stops.txt

-   trips.txt
-   stop_times.txt

..  todo:: Use Stingray Reader to simplify the load.

Transit System Source

::

    http://googletf.gohrt.com/google_transit.zip

Load
==============

..  autofunction:: get_source_data

..  autoclass:: Accessor
    :members:

..  autoclass:: AccessZip
    :members:

..  autoclass:: AccessDir
    :members:


"""
from __future__ import print_function, division
from collections import namedtuple, defaultdict
from itertools import tee
import datetime
import csv
import os
import math
import pprint
import glob
import zipfile
import caravel.report
import urlparse
import urllib2
import time
from caravel.conf import settings
from caravel.transit_system.models import Route_Definition, Service, Stop_Definition
from contextlib import closing
from couchdbkit.exceptions import *

URL_Google_Transit = "http://googletf.gohrt.com/google_transit.zip"

def get_source_data( connection=None, target_dir='.', url=None ):
    """Get the lastest Route Definition ZIP Archive.

    :param connection: Override to the default of urllib2.OpenerDirector.
    :param target_dir: Working directory for result file
    :param url: URL for the file (http://googletf.gohrt.com/google_transit.zip)
    """
    if not connection:
        connection= urllib2.build_opener()
    if not url:
        url= URL_Google_Transit

    download=  urlparse.urlparse(url)
    dir, name = os.path.split( download.path )

    with closing( connection.open( url ) ) as source:
        with open(os.path.join(target_dir,name),'wb') as target:
            target.write( source.read() )
    return name

class Accessor( object ):
    """Abstract superclass to unify access to a directory and access to
    a ZIP archive.
    """
    pass

class AccessZip( Accessor ):
    """Access a ZIP archive."""
    def __init__( self, archive ):
        """Prepare the archive for access.

        :param archive: a ZIP archive.
        """
        self.archive= archive
        self.zip= zipfile.ZipFile( self.archive, 'r' )
    def open( self, name, mode='r' ):
        """Returns an open file object for the named member."""
        return self.zip.open( name, mode )

class AccessDir( Accessor ):
    """Access a Directory (an archive that's been expanded.)"""
    def __init__( self, base ):
        """Prepare the directory for access.

        :param base: the directory name.
        """
        self.base= base
    def open( self, name, mode='rb' ):
        """Returns an open file object for the named member."""
        return open( os.path.join(self.base,name), mode )

class Loader( object ):
    """Load the transit data to the CouchDB.
    """
    weekday_name = 'monday,tuesday,wednesday,thursday,friday,saturday,sunday'.split(',')
    def load( self, base ):
        """Open the given .ZIP file or directory.  This will eagerly load
        the files.  It takes a second or two.

        :param base: Directory name or .ZIP file name.
        """
        if os.path.isfile( base ) and base.endswith('.zip'):
            # A google_transit.zip file
            self.accessor= AccessZip( base )
        elif os.path.isdir( base ):
            # Unzipped directory
            self.accessor = AccessDir( base )
        else:
            raise IOError( "Unopenable Archive: {0!r}".format(base) )

        settings.db.compact()
        time.sleep(1.0) # Wait for compaction.

        with self.accessor.open( 'calendar.txt' ) as source:
            rdr= csv.DictReader( source )
            self._load_calendar(rdr)
        with self.accessor.open( 'calendar_dates.txt' ) as source:
            rdr= csv.DictReader( source )
            self._load_calendar_dates(rdr)
        with self.accessor.open( 'routes.txt' ) as source:
            rdr= csv.DictReader( source )
            self._load_routes(rdr)
        with self.accessor.open('stops.txt' ) as source:
            rdr= csv.DictReader( source )
            self._load_stops(rdr)
        with self.accessor.open( 'trips.txt' ) as source:
            rdr= csv.DictReader( source )
            self._load_trips(rdr)
        with self.accessor.open('stop_times.txt' ) as source:
            rdr= csv.DictReader( source )
            self._load_stop_times(rdr)

        settings.db.compact()
        time.sleep(1.0) # Wait for compaction.

    def _load_calendar(self, rdr):
        """Fetch the calendar table, creating :class:`Service` objects.

        Given a calendar row, create the details for each date.

        Mapping from day number to day "name".
        Must match the keys in GTF data.
        """
        Service.set_db( settings.db )
        services_by_date= defaultdict(set)
        for row in rdr:
            start_date= datetime.datetime.strptime( row['start_date'], '%Y%m%d' ).date()
            end_date= datetime.datetime.strptime( row['end_date'], '%Y%m%d' ).date()
            for d in xrange((end_date-start_date).days+1):
                date= start_date + datetime.timedelta(days=d)
                day_name= self.weekday_name[date.weekday()]
                if row[day_name] == '1':
                    services_by_date[date].add(row['service_id'])
        for date in sorted(services_by_date):
            if date.day == 1:
                time.sleep(0.25)
            previous= list( Service.view( 'service/bydate', key=date.strftime("%Y-%m-%d") ) )
            if previous:
                settings.db.delete_docs( previous )
            serv= Service(
                date= date,
                day_of_week= self.weekday_name[date.weekday()].title(),
                services= list( sorted(services_by_date[date]) ),
            )
            #print( serv, settings.db, Service.get_db() )
            settings.db.save_doc(serv)
    def _load_calendar_dates(self, rdr):
        """Fetch the calendar_dates table, updating the :class:`Service` objects.
        Can only be done successfully **after** the core calendar has been loaded.
        These are add/remove changes to the calendar.
        """
        Service.set_db( settings.db )
        for row in rdr:
            date= datetime.datetime.strptime( row['date'], '%Y%m%d' ).date()
            docs= list( Service.view( 'service/bydate', key=date.strftime("%Y-%m-%d") ) )
            if docs:
                serv= docs[0]
                if row['exception_type'] == '1': # Add
                    serv.services.append( row['service_id'])
                elif row['exception_type'] == '2' and row['service_id'] in serv.services: # Remove
                    serv.services.remove( row['service_id'])
                elif row['exception_type'] == '2' and row['service_id'] not in serv.services:
                    # Wasn't there to begin with?  Weird.
                    pass
                else:
                    raise GTFException( "Unknown Calendar Date {0!r}".format(row) )
            else:
                # Missing date?  Weird.
                pass
            serv.save()
    def _load_routes(self, rdr):
        """Fetch the routes table, creating :class:`Route_Definition` objects."""
        Route_Definition.set_db( settings.db )
        for row in rdr:
            for r in Route_Definition.view( 'service/route', key=row['route_id'] ):
                r.delete()
            route= Route_Definition(**row)
            route.save()
    def _load_stops(self, rdr):
        """Fetch the stops table, creating :class:`Stop_Definition` objects.
        Note that some stops don't have any stop times, and should be ignored.
        """
        Stop_Definition.set_db( settings.db )
        for row in rdr:
            for s in Stop_Definition.view( 'service/stop', key=row['stop_id'] ):
                s.delete()
            row['stop_lat']= float(row['stop_lat'])
            row['stop_lon']= float(row['stop_lon'])
            stop= Stop_Definition(**row)
            stop.save()

    def _load_trips(self, rdr):
        """Fetch the trips table, updating :class:`Route_Definition` objects with trips.
        Must be loaded after stops and routes, but before stop times.

        This is a mapping among route_id,service_id,trip_id,direction_id,block_id

        -   [route/direction] -> [service class] -> [trip]<>-> [list of stops]

        -   [stop] -> [service class] -> [list of trips] -> [route/direction]
        """
        self.trip= {}
        self.trip_by_route= defaultdict(list)
        for row in rdr:
            self.trip[ row['trip_id'] ]= row
            self.trip_by_route[ row['route_id'] ].append( row )

    @staticmethod
    def time_parse( string ):
        """Transform HH:MM:SS string into seconds past midnight.
        Unlike :mod:`datetime`, this does not mind times >= 24:00:00.

        :param string: String of the form HH:MM:SS
        :return: seconds past midnight
        """
        hh, mm, ss = map(int, string.split(':'))
        return (hh*60+mm)*60+ss

    def _load_stop_times(self, rdr):
        """Fetch the stop_times table, :class:`Route_Definition` objects with times.

        Must be done last.  Requires the self.trip and self.trip_by_route information.
        """
        for row in rdr:
            try:
                row['arrival_time']= self.time_parse(row['arrival_time'])
                row['departure_time']= self.time_parse(row['departure_time'])
            except ValueError:
                raise GTFException( "Bad Time {0!r}".format(row) )

            trip= self.trip[row['trip_id']]

            docs= list( Route_Definition.view( 'service/route', key=trip['route_id'] ) )
            route= docs[0]
            if trip['service_id'] not in route.trips:
                route.trips[ trip['service_id'] ]= {}
            if trip['trip_id'] not in route.trips[trip['service_id']]:
                route.trips[ trip['service_id'] ][trip['trip_id']] = dict(
                        direction_id= trip['direction_id'],
                        block_id= trip['block_id'],
                        stops= [], )
            route_trip= route.trips[ trip['service_id'] ][trip['trip_id']]
            route_trip['stops'].append( row )
            route.save()

            docs = list( Stop_Definition.view( 'service/stop', key=row['stop_id']))
            stop= docs[0]
            if trip['service_id'] not in stop.trips:
                stop.trips[ trip['service_id'] ]= {}
            if trip['trip_id'] not in stop.trips[trip['service_id']]:
                stop.trips[ trip['service_id'] ][trip['trip_id']] = dict(
                        direction_id= trip['direction_id'],
                        block_id= trip['block_id'],
                        route= trip['route_id'],
                        times= [], )
            stop_trip= stop.trips[ trip['service_id'] ][trip['trip_id']]
            stop_trip['times'].append( row )
            stop.save()
