#!/usr/bin/env python2.7
"""From live Arrival and Dwell records, compute the closest stop.

Synopsis

::

    python -m caraval.arrival_at_stop -t hrt_20120218_0425 *.rpt

Description

Uses the supplied transit information directory to gather information
on the transit system.

Reads the given raw \*.rpt feed to get bus Reports.

Each Arrival or Dwell report is matched against a stop to determine where
the vehicle is and how it stands with respect to it's schedule.
This creates a CSV file with the Report, Stop, Stop Time, Route and Trip information.

Some Reports cannot be matched against a stop, these reports are written
to a "reject" file, possibly including one or two stops near the report.

Options

..  program:: arrival_at_stop

..  option:: \*.rpt...

    List of source files to process.

..  option:: --new

    Get a new .rpt file and process it.

..  option:: -t transit_details

    Directory (or .ZIP) with HRT details.

..  option:: -r no_stop.csv

    Reject file to which Reports are written for which there is no stop.

..  option:: -s stop.csv

    Stops file to which Report, Stop, Stop Time, Route and Trip information
    is written.

..  autofunction:: arrival_at_stop

..  autofunction:: prefix_fields
..  autofunction:: prefix_dict

..  autoclass: Stop
    :members:

..  autoclass: NoStop
    :members:

..  autofunction:: get_args
"""
from __future__ import print_function, division
from collections import defaultdict, Callable
import datetime
import csv
import os
import glob
import caravel.report
import transit_system
import pprint
import logging
import sys
import argparse

logger= logging.getLogger( __name__ )

def arrival_at_stop( conn, files, no_stop=print, stop=print ):
    counts= defaultdict( int )
    factory= caravel.report.ReportFactory()
    for report in caravel.report.report_iter( factory, files ):
        counts['input'] += 1
        if not (report and report.rte): # Arrival or Dwell
            counts['excluded'] += 1
            continue
        services= tuple( transit_system.get_services_today( conn, report.timestamp.date() ) )
        if not services:
            no_stop( "Bad Date", report, None, None )
            counts['bad date'] += 1
            continue

        # Some analysis seems to indicate that 528 feet is far enough away.
        candidates = list( transit_system.get_candidate_stops(conn, (report.lat, report.lon), report.time, services, max_dist=0.10) )

        if len(candidates) == 0:
            wider= 0.5 # # Search out as far as 2640 feet away.
            candidates = list( transit_system.get_candidate_stops(conn, (report.lat, report.lon), report.time, services, max_dist=wider) )
            try:
                dist_fit= min( candidates, key=lambda x: x.distance )
                time_fit= min( candidates, key=lambda x: abs(x.time) )
                if dist_fit.distance == time_fit.distance and dist_fit.time == time_fit.time:
                    no_stop( ">0.10", report, dist_fit, None )
                else:
                    no_stop( ">0.10", report, dist_fit, time_fit )
            except ValueError:
                # usually ValueError: min() arg is an empty sequence
                no_stop( ">{0:.2f}".format(wider), report, None, None )
            counts['no stop'] += 1
            continue

        # candidate with minimum time from scheduled stop.
        best_fit= min( candidates, key=lambda x: abs(x.time) )

        #print( '  fit', best_fit )
        stop( report, best_fit.distance, best_fit.time, best_fit.stop, best_fit.stop_time,
            transit_system.get_route_from_stop_time( conn, best_fit.stop_time ),
            transit_system.get_trip_from_stop_time( conn, best_fit.stop_time ), )
        counts['good']  += 1
    return counts

def prefix_fields( prefix, nt_class ):
    return list(prefix+'_'+f for f in nt_class._fields)

def prefix_dict( prefix, nt_obj ):
    return dict(
        (prefix+'_'+f,getattr(nt_obj,f)) for f in nt_obj._fields
    )

class Stop( Callable ):
    heading= (
        caravel.report.Report.headings
        + [ 'distance', 'time', ]
        + prefix_fields('stop', transit_system.Stop)
        + prefix_fields('stop_time', transit_system.Stop_Time)
        + prefix_fields('route', transit_system.Route)
        + prefix_fields('trip', transit_system.Trip) )
    def __init__( self, target=None ):
        self.wtr= csv.DictWriter( target, self.heading )
        self.wtr.writeheader()
        self.count= 0
    def __call__( self, report, distance, time, stop, stop_time, route, trip ):
        row= report.as_dict()
        row['distance']= distance
        row['time']= time
        row.update( prefix_dict('stop', stop ) )
        row.update( prefix_dict('stop_time', stop_time ) )
        row.update( prefix_dict('route', route ) )
        row.update( prefix_dict('trip', trip ) )
        self.wtr.writerow( row )
        self.count += 1

class NoStop( Callable ):
    heading= ( ['status']
        + caravel.report.Report.headings
        + prefix_fields('candidate_1', transit_system.Candidate)
        + prefix_fields('candidate_2', transit_system.Candidate)
        )
    def __init__( self, target=None ):
        self.wtr= csv.DictWriter( target, self.heading )
        self.wtr.writeheader()
        self.count= 0
    def __call__( self, status, report, dist_fit, time_fit ):
        row= report.as_dict()
        row['status']= status
        if dist_fit:
            row.update( prefix_dict('candidate_1', dist_fit ) )
        if time_fit:
            row.update( prefix_dict('candidate_2', time_fit ) )
        self.wtr.writerow( row )
        self.count += 1

def get_args():
    """Parse command-line arguments.
    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'files', action='store', nargs='*' )
    parser.add_argument( '--new', '-n', action='store_true', default=False, dest='acquire' )
    parser.add_argument( '--transit', '-t', action='store', default='google_transit.zip' )
    parser.add_argument( '--reject', '-r', action='store', default='no_stop.csv' )
    parser.add_argument( '--stop', '-s', action='store', default='stop.csv' )
    parser.add_argument( '--debug', '-d', action='store_true', default=False )
    args= parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )

    args= get_args()
    if args.debug:
        logging.getLogger().setLevel( logging.DEBUG )
    if args.acquire:
        latest= caravel.acquire.get_reports()
        files= [latest] + args.files
    else:
        files= args.files

    conn= transit_system.Connection( )
    conn.open( args.transit )

    with open( args.stop, 'wb' ) as stop_file:
        with open( args.reject, 'wb') as no_stop_file:
            stop= Stop( stop_file )
            no_stop= NoStop( no_stop_file )
            counts= arrival_at_stop( conn, files, no_stop= no_stop, stop=stop )

    logger.info( "Counts {0}".format( pprint.pformat( dict(counts) ) ) )
    logging.shutdown()
