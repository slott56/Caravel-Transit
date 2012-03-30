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

..  autoclass:: Accessor
    :members:

..  autoclass:: AccessZip
    :members:

..  autoclass:: AccessDir
    :members:

Transit Objects
=================

..  autoclass:: Service
..  autoclass:: Route_Definition
..  autoclass:: Stop_Definition

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
from caravel.conf import settings
from contextlib import closing
from couchdbkit import Document
from couchdbkit import schema
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

class Service( Document ):
    date= schema.DateProperty()
    day_of_week= schema.StringProperty()
    services= schema.ListProperty()
    def __repr__( self ):
        return "Service(date={0.date}, day_of_week={0.day_of_week}, services={0.services})".format( self )

class Route_Definition( Document ):
    route_id= schema.StringProperty()
    route_short_name= schema.StringProperty()
    route_long_name= schema.StringProperty()
    route_desc= schema.StringProperty()
    route_type= schema.StringProperty()
    route_url= schema.StringProperty()
    trips= schema.DictProperty() # Service is required to identify a given trip.
    # Trip is { trip_id:..., direction_id:..., block_id:..., stops:{ ... } }
    def __repr__( self ):
        return ("Route_Definition( route_id={0.route_id}, "
                "route_short_name= {0.route_short_name}, "
                "route_long_name= {0.route_long_name}, "
                "route_desc= {0.route_desc}, "
                "route_type= {0.route_type}, "
                "route_url= {0.route_url}, "
                "trips= {0.trips!r} )").format( self )
    def stops( self ):
        """Flat list of stops on this route."""
        for svc in self.trips:
            for trip in self.trips[svc]:
                for s in self.trips[svc][trip]['stops']:
                    yield s

class Stop_Definition( Document ):
    stop_id= schema.StringProperty()
    stop_name= schema.StringProperty()
    stop_lat= schema.FloatProperty()
    stop_lon= schema.FloatProperty()
    trips= schema.DictProperty() # Service is required to identify a given trip.
    def __repr__( self ):
        return ("Stop_Definition( stop_id={0.stop_id}, "
                "stop_name= {0.stop_name}, "
                "stop_lat= {0.stop_lat}, "
                "stop_lon= {0.stop_lon}, "
                "trips= {0.trips!r} )").format( self )
    def distance_from( self, lat, lon ):
        """Distance from a given point, in miles."""
        return dist_approx( (self.stop_lat, self.stop_lon), (lat,lon) )

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
    def _load_calendar(self, rdr):
        """Fetch the calendar table, creating :class:`Service` objects.

        Give a given calendar row, create the details for each date."""
        # Mapping from day number to day name.  Must be in this order.  No changes.
        # Must match the dictionary keys in GTF data.
        Service.set_db( settings.db )
        services_by_date= defaultdict(set)
        for row in rdr:
            start_date= datetime.datetime.strptime( row['start_date'], '%Y%m%d' ).date()
            end_date= datetime.datetime.strptime( row['end_date'], '%Y%m%d' ).date()
            for d in xrange((end_date-start_date).days+1):
                date= start_date + datetime.timedelta(days=d)
                day_name= self.weekday_name[date.weekday()]
                if row[day_name] == '1':
                    services_by_date[date].add( row['service_id'])
        for date in sorted(services_by_date):
            settings.db.bulk_delete( list( Service.view( 'service/bydate', key=date.strftime("%Y-%m-%d") ) ) )
            serv= Service(
                date= date,
                day_of_week= self.weekday_name[date.weekday()].title(),
                services= list( sorted(services_by_date[date]) ),
            )
            serv.save()
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

def get_services_today( today=None ):
    """Returns the Service ID applicable today.
    Examines calendar and calendar dates.

    :param today: A :class:`datetime.date` object.
        If omitted, the current date is used.
    :returns: A sequence of service id strings that apply to this date.
    """
    Service.set_db(settings.db)
    if not today:
        today= datetime.datetime.today().date()
    svc= list( Service.view( 'service/bydate', key=today.strftime("%Y-%m-%d")) )
    if not svc: return []
    return svc[0].services

