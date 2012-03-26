#!/usr/bin/env python2.7
"""Caravel ETL of real-time-feed with mappings
from source encodings to GTFS keys.

1.  Get the next position report with the mapping applied.

    -   Locations have precious little additional information.

    -   Arrivals, however, have plenty of additional data, including
        Route, Direction and Stop.

2.  Track route, route-stop, stop and vehicle status.

3.  Clean up old status reports.

Components
============

..  autofunction:: update_route
..  autofunction:: update_route_stop
..  autofunction:: update_stop
..  autofunction:: update_vehicle
..  autofunction:: track_arrival
..  autofunction:: track_location
..  autofunction:: remove_old
"""
from __future__ import print_function
from caravel.feed.models import *
from caravel.status.models import *
import datetime
from collections import defaultdict

def update_route( report ):
    """Add to today's route/direction documents."""
    docid= "{0.route}-{0.direction}".format( report )
    try:
        route_obj= Route.get( docid=docid )
    except ResourceNotFound:
        route_obj= Route(
            date= report.timestamp.date(),
            route= report.route,
            direction= report.direction,
            history= [],
        )
    # Check for duplicate vehicle/time in the report set.
    if report.timestamp not in set( h['timestamp'] for h in route_obj.history ):
        # Also, assure that it's sorted in order?
        route_obj.history.append(
            {'vehicle':report.vehicle, 'stop': report.stop, 'timestamp':report.timestamp} )
    route_obj.save()
    return route_obj

def update_route_stop( report ):
    """Add to today's route/direction/stop documents."""
    docid= "{0.route}-{0.direction}-{0.stop}".format( report )
    try:
       routestop = RouteStop().get(docid=docid)
    except ResourceNotFound:
        routestop = RouteStop(
            date= report.timestamp.date(),
            route= report.route,
            direction= report.direction,
            stop= report.stop,
            history= [],
        )
    if report.timestamp not in set( h['timestamp'] for h in routestop.history ):
        routestop.history.append( {'vehicle':report.vehicle, 'timestamp':report.timestamp})
    routestop.save()
    return routestop

def update_stop( report ):
    """Add to today's Stop documents."""
    docid= "{0.stop}".format( report )
    try:
       stop_object = Stop().get(docid=docid)
    except ResourceNotFound:
        stop_object = Stop(
            date= report.timestamp.date(),
            stop= report.stop,
            history= [],
        )
    if report.timestamp not in set( h['timestamp'] for h in stop_object.history ):
        stop_object.history.append( {'vehicle':report.vehicle, 'timestamp':report.timestamp})
    stop_object.save()
    return stop_object

def update_vehicle( report ):
    """Add to today's vehicle documents at this stop."""

    docid= "{0.vehicle}".format( report )
    try:
       vehicle_obj = Vehicle().get(docid=docid)
    except ResourceNotFound:
        vehicle_obj = Vehicle(
            date= report.timestamp.date(),
            vehicle= report.vehicle,
            history= [],
        )
    if report.timestamp not in set( h['timestamp'] for h in vehicle_obj.history ):
        vehicle_obj.history.append( {'route':report.route,
                                    'direction':report.direction,
                                    'stop':report.stop,
                                    'timestamp':report.timestamp})
    vehicle_obj.save()
    return vehicle_obj

def track_arrival( mappings, report ):
    """Apply mappings.  Create or update status objects.

    Use a Hard-wired mapping for direction.

    Apply current mappings for route, vehicle and stop.
    If (a) the mapping exists and (b) the value is in the mapping
    """

    direction = {'1':'Inbound', '2':'Outbound'}[report.dir]
    try:
        route= mappings['route'].map[report.rte]
    except KeyError:
        route= None
    try:
        stop= mappings['stop'].map[report.stop]
    except KeyError:
        stop= None
    try:
        v= report.id[4:]
        vehicle= mappings['vehicle'].map[v]
    except KeyError:
        vehicle= None
    report.route= route
    report.direction= direction
    report.stop= stop
    report.vehicle= vehicle

    if route and stop:
        #print( report, 'route', route, direction, stop )

        update_route(report)
        update_route_stop(report)
        update_stop(report)

    if vehicle:
        update_vehicle(report)
    return report

def track_location( mappings, report ):
    """Track a simple location report.

    ..  todo:: Geospatial lookup

        Gather statistics on location reports
        to find these other locations.
    """

    try:
        v= report.id[4:]
        vehicle= mappings['vehicle'].map[v]
    except KeyError:
        vehicle= None

    report.route= None
    report.direction= None
    report.stop= None
    # Use a geospatial lookup to match
    # this with a point on the route system.

    if vehicle:
        update_vehicle(report)

    print( report, 'bus', vehicle )

def remove_old( db, today=None ):
    """Remove old Route, RouteStop and Vehicle reports.

    This should only be run once in a great while.

    :return: sequence of {id:..., rev:..., ok:true} status responses.
    """
    if today is None:
        today= datetime.datetime.today().date()
    docs= []
    for r in db.view('status/all'):
        object= r['value']
        published= datetime.datetime.strptime(object['date'],'%Y-%m-%d').date()
        if (today-published).days >= 1:
            print( "Delete ", object )
            resp= db.delete_doc(object['_id'])
            docs.append( resp )
    return docs