#!/usr/bin/env python2.7
"""Caravel Arrival Time and Location Matching Statistics

This examines a suite of \*.rpt files to get a bunch of Arrival and Dwell
reports.  It matches the Arrival and Dwell reports against the transit map,
getting a fairly large number of candidate matches.

..  autofunction:: arrival_stats

"""
from __future__ import print_function, division
import os
import transit_system
import statistics
from collections import defaultdict
import caravel.report
import glob
import pprint

def arrival_stats( reader, conn, base='.' ):
    """Use the :meth:`transit_system.connection.get_candidate_stops` to locate
    stops.  Compare the shortest distance stop with stops farther away to see
    if the time match of a later stop is better than the time match of the
    closest stop.
    """
    count= 0
    matches= defaultdict(list)
    for report in caravel.report.report_iter( reader, glob.glob( os.path.join(base,'*.rpt') ) ):
        if report and report.rte: # Arrival or Dwell
            count += 1
            services= tuple( transit_system.get_services_today(conn, report.timestamp.date() ) )
            if not services:
                print( "***Services could not be found for {0!r}".format(report) )
                continue
            #print()
            #print( arrival, services )
            candidates = list( transit_system.get_candidate_stops(conn, (report.lat, report.lon), report.time, services, max_dist=1.0) )
            #print( [ (c.distance,c.time,c.stop.stop_id) for c in candidates ] )

            if len(candidates) == 0:
                print( "No stop for", report )
                continue

            step = 0
            for s in range(1,len(candidates)):
                if abs(candidates[s].time) < abs(candidates[0].time):
                    step= s
                    break
            matches[step].append( candidates )

    print()
    print( "Reports", count )
    for s in matches:
        fq= statistics.FQTable()
        for candidates in matches[s]:
            distance_to_better= 16*int((candidates[s].distance)//16)
            fq[distance_to_better] += 1
        print()
        print( s )
        pprint.pprint( dict(fq) )
        mean, std = fq.mean(), fq.sd()
        if std:
            print( "{0:d}, {1:5.0f}, {2:5.0f}, {3:3d}".format( s, fq.mean(), fq.sd(), fq.count ) )
        else:
            print( "{0:d}, {1:5.0f}, {2:>5s}, {3:3d}".format( s, fq.mean(), "None", fq.count ) )

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
    reader= caravel.report.ReportReader_v2()

    arrival_stats( reader, conn )