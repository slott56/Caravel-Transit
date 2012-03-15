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

..  todo:: Use Stingray Reader to simplify the load.

Transit System Source

::

    http://googletf.gohrt.com/google_transit.zip

Acquisition
==============

..  autofunction:: get_source_data

Transit Objects
=================

..  autoclass:: Calendar
..  autoclass:: Calendar_Date
..  autoclass:: Route
..  autoclass:: Stop
..  autoclass:: Trip
..  autoclass:: Stop_Time
..  autoclass:: Candidate

Transit "Connection"
======================

This is a database-like object.

..  autoclass:: Accessor
    :members:

..  autoclass:: AccessZip
    :members:

..  autoclass:: AccessDir
    :members:

..  autoclass:: Connection
    :members:

Query Functions
=================

..  autofunction:: radians
..  autofunction:: degrees
..  autofunction:: dist_approx
..  autofunction:: get_services_today
..  autofunction:: get_closest_stops
..  autofunction:: get_closest_times_in_service
..  autofunction:: get_candidate_stops
..  autofunction:: get_route_from_stop_time
..  autofunction:: get_trip_from_stop_time
..  autofunction:: get_next_stop_time
..  autofunction:: get_route
..  autofunction:: get_stop
..  autofunction:: get_route_stops
..  autofunction:: get_stop_times
..  autofunction:: get_closest_stops_filtered
..  autofunction:: get_closest_routes_filtered

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
from contextlib import closing

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

Calendar = namedtuple('Calendar', 'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date')
Calendar_Date = namedtuple('Calendar_Date', 'service_id,date,exception_type' )
Route = namedtuple( 'Route', 'route_id,route_short_name,route_long_name,route_desc,route_type,route_url' )
Stop = namedtuple( 'Stop', 'stop_id,stop_name,stop_lat,stop_lon')
Trip = namedtuple( 'Trip', 'route_id,service_id,trip_id,direction_id,block_id' )
Stop_Time= namedtuple('Stop_Time', 'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint' )

Candidate = namedtuple('Candidate', ['distance', 'time', 'stop', 'stop_time'] )

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

class Connection( object ):
    """Open a database-like connection to the transit data.
    This will eagerly load all the files, creating a large (but fast) in-memory database.
    """
    def open( self, base ):
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
            raise IOError( "Unopenable Archive" )
        with self.accessor.open( 'calendar.txt' ) as source:
            self.calendar= list( self._load_calendar(source) )
        with self.accessor.open( 'calendar_dates.txt' ) as source:
            self.calendar_dates= dict( (cd.date,cd) for cd in self._load_calendar_dates(source) )
        with self.accessor.open( 'routes.txt' ) as source:
            self.routes= dict( (r.route_id,r) for r in self._load_routes(source) )
        with self.accessor.open( 'trips.txt' ) as source:
            self.trips= dict( (t.trip_id,t) for t in self._load_trips(source) )
        stop_times= defaultdict(list)
        with self.accessor.open('stop_times.txt' ) as source:
            for st in  self._load_stop_times(source):
                 stop_times[st.stop_id].append( st )
        # Force key errors
        self.stop_times= dict(stop_times)
        with self.accessor.open('stops.txt' ) as source:
            self.stops= dict( (s.stop_id,s) for s in self._load_stops(source)
                if s.stop_id in stop_times # reject spurious data
                )
        self.build_indices()
    def build_indices( self ):
        trip_times= defaultdict(list)
        for stop_id in self.stop_times:
            for st in self.stop_times[stop_id]:
                trip_times[st.trip_id].append( st )
        # Force key errors
        self.trip_times= dict(trip_times)

        trips_by_route= defaultdict(list)
        for t in self.trips.values():
            trips_by_route[t.route_id].append( t )
        # Force key errors
        self.trips_by_route= dict( trips_by_route )
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
    @staticmethod
    def time_parse( string ):
        """Transform HH:MM:SS string into seconds past midnight.
        Unlike :mod:`datetime`, this does not mind times >= 24:00:00.

        :param string: String of the form HH:MM:SS
        :return: seconds past midnigth
        """
        hh, mm, ss = map(int, string.split(':'))
        return (hh*60+mm)*60+ss
    def _load_stop_times(self, source):
        """Fetch the stop_times table, creating :class:`Stop_Time` objects."""
        rdr= csv.DictReader( source )
        for row in rdr:
            try:
                row['arrival_time']= self.time_parse(row['arrival_time'])
                row['departure_time']= self.time_parse(row['departure_time'])
                yield Stop_Time( **row )
            except ValueError:
                print( row, "has bad time" )
            except AssertionError:
                print( row, "has no stop" )


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

