#!/usr/bin/env python2.7
"""Caravel Transit System "database".

This reads the various files that define the transit system to
create an in-memory database.

-   calendar.txt
-   calendar_dates.txt

-   routes.txt
-   stops.txt

-   trips.txt
-   stop_times.txt

Transit Objects
=================

..  autoclass:: Calendar
..  autoclass:: Calendar_Date
..  autoclass:: Route
..  autoclass:: Stop
..  autoclass:: Trip
..  autoclass:: Stop_Time
..  autoclass:: Candidate

Other Functions
=================

..  autofunction:: radians
..  autofunction:: degrees
..  autofunction:: dist_approx
..  autofunction:: time_parse

Transit "Connection"
======================

This is a database-like object.

..  autoclass:: Connection
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

def radians( degrees ):
    """Convert Lat/Lon degrees to radians.

    :param degrees: Latitude or Longitude
    :returns: Radians
    """
    return math.pi*degrees/180

def degrees( radians ):
    """Convert radians to Lat/Lon degrees.

    :param radians: angle in radians, usually from a distance calculation
    :returns: Degrees
    """
    return 180*radians/math.pi

def dist_approx( p1, p2 ):
    """The Equirectangular Approximation for distance between two coordinates.
    Fast and reasonably accurate.

    See :ref:`design.distance` for details.

    :param p1: (lat,lon) 2-tuple
    :param p2: (lat,lon) 2-tuple
    :returns: distance in statute miles.
    """
    lat1, lon1 = map( radians, p1 )
    lat2, lon2 = map( radians, p2 )
    x = (lon2-lon1) * math.cos((lat1+lat2)/2)
    y = (lat2-lat1)
    c = math.hypot(x,y)
    return 3961.3*c # 3440.07 for nm, 3961.3 for statute miles, 6378.1 for km, 20915664.0 for feet

def time_parse( string ):
    """Transform HH:MM:SS string into seconds past midnight.
    Unlike :mod:`datetime`, this does not mind times >= 24:00:00.

    :param string: String of the form HH:MM:SS
    :return: seconds past midnigth
    """
    hh, mm, ss = map(int, string.split(':'))
    return (hh*60+mm)*60+ss

Calendar = namedtuple('Calendar', 'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date')
Calendar_Date = namedtuple('Calendar_Date', 'service_id,date,exception_type' )
Route = namedtuple( 'Route', 'route_id,route_short_name,route_long_name,route_desc,route_type,route_url' )
Stop = namedtuple( 'Stop', 'stop_id,stop_name,stop_lat,stop_lon')
Trip = namedtuple( 'Trip', 'route_id,service_id,trip_id,direction_id,block_id' )
Stop_Time= namedtuple('Stop_Time', 'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint' )

Candidate = namedtuple('Candidate', ['distance', 'time', 'stop', 'stop_time'] )

class Connection( object ):
    """Open a database-like connection to the transit data.
    This will eagerly load all the files, creating a large (but fast) in-memory database.
    """
    def open( self, base ):
        """Open the given .ZIP file or directory.  This will eagerly load
        the files.  It takes a second or two.

        :param base: Directory name or .ZIP file name.
        """
        self.base= base
        if os.path.isfile( base ) and base.endswith('.zip'):
            # The google_transit.zip file
            zip= zipfile.ZipFile( base, 'r' )
            with zip.open( 'calendar.txt', 'r' ) as source:
                self.calendar= list( self._load_calendar(source) )
            with zip.open( 'calendar_dates.txt', 'r') as source:
                self.calendar_dates= dict( (cd.date,cd) for cd in self._load_calendar_dates(source) )
            with zip.open( 'routes.txt', 'r') as source:
                self.routes= dict( (r.route_id,r) for r in self._load_routes(source) )
            with zip.open( 'trips.txt', 'r') as source:
                self.trips= dict( (t.trip_id,t) for t in self._load_trips(source) )
            stop_times= defaultdict(list)
            trip_times= defaultdict(list)
            with zip.open('stop_times.txt', 'r') as source:
                for st in  self._load_stop_times(source):
                     stop_times[st.stop_id].append( st )
                     trip_times[st.trip_id].append( st )
            with zip.open('stops.txt', 'r') as source:
                self.stops= dict( (s.stop_id,s) for s in self._load_stops(source)
                    if s.stop_id in stop_times # reject spurious data
                    )
        else:
            # Unzipped directory of files
            with open( os.path.join(self.base,'calendar.txt'), 'rb') as source:
                self.calendar= list( self._load_calendar(source) )
            with open( os.path.join(self.base,'calendar_dates.txt'), 'rb') as source:
                self.calendar_dates= dict( (cd.date,cd) for cd in self._load_calendar_dates(source) )
            with open( os.path.join(self.base,'routes.txt'), 'rb') as source:
                self.routes= dict( (r.route_id,r) for r in self._load_routes(source) )
            with open( os.path.join(self.base,'trips.txt'), 'rb') as source:
                self.trips= dict( (t.trip_id,t) for t in self._load_trips(source) )
            stop_times= defaultdict(list)
            trip_times= defaultdict(list)
            with open( os.path.join(self.base,'stop_times.txt'), 'rb') as source:
                for st in  self._load_stop_times(source):
                     stop_times[st.stop_id].append( st )
                     trip_times[st.trip_id].append( st )
            with open( os.path.join(self.base,'stops.txt'), 'rb') as source:
                self.stops= dict( (s.stop_id,s) for s in self._load_stops(source)
                    if s.stop_id in stop_times # reject spurious data
                    )
        # Tweaks to raise key errors
        self.stop_times= dict(stop_times)
        self.trip_times= dict(trip_times)

    def _load_calendar(self, source):
        """Fetch the calendar table, creating :class:`Calendar` objects."""
        rdr= csv.DictReader( source )
        for row in rdr:
            row['start_date']= datetime.datetime.strptime( row['start_date'], '%Y%m%d' ).date()
            row['end_date']= datetime.datetime.strptime( row['end_date'], '%Y%m%d' ).date()
            yield Calendar( **row )
    def _load_calendar_dates(self, source):
        """Fetch the calendar_dates table, creating :class:`Calendar_Date` objects."""
        rdr= csv.DictReader( source )
        for row in rdr:
            row['date']= datetime.datetime.strptime( row['date'], '%Y%m%d' ).date()
            yield Calendar_Date( **row )
    def _load_routes(self, source):
        """Fetch the routes table, creating :class:`Route` objects."""
        rdr= csv.DictReader( source )
        for row in rdr:
            yield Route(**row)
    def _load_stops(self, source):
        """Fetch the stops table, creating :class:`Stop` objects.
        Note that some stops don't have any stop times, and should be ignored.
        """
        rdr= csv.DictReader( source )
        for row in rdr:
            row['stop_lat']= float(row['stop_lat'])
            row['stop_lon']= float(row['stop_lon'])
            yield Stop(**row)
    def _load_trips(self, source):
        """Fetch the trips table, creating :class:`Trip` objects."""
        rdr= csv.DictReader( source )
        for row in rdr:
            yield Trip(**row)
    def _load_stop_times(self, source):
        """Fetch the stop_times table, creating :class:`Stop_Time` objects."""
        rdr= csv.DictReader( source )
        for row in rdr:
            try:
                row['arrival_time']= time_parse(row['arrival_time'])
                row['departure_time']= time_parse(row['departure_time'])
                yield Stop_Time( **row )
            except ValueError:
                print( row, "has bad time" )
            except AssertionError:
                print( row, "has no stop" )

    def get_services_today( self, today=None ):
        """Returns the Service ID applicable today.
        Examines calendar and calendar dates.

        :param today: A :class:`datetime.date` object.
            If omitted, the current date is used.
        :returns: A sequence of service id strings that apply to this date.
        """
        if not today:
            today= datetime.datetime.today().date()
        if today in self.calendar_dates:
            yield self.calendar_dates[today].service_id
            return
        for cal in self.calendar:
            if cal.start_date <= today <= cal.end_date:
                column= ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')[today.weekday()]
                if int(getattr(cal, column)):
                    yield cal.service_id

    def get_closest_stops( self, lat_lon, max_dist=None ):
        """Given a lat/lon pair, locate nearby stops.

        :param lat_lon: A (lat,lon) 2-tuple
        :param max_dist: An upper limit on distances to examine
        :return: iterator over (distance,stop) pairs ordered from nearest to
            the specified max_dist value.
        """
        distances= ( (dist_approx( lat_lon, (s.stop_lat,s.stop_lon) ), s)
            for s in self.stops.values() )
        if max_dist is not None:
            distances = ( (dist,stop) for dist,stop in distances if dist < max_dist )
        return sorted(distances)
    def get_closest_times_in_service( self, stop_id, time, services, min_time=None, max_time=None ):
        """Given a stop and a time, locate the scheduled stop_time closest to this.

        :param stop_id: The id for a stop
        :param time: The seconds-after-midnight time
        :param services: The iterable sequence of services applicable
        :param min_time: The lower limit on seconds prior to the scheduled time.
            Usually, this is a negative number.
        :param max_time: The upper limit on seconds after the the scheduled time.
            This is a positive number.
        :returns: iterator over (time,stop_time) pairs ordered from closest in time
            to the max_time value.  The absolute magnitude is used for sorting
            so early and late times will be intermixed.
        """
        times = ( (st.arrival_time-time, st)
            for st in self.stop_times[stop_id]
            if self.trips[st.trip_id].service_id in services
            )
        if min_time is not None:
            times = ( (time,stop) for time,stop in times if time >= min_time )
        if max_time is not None:
            times = ( (time,stop) for time,stop in times if time < max_time )
        return sorted(times, key=lambda x: abs(x[0]) )
    def get_candidate_stops( self, report, services, max_dist=None, min_time=None, max_time=None, count=6 ):
        """Compute the most likely stops to match a report.
        This will use :meth:`get_closest_stops` to locate a collection of likely stops.
        For each stop, :meth:`get_closest_times_in_service` is used to locate the
        most likely scheduled time before or after the reported time.

        Initial surveys of the data provided guidance on the upper bounds
        for time and distance matching.

        :param report: a :class:`caravel.report.Report` instance.
        :param services: The iterable sequence of services applicable
        :param max_dist: An upper limit on distances to examine.  The default value is 0.1 mile.
        :param min_time: The lower limit on seconds prior to the scheduled time.
            Usually, this is a negative number.  The default is about -180 seconds.
        :param max_time: The upper limit on seconds after the the scheduled time.
            This is a positive number.  The default is about 360 seconds.
        """
        if max_dist is None: max_dist = 0.1 # subjective break between continuous and sparse
        if min_time is None: min_time = -(96.2+92.4*1)
        if max_time is None: max_time = 96.2+92.4*3
        distances= self.get_closest_stops( (report.lat, report.lon), max_dist=max_dist )
        for distance, stop in distances:
            h= 0
            for delta, stop_time in self.get_closest_times_in_service( stop.stop_id, report.time, services, min_time=min_time, max_time=max_time ):
                h= 1
                yield Candidate(int(distance*5280), delta, stop, stop_time)
            count -= h
            if count == 0: break