def get_closest_stops( lat_lon, max_dist=None ):
    """Given a lat/lon pair, locate nearby stops.

    Handles the following REST requests.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}`

        This can find the nearest stops to this coordinate.

    :param lat_lon: A (lat,lon) 2-tuple
    :param max_dist: An upper limit on distances to examine
    :return: iterator over (distance,stop) pairs ordered from nearest to
        the specified max_dist value.
    """
    Stop_Definition.set_db( settings.db )
    distances= ( (dist_approx( lat_lon, (s.stop_lat,s.stop_lon) ), s)
        for s in Stop_Definition.view('service/stop') )
    if max_dist is not None:
        distances = ( (dist,stop) for dist,stop in distances if dist < max_dist )
    return sorted(distances)

def get_closest_times_in_service( stop_id, time, services, min_time=None, max_time=None ):
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
    # get StopTimes based on Stop.  Need a view of key=Stop, value=stop time
    Stop_Definition.set_db( settings.db )
    stop= list( Stop_Definition.view('service/stop') )[0]
    trips = []
    for svc in services:
        trips.extend( stop.trips[svc].values() )
    times = ( (st['arrival_time']-time, st)
        for t in trips
        for st in t['times']
        )
    if min_time is not None:
        times = ( (time,stop) for time,stop in times if time >= min_time )
    if max_time is not None:
        times = ( (time,stop) for time,stop in times if time < max_time )
    return sorted(times, key=lambda x: abs(x[0]) )

def get_candidate_stops( lat_lon, time, services, max_dist=None, min_time=None, max_time=None, count=6 ):
    """Compute the most likely stops to match a report's lat/lon and time.
    This will use :meth:`get_closest_stops` to locate a collection of likely stops.
    For each stop, :meth:`get_closest_times_in_service` is used to locate the
    most likely scheduled time before or after the reported time.

    Initial surveys of the data provided guidance on the upper bounds
    for time and distance matching.

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
    distances= get_closest_stops( lat_lon, max_dist=max_dist )
    for distance, stop in distances:
        h= 0
        for delta, stop_time in get_closest_times_in_service( stop.stop_id, time, services, min_time=min_time, max_time=max_time ):
            h= 1
            yield Candidate(int(distance*5280), delta, stop, stop_time)
        count -= h
        if count == 0: break

def get_route_from_stop_time( stop_time ):
    """Query the route that contains a given stop_time value.
    This does a stop_times JOIN trips JOIN routes query.

    This is ill-constrained, since it can provide lots of
    routes all over the transit system.

    :param stop_time: a :class:`Stop_Time` instance.
    :return: a :class:`Route` instance.
    """
    Route_Definition.set_db( settings.db )
    return list( Route_Definition.view( 'service/stop_time', key_start= stop_time ) )

def get_next_stop_time( stop, time, services ):
    """Given a :class:`Stop_Definition` object, a time after midnight,
    and specific classes of service,
    locate the remaining sequence of stops.

    :param stop: A :class:`Stop_Definition` object
    :param time: A seconds-after-midnight arrival time to use as a filter
    :param services: The iterable sequence of services applicable
    :returns: sequence of dictionaries with stop time information.
    """
    for s in services:
        if s in stop.trips:
            for trip in stop.trips[s]:
                route_view= Route_Definition.view('service/route',key=stop.trips[s][trip]['route'])
                for route in route_view:
                    for trip in route.trips[s]:
                        for t in route.trips[s][trip]['stops']:
                            if t['arrival_time'] >= time:
                                yield t

def get_route( id=None ):
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
    :return: route definition or list of route definitions.
    """
    Route_Definition.set_db( settings.db )
    if id:
        return list( Route_Definition.view( 'service/route', key=id ) )
    else:
        return list(Route_Definition.view( 'service/route' ))

def get_stop( id=None ):
    """Returns stop or list of stops.
    Handles the following REST requests.

    :samp:`/stop/`

        All 3210 stops.

    :samp:`/stop/{id}/`

        A specific stop.

    :param id: Optional route id.  If no route id, all routes are returned.
    :return: stop definition or list of stop definitions.
    """
    Stop_Definition.set_db( settings.db )
    if id:
        return list( Stop_Definition.view( 'service/stop', key=id ) )
    else:
        return list( Stop_Definition.view( 'service/stop' ) )