def get_services_today( conn, today=None ):
    """Returns the Service ID applicable today.
    Examines calendar and calendar dates.

    :param conn: An open :class:`Connection`.
    :param today: A :class:`datetime.date` object.
        If omitted, the current date is used.
    :returns: A sequence of service id strings that apply to this date.
    """
    if not today:
        today= datetime.datetime.today().date()
    if today in conn.calendar_dates:
        yield conn.calendar_dates[today].service_id
        return
    for cal in conn.calendar:
        if cal.start_date <= today <= cal.end_date:
            column= ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')[today.weekday()]
            if int(getattr(cal, column)):
                yield cal.service_id

def get_closest_stops( conn, lat_lon, max_dist=None ):
    """Given a lat/lon pair, locate nearby stops.

    Handles the following REST requests.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}`

        This can find the nearest stops to this coordinate.

    :param conn: An open :class:`Connection`.
    :param lat_lon: A (lat,lon) 2-tuple
    :param max_dist: An upper limit on distances to examine
    :return: iterator over (distance,stop) pairs ordered from nearest to
        the specified max_dist value.
    """
    distances= ( (dist_approx( lat_lon, (s.stop_lat,s.stop_lon) ), s)
        for s in conn.stops.values() )
    if max_dist is not None:
        distances = ( (dist,stop) for dist,stop in distances if dist < max_dist )
    return sorted(distances)

def get_closest_times_in_service( conn, stop_id, time, services, min_time=None, max_time=None ):
    """Given a stop and a time, locate the scheduled stop_time closest to this.

    :param conn: An open :class:`Connection`.
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
        for st in conn.stop_times[stop_id]
        if conn.trips[st.trip_id].service_id in services
        )
    if min_time is not None:
        times = ( (time,stop) for time,stop in times if time >= min_time )
    if max_time is not None:
        times = ( (time,stop) for time,stop in times if time < max_time )
    return sorted(times, key=lambda x: abs(x[0]) )

def get_candidate_stops( conn, lat_lon, time, services, max_dist=None, min_time=None, max_time=None, count=6 ):
    """Compute the most likely stops to match a report's lat/lon and time.
    This will use :meth:`get_closest_stops` to locate a collection of likely stops.
    For each stop, :meth:`get_closest_times_in_service` is used to locate the
    most likely scheduled time before or after the reported time.

    Initial surveys of the data provided guidance on the upper bounds
    for time and distance matching.

    :param conn: An open :class:`Connection`.
    :param lat_lon: A (lat,lon) tuple from a :class:`caravel.report.Report` instance.
    :param time: A time (seconds past midnight) from a :class:`caravel.report.Report` instance.
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
    distances= get_closest_stops( conn, lat_lon, max_dist=max_dist )
    for distance, stop in distances:
        h= 0
        for delta, stop_time in get_closest_times_in_service( conn, stop.stop_id, time, services, min_time=min_time, max_time=max_time ):
            h= 1
            yield Candidate(int(distance*5280), delta, stop, stop_time)
        count -= h
        if count == 0: break

def get_route_from_stop_time( conn, stop_time ):
    """Query the route that contains a given stop_time value.
    This does a stop_times JOIN trips JOIN routes query.

    :param conn: An open :class:`Connection`.
    :param stop_time: a :class:`Stop_Time` instance.
    :return: a :class:`Route` instance.
    """
    return conn.routes[conn.trips[stop_time.trip_id].route_id]

def get_trip_from_stop_time( conn, stop_time ):
    """Query the trip that contains a given stop_time value.
    This does a stop_times JOIN trips JOIN routes query.

    :param conn: An open :class:`Connection`.
    :param stop_time: a :class:`Stop_Time` instance.
    :return: a :class:`Trip` instance.
    """
    return conn.trips[stop_time.trip_id]

