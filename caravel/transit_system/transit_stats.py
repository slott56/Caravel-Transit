#!/usr/bin/env python2.7
"""Caravel Transit System Statistics

This computes the overall average time between stops along all routes.

It computes the overall average distance between stops along all routes.

..  autofunction:: route_size

..  autofunction:: route_stop_stats

..  autofunction:: time
"""
from __future__ import print_function, division
import os
import caravel.statistics
import caravel.transit_system.load
import caravel.transit_system.models
from collections import namedtuple, defaultdict
import csv
import datetime

def route_size(conn):
    """Examine all stops to get the complete bounding rectangle
    of lat/lon coordinates.
    """
    LatLon= namedtuple( 'LatLon', ('stop_lat', 'stop_lon') )
    with conn.open('stops.txt') as stops:
        rdr= csv.DictReader( stops )
        stop_iter = ( LatLon(float(row['stop_lat']),  float(row['stop_lon'])) for row in rdr )
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

def time( text ):
    """Parse HH:MM:SS that may go past 23:59:59."""
    hh, mm, ss = map(int, text.split(':'))
    return (hh*60+mm)*60+ss

def route_stop_stats( conn ):
    """These are simple descriptive statistics of distances
    between stops and distances between arrival times along
    the defined routes.
    """
    time_delta = caravel.statistics.FQTable()
    distance_delta= caravel.statistics.FQTable()
    stop_times= defaultdict(list)
    with conn.open('stop_times.txt') as stop_times_txt:
        rdr= csv.DictReader(stop_times_txt)
        for row in rdr:
            stop_times[row['trip_id']].append( row )
    with conn.open('stops.txt') as stops_txt:
        rdr= csv.DictReader( stops_txt )
        stop_defs= dict( (row['stop_id'], row) for row in rdr )
    with conn.open('trips.txt') as trips_txt:
        trips= csv.DictReader( trips_txt )
        for trip in trips:
            stops= stop_times[trip['trip_id']]
            for i in range(1,len(stops)):
                # time and distance from previous stop
                d_t= time(stops[i]['arrival_time']) - time(stops[i-1]['arrival_time'])
                p_i= float(stop_defs[stops[i]['stop_id']]['stop_lat']), float(stop_defs[stops[i]['stop_id']]['stop_lat'])
                p_i1= float(stop_defs[stops[i-1]['stop_id']]['stop_lat']), float(stop_defs[stops[i-1]['stop_id']]['stop_lat'])
                d_d= caravel.transit_system.models.dist_approx( p_i, p_i1 )
                if d_t != 0: time_delta[ d_t ] += 1
                d_bin= 16*int(d_d*5280//16)
                if d_bin != 0: distance_delta[d_bin] += 1
    print( 'time', time_delta.mean(), time_delta.sd() )
    print( 'dist', distance_delta.mean(), distance_delta.sd() )


if __name__ == "__main__":
    data = os.path.join('hampton-roads-transit-hrt_20120218_0425' )
    conn= caravel.transit_system.load.AccessDir( data )
    with conn.open( 'calendar.txt' ) as source:
        print( 'calendar', len(source.readlines()))
    with conn.open('calendar_dates.txt') as source:
        print( 'calendar_dates', len(source.readlines()))
    with conn.open('routes.txt') as source:
        print( 'routes', len(source.readlines()) )
    with conn.open('stops.txt') as source:
        print( 'stops', len(source.readlines()) )
    with conn.open('trips.txt') as source:
        print( 'trips', len(source.readlines()) )
    with conn.open('stop_times.txt') as source:
        print( 'stop_times', len(source.readlines()) )

    route_size( conn )
    route_stop_stats( conn )
