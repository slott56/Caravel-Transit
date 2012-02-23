#!/usr/bin/env python2.7
"""Caravel Transit System Statistics

This computes the overall average time between stops along all routes.

It computes the overall average distance between stops along all routes.

..  autofunction:: route_size
..  autofunction:: route_stop_stats
"""
from __future__ import print_function, division
import os
import transit_system
import statistics

def route_size( conn ):
    """Examine all stops to get the complete bounding rectangle
    of lat/lon coordinates.
    """
    stop_iter= iter(conn.stops.values())
    first= next(stop_iter)
    min_lat= max_lat= first.stop_lat
    min_lon= max_lon= first.stop_lon
    for stop in stop_iter:
        min_lat= min( stop.stop_lat, min_lat )
        max_lat= max( stop.stop_lat, max_lat )
        min_lon= min( stop.stop_lon, min_lon )
        max_lon= max( stop.stop_lon, max_lon )
    print( "Lat: {0:.4f} {1:.4f}".format(min_lat, max_lat) )
    print( "Lon: {0:.4f} {1:.4f}".format(min_lon, max_lon) )

def route_stop_stats( conn ):
    """These are simple descriptive statistics of distances
    between stops and distances between arrival times along
    the defined routes.
    """
    time_delta = statistics.FQTable()
    distance_delta= statistics.FQTable()
    for t in conn.trips:
        trip= conn.trips[t]
        stops= conn.trip_times[trip.trip_id]
        for i in range(1,len(stops)):
            # time and distance from previous stop
            d_t= stops[i].arrival_time -stops[i-1].arrival_time
            p_i= conn.stops[stops[i].stop_id].stop_lat, conn.stops[stops[i].stop_id].stop_lat
            p_i1= conn.stops[stops[i-1].stop_id].stop_lat, conn.stops[stops[i-1].stop_id].stop_lat
            d_d= transit_system.dist_approx( p_i, p_i1 )
            if d_t != 0: time_delta[ d_t ] += 1
            d_bin= 16*int(d_d*5280//16)
            if d_bin != 0: distance_delta[d_bin] += 1
    print( 'time', time_delta.mean(), time_delta.sd() )
    print( 'dist', distance_delta.mean(), distance_delta.sd() )


if __name__ == "__main__":
    data = os.path.join('hampton-roads-transit-hrt_20120218_0425' )
    conn= transit_system.Connection( )
    conn.open( data )
    print( 'calendar', len(conn.calendar))
    print( 'calendar_dates', len(conn.calendar_dates))
    print( 'routes', len(conn.routes) )
    print( 'stops', len(conn.stops) )
    print( 'trips', len(conn.trips) )
    print( 'stop_times', len(conn.stop_times) )
    route_size( conn )
    route_stop_stats( conn )