def get_next_stop_time( conn, stop_time, services ):
    """Given a :class:`Stop_Time` object, locate the remaining
    sequence of stops.

    :param conn: An open :class:`Connection`.
    :param stop_time: A :class:`Stop_Time` object
    :param services: The iterable sequence of services applicable
    :returns: iterator over (time,stop_time) pairs ordered from closest in time
        to the max_time value.  The absolute magnitude is used for sorting
        so early and late times will be intermixed.
    """
    next_iter = ( st for st in conn.trip_times[stop_time.trip_id]
                 if st.stop_id != stop_time.stop_id
                 and st.arrival_time >= stop_time.departure_time
                 and conn.trips[st.trip_id].service_id in services
                 )
    return next_iter

def get_route( conn, id=None ):
    """Returns route or list of routes.
    Handles the following REST requests.

    :samp:`/route/`

        The route list.  All 70.

    :samp:`/route/{id}/`

        All stops along the route, each stop decorated with direction and service.
        The time-of-day details for a given trip are not provided; they are associated
        with a specific stop.

    :param conn: An open :class:`Connection`.
    :param id: Optional route id.  If no route id, all routes are returned.
    :return: route or list of routes.  Each route is a 3-tuple of (route, trip_list)
        Each trip list is a sequence of stop_times.  Stop details are not included.
    """
    def elaborate( r ):
        return ( r, ( (t, conn.trip_times[t.trip_id]) for t in conn.trips_by_route[r.route_id] ) )
    if id:
        return elaborate( conn.routes[id] )
    else:
        return ( elaborate(r) for r in conn.routes.values() )

def get_stop( conn, id=None ):
    """Returns stop or list of stops.
    Handles the following REST requests.

    :samp:`/stop/`

        All 3210 stops.

    :samp:`/stop/{id}/`

        A specific stop.
    """
    def elaborate( s ):
        return s, conn.stop_times[s.stop_id]
    if id:
        return elaborate( conn.stops[id] )
    else:
        return ( elaborate(s) for s in conn.stops.values() )

def get_route_stops( conn, id, dir=None, date=None, time=None ):
    """Returns a route with a list of stops on that route.
    Handles the following REST requests.

    :samp:`/route/{id}/{dir}`

        All stops in a particular direction along the route.  The direction is
        more-or-less inoound or outbound, and is actually a foreign key to a direction
        table.

    :samp:`/route/{id}/?date={date}`

        All stops along the route filtered by services available on the given date.
        Day of week is generally sufficient, but there are calendar overrides,
        so full date is required.

    :samp:`/route/{id}/?date={date}&time={time}`

        All stops along the route, filtered by services available on the given date
        on or after the given time.  If these are ordered by distance (along the route's
        direction) it should provide a tidy summary of the route.

    :param conn: An open :class:`Connection`.
    :param id: route id.
    :param dir: optional direction, codes are '1' and '0'.
    :param date: a datetime.date object; the services available on this date
        are used to filter the results.
    :param time: a seconds-after-midnight time.
    """
    if dir:
        trips = ( t for t in conn.trips.values() if t.route_id==id and t.direction_id == dir)
    elif date:
        services= set(get_services_today( conn, date ))
        trips = ( t for t in conn.trips.values() if t.route_id==id and t.service_id in services)
    else:
        trips = ( t for t in conn.trips.values() if t.route_id==id)
    if time:
        stop_ids = set( st.stop_id for t in trips for st in conn.trip_times[t.trip_id] if st.arrival_time >= time )
    else:
        stop_ids = set( st.stop_id for t in trips for st in conn.trip_times[t.trip_id]  )
    return conn.routes[id], (conn.stops[stop_id] for stop_id in stop_ids)

