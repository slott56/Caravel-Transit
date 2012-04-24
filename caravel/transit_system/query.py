#!/usr/bin/env python2.7
"""Caravel Transit System Database Queries.


Query Functions
=================

..  autofunction:: get_services_today
..  autofunction:: get_closest_stops
..  autofunction:: get_closest_times_in_service
..  autofunction:: get_candidate_stops
..  autofunction:: get_route_from_stop_time
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
from caravel.transit_system.models import Service, Stop_Definition, Route_Definition, dist_approx

from caravel.conf import settings

Candidate = namedtuple('Candidate', ['distance', 'time', 'stop', 'stop_time'] )

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

    If ``id`` is None, it returns all route definitions.

    Otherwise, it returns the requested route definition.

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

    If ``id`` is None, it returns all stop definitions.

    Otherwise, it returns the requested stop definition.

    :param id: Optional stop id.  If no stop id, all stops are returned.
    :return: stop definition or list of stop definitions.
    """
    Stop_Definition.set_db( settings.db )
    if id:
        return list( Stop_Definition.view( 'service/stop', key=id ) )
    else:
        return list( Stop_Definition.view( 'service/stop' ) )

def get_route_stops( id, dir=None, date=None ):
    """Returns a route with a list of stops on that route.

    The route ID is required.
    Either a direction or a date must be given to filter the stops
    along the route.

    If direction is given,

        All stops in a particular direction along the route.  The direction is
        more-or-less inoound or outbound, and is actually a foreign key to a direction
        table.

    If date is given,

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

    The stop ID is required.
    Either a direction or a date must be given to filter the times
    at this stop.

    If a direction is given.

        All stop times for this stop constrained by trip direction.

    If a date is given.

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

    Handles the following kinds of queries for a stop.

    -   latlng=nn.nnnnnn,mm.mmmmmm and direction

        This can find the nearest stops for all routes heading in this direction.

    -   latlng=nn.nnnnnn,mm.mmmmmm and date

        This finds the nearest stops with a service that is active on the given date.

    -   atlng=nn.nnnnnn,mm.mmmmmm and time

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

    Handles the following kinds of queries for stops associated with a given route.

    -   latlng=nn.nnnnnn,mm.mmmmmm

        This can find the nearest stops on the given route to this coordinate.

    -   latlng=nn.nnnnnn,mm.mmmmmm and direction

        This can find the nearest stops on the given route and direction to this coordinate.

    -   latlng=nn.nnnnnn,mm.mmmmmm, direction and date

        This can find the nearest stops on the given route and direction to this coordinate
        active on the given date.

    -   latlng=nn.nnnnnn,mm.mmmmmm, direction, date and time

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