def get_route_stops( id, dir=None, date=None ):
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

    :param id: route id.
    :param dir: optional direction, codes are '1' and '0'.
    :param date: a datetime.date object; the services available on this date
        are used to filter the results.

    :returns: a :class:`Route_Definition` instance.
    """
    Route_Definition.set_db( settings.db )
    route= list( Route_Definition.view('service/route',key=id) )[0]
    if date:
        services= set(get_services_today( date ))
        for s in route.trips:
            if s not in services:
                del route.trips[s]
    if dir:
        for svc in route.trips:
            for trip in route.trips[svc]:
                if route.trips[svc][trip]['direction_id'] != dir:
                    del route.trips[svc][trip]
    return route

def get_stop_times( id, dir=None, date=None ):
    """Returns a stop with a list of stop times.
    Handles the following REST requests.

    :samp:`/stop/{id}/?dir={dir}`

        All stop times for this stop constrained by trip direction.

    :samp:`/stop/{id}/?dir={dir}&date={date}`

        All stop times for this stop constrained by services on the specific date.

    :param id: stop id.
    :param dir: optional route direction, codes are '1' and '0'.
    :param date: a datetime.date object; the services available on this date
        are used to filter the results.
    :returns: a :class:`Stop_Definition` instance.
    """
    Stop_Definition.set_db( settings.db )
    stop= list( Stop_Definition.view('service/stop',key=id) )[0]

    if date:
        services= set(get_services_today( date ))
        for s in stop.trips:
            if s not in services:
                del stop.trips[s]
    if dir:
        for svc in stop.trips:
            for trip in stop.trips[svc]:
                if stop.trips[svc][trip]['direction_id'] != dir:
                    del stop.trips[svc][trip]
    return  stop

def filter_stops_by_dir( stops, dir ):
    """Pick only stops where the trip direction is the given direction."""
    for stop in stops:
        any_dir= any( stop.trips[svc][trip]['direction_id'] == dir
            for svc in stop.trips
            for trip in stop.trips[svc] )
        if any_dir:
            yield stop

def filter_stops_by_date( stops, date ):
    services= set(get_services_today( date ))
    for stop in stops:
        any_svc = any( s in stop.trips for s in services )
        if any_svc:
            yield stop

def filter_stops_by_time( stops, time ):
    for stop in stops:
        any_time= any( stop_time['arrival_time'] >= time
            for svc in stop.trips
            for trip in stop.trips[svc]
            for stop_time in stop.trips[svc][trip]['times'] )
        if any_time:
            yield stop

def get_closest_stops_filtered( lat_lon, max_dist=None, dir=None, date=None, time=None ):
    """Given a lat/lon pair, locate nearby stops.

    Handles the following REST requests.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&dir={dir}`

        This can find the nearest stops for all routes heading in this direction.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}`

        This finds the nearest stops with a service that is active on the given date.

    :samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&time={time}`

        This finds the nearest stops with a service that is active on the given date
        and on or after the given time.


    :param lat_lon: A (lat,lon) 2-tuple
    :param dir: A trip direction_id
    :param max_dist: An upper limit on distances to examine
    :return: iterator over (distance,stop) pairs ordered from nearest to
        the specified max_dist value.
    """
    stops= list( s for d,s in get_closest_stops( lat_lon, max_dist ) )
    #print( "get_closest_stops_filtered", stops, dir, date, time )
    if dir:
        stops= list( filter_stops_by_dir( stops, dir ) )
    if date:
        stops= list( filter_stops_by_date( stops, date ) )
    if time:
        stops= list( filter_stops_by_time( stops, time ) )
    #print( "get_closest_stops_filtered", stops )
    return stops

def get_closest_routes_filtered( lat_lon, id, dir=None, max_dist=None, date=None, time=None ):
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

    :param lat_lon: A (lat,lon) 2-tuple
    :paran id: route id
    :param dir: A trip direction_id
    :param max_dist: An upper limit on distances to examine
    :return: iterator over (distance,stop) pairs ordered from nearest to
        the specified max_dist value.
    """
    route= get_route_stops( id, dir, date )
    route_stops = set( s['stop_id'] for s in route.stops() )
    #print( "get_closest_routes_filtered", route, route_stops )
    closest_stops= get_closest_stops_filtered( lat_lon, max_dist, dir, date, time )
    #print( "get_closest_routes_filtered", closest_stops )

    return ( s for s in closest_stops if s.stop_id in route_stops )