def get_stop_times( conn, id, dir=None, date=None, time=None ):
    """Returns a stop with a list of stop times.
    Handles the following REST requests.

    :samp:`/stop/{id}/?dir={dir}`

        All stop times for this stop constrained by trip direction.

    :samp:`/stop/{id}/?dir={dir}&date={date}`

        All stop times for this stop constrained by services on the specific date.

    :samp:`/stop/{id}/?dir={dir}&date={date}&time={time}`

    All stop times at this stop, filtered by services available on the given date
    on or after the given time

    :param conn: An open :class:`Connection`.
    :param id: stop id.
    :param dir: optional route direction, codes are '1' and '0'.
    :param date: a datetime.date object; the services available on this date
        are used to filter the results.
    :param time: a seconds-after-midnight time.
    """
    if dir:
        times= list( (st,conn.trips[st.trip_id]) for st in conn.stop_times[id] if conn.trips[st.trip_id].direction_id == dir )
    elif date:
        services= set(get_services_today( conn, date ))
        times= list( (st,conn.trips[st.trip_id]) for st in conn.stop_times[id] if conn.trips[st.trip_id].service_id in services )
    else:
        times= list( (st,conn.trips[st.trip_id]) for st in conn.stop_times[id] )
    return  conn.stops[id], times

def filter_stops_by_dir( conn, stops, dir ):
    return ( s for s in stops if s.stop_id in set( st.stop_id for st in conn.stop_times[s.stop_id] if conn.trips[st.trip_id].direction_id == dir ) )

def filter_stops_by_date( conn, stops, date ):
    services= set(get_services_today( conn, date ))
    return ( s for s in stops if s.stop_id in set( st.stop_id for st in conn.stop_times[s.stop_id] if conn.trips[st.trip_id].service_id in services ) )

def filter_stops_by_time( conn, stops, time ):
    return ( s for s in stops if s.stop_id in set( st.stop_id for st in conn.stop_times[s.stop_id] if st.arrival_time >= time ) )

def get_closest_stops_filtered( conn, lat_lon, max_dist=None, dir=None, date=None, time=None ):
    """Given a lat/lon pair, locate nearby stops.

    Handles the following REST requests.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&dir={dir}`

        This can find the nearest stops for all routes heading in this direction.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}`

        This finds the nearest stops with a service that is active on the given date.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&time={time}`

        This finds the nearest stops with a service that is active on the given date
        and on or after the given time.


    :param conn: An open :class:`Connection`.
    :param lat_lon: A (lat,lon) 2-tuple
    :param dir: A trip direction_id
    :param max_dist: An upper limit on distances to examine
    :return: iterator over (distance,stop) pairs ordered from nearest to
        the specified max_dist value.
    """
    stops= ( s for d,s in get_closest_stops( conn, lat_lon, max_dist ) )
    if dir:
        stops= filter_stops_by_dir( conn, stops, dir )
    elif date:
        stops= filter_stops_by_date( conn, stops, date )
    if time:
        return filter_stops_by_time( conn, stops, time )
    else:
        return stops

def get_closest_routes_filtered( conn, lat_lon, id, dir=None, max_dist=None, date=None, time=None ):
    """Given a lat/lon pair, locate nearby stops on a given route.

    Handles the following REST requests.

    :samp:`/route/{id}/?latlng={nn.nnnnnn,mm.mmmmmm}`

        This can find the nearest stops on the given route to this coordinate.

    :samp:`/route/{id}/{dir}/?latlng={nn.nnnnnn,mm.mmmmmm}`

        This can find the nearest stops on the given route and direction to this coordinate.

    :samp:`/route/{id}/{dir}/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}`

        This can find the nearest stops on the given route and direction to this coordinate
        active on the given date.

    :samp:`/route/{id}/{dir}/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}&time={time}`

        This can find the nearest stops on the given route and direction to this coordinate
        active on the given date and on or after the given time.

    :param conn: An open :class:`Connection`.
    :param lat_lon: A (lat,lon) 2-tuple
    :paran id: route id
    :param dir: A trip direction_id
    :param max_dist: An upper limit on distances to examine
    :return: iterator over (distance,stop) pairs ordered from nearest to
        the specified max_dist value.
    """
    r, stops1_iter= get_route_stops( conn, id, dir, date, time )
    stops2= get_closest_stops_filtered( conn, lat_lon, max_dist, dir, date, time )
    return ( s for s in stops2 if s in set(stops1_iter) )