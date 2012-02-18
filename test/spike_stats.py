"""Spike the three-tier stats model.

-   History of route arrivals.

-   Daily adjustment.

-   Last-Stop FIFO.

Live Data
==========

Here's a typical sequence of data.
This listing has a number of ``route, direction, stop ('time dwell',...)`` instances.


::

    26 1  31 ('07:04:56 97', '14:04:28 104')
    26 1  45 ('07:20:15 None',)
    26 1 134 ('09:21:32 561',)
    26 1 140 ('09:31:27 10',)
    26 2  46 ('07:20:24 9',)
    26 2 221 ('11:13:57 None',)
    27 1 381 ('09:45:47 None',)
    27 1 458 ('10:46:38 11',)
    27 1 1188 ('19:53:29 None',)
    27 2 147 ('07:05:26 44',)
    27 2 333 ('09:21:18 442',)
    27 2 335 ('09:20:34 None', '09:20:34 None')
    27 2 481 ('11:12:17 56',)
    27 2 717 ('14:04:46 45',)

This shows three features.

-   Route 26, direction 1, stop 31 was visited twice.  This is a scheduled stop.
    Each day, the approximate sequence times will repeat.

-   Route 27, direction 2, stop 335 got duplicate reports.  This happens.

-   Route 26, direction 1, stop 45 (among many others) was missing.
    In this case,
    the various samples analyzed had time gaps.  Pragmatically, missing
    data must be tolerated.

Sample Data
================

We'll use a stand-in for Dwell/Arrival reports, :class:`Report`.

We'll use a considerably simpler collection of routes with just 4 stops each.
This gives us a first, last and two middle stops on each route.

We'll fabricate a schedule that cycles just four times through the stops.
This allows each cycle to omit a stop, leading to a matrix with gaps.
It also means that we have a very small statistical base for computing mean
arrival times.

There are :math:`4! = 24` permutations of 4 stops.
"""
from __future__ import print_function, division
from collections import namedtuple, defaultdict
from itertools import permutations, tee
import datetime
import random
import math
import pprint

Report = namedtuple( "Report", ("id", "time", "rte", "dir", "stop") )

def sample_data_iter():
    """A snapshot of some output."""
    stops_output = """
 26 1  31 ('07:04:56 97', '14:04:28 104')
 26 1  45 ('07:20:15 None',)
 26 1 134 ('09:21:32 561',)
 26 1 140 ('09:31:27 10',)
 26 2  46 ('07:20:24 9',)
 26 2 221 ('11:13:57 None',)
 27 1 381 ('09:45:47 None',)
 27 1 458 ('10:46:38 11',)
 27 1 1188 ('19:53:29 None',)
 27 2 147 ('07:05:26 44',)
 27 2 333 ('09:21:18 442',)
 27 2 335 ('09:20:34 None', '09:20:34 None')
 27 2 481 ('11:12:17 56',)
 27 2 717 ('14:04:46 45',)
"""

    for line in (l.strip() for l in stops_output.splitlines()):
        if not line: continue
        head, _, tail = line.partition('(')
        rte, dir, stop = map( int, head.split() )
        for time_dwell in tail[:-1].split(','):
            if not time_dwell: continue
            time, _, dwell = time_dwell.strip()[1:-1].partition(' ')
            t = datetime.datetime.strptime( time, "%H:%M:%S").time()
            rpt= Report( '1111', t, rte, dir, stop )
            yield rpt

def synth_data_iter():
    """Synthesize data for route discovery.

    This generates data for two routes.  Each route will have four stops.
    Data is generated over 24 "days", each day has a different
    permutation of omitted Arrival data in the schedule.

    For a given route, 24 days of data are generated; each day has a different
    permutation of missing data.

    For a given day of a given route, four cycles are generated. This assures
    that all permutations are used.  More cycles would repeat permutations.
    Fewer cycles would omit permutations.

    The stop id number orders are randomized.  For each route, both directions
    are created.  For this example, they are precise reciprocals.

    The arrival times are generally about 10 minutes (600 seconds) apart.
    A random factor of :math:`\pm 60` is used to make sure times aren't simple
    repeats.

    :returns: iterator over Report instances.
    """
    num_stops= 4
    num_routes= 2
    base_date= datetime.datetime.today().date()
    print( base_date )
    for route in range(num_routes):
        stop_id = [ random.randrange(1,256) for i in range(num_stops) ]
        for day, gaps in enumerate(permutations( range(num_stops) )):
            base_time= datetime.datetime.combine( base_date, datetime.time(7, route, 0) )
            for cycle in range(4): # number of stops; uses all permutations once
                dir= 0
                for stop in range(num_stops):
                    if stop == gaps[cycle]: continue
                    sequence = stop + num_stops*dir + cycle*num_stops*2
                    offset = sequence*600 + random.randrange( -60, 60 )
                    td= base_time+datetime.timedelta( days= day, seconds=offset )
                    yield Report( id='1111', time=td, rte=route, dir=dir+1, stop=stop_id[stop] )
                dir= 1
                for stop in range(num_stops):
                    if stop == gaps[cycle]: continue
                    sequence = stop + num_stops*dir + cycle*num_stops*2
                    offset = sequence*600 + random.randrange( -60, 60 )
                    td= base_time+datetime.timedelta( days= day, seconds=offset )
                    yield Report( id='1111', time=td, rte=route, dir=dir+1, stop=stop_id[-stop-1] )

def count( samples ):
    return sum( 1 for s in samples )

def mean( samples ):
    s_iter, c_iter = tee( samples, 2 )
    return sum(s_iter) / count(c_iter)

def stddev( samples ):
    m_iter, sd_iter, c_iter = tee( samples, 3 )
    m= mean(m_iter)
    sumsq= sum( (x-m)**2 for x in sd_iter )
    return math.sqrt( sumsq/count(c_iter)-1)

def group_by_rte_dir_stop( data ):
    """Since the GPS reports are in time order, we need to parition them
    by route/direction/stop and date.

    This creates a RDS (Route/Direction/Stop) dictionay that
    contains each day's times.

    ::

        { (1,2,3): { 10/11/12: (7:08, 8:09, 9:10), 10/12/12: (7:09, 8:08) },
          (1,2,4): { 10/11/12: (7:18, 8:19, 9:20), 10/12/12: (7:19, 8:18) },
        }

    :param data: An iterable of :class:`Report` instances.  Usually :func:`synth_data_iter`.
    :returns: Dictionary keyed by Route/Direction/Stop.  Each value in that
        is a dictionary keyed by day.  Each value is a time.
    """
    reports = defaultdict( lambda: defaultdict(set) )
    for rpt in data:
        reports[rpt.rte, rpt.dir, rpt.stop][rpt.time.date()].add( rpt.time )
    return reports

def cluster_times( reports ):
    """Correlate arrival times across the various days in the data set to
    create a cluster of times for each R/D/S with a minimal deviation.

    For a given route/direction/stop, step through each day's arrival
    times at that stop.  These times are spread throughout the day, based
    on various trips around the route.

    Assume that the first day's reported times reflect the scheduled visit times.
    Build a "visits" sequence.  Each element of this sequence is a sublist
    of actual times.  Initially, the sublists only have a sigle time.

    For each day after the first:

    -   For each stop in that day:

        *   For each cluster of assumed visit times (initially based on the first day).
            (Note that this is inefficient; we should use just a few adjacent clusters).

            +   Compute the standad deviation of the cluster of assumed visit times,
                using the new stop as the mean time.

        *   The cluster of assumed visit times which has the smallest deviation
            gets this new time assigned to it.

        *   If the deviations are all "large", then this is a new visit time that
            doesn't correlate with any of the times seen so far.
            (For example, the first day was incomplete.)
            Create a new assumed visit time for this
            stop.  The cluster has this outlier time in it.

    When all days have been examined for a given R/D/S combination, the sequence
    of visit times has clusters that *should* match the official bus schedule.

    Each cluster is reduced to a mean and a standard deviation.  This shows the
    "expected" arrival time and provides a statistical window for boundary times.

    This sequence of expected arrival and standard deviations form the schedule for
    a given Route/Direction/Stop during the day.

    ..  todo:: Day-of-Week.

        Separate by day-of-week to allow weekend schedules to vary from
        weekday schedules.

    :param reports: A dictionary of dictionaries.  The top key is R/D/S.  Each
        inner dictionary is keyed by date and has a list of times.
        See :func:`group_by_rte_dir_stop`.

    :returns: A sequence of ((R/D/S), Time Sequence) tuples.  The Time Sequence
        contains an ordered list of (mean, standard deviation) 2-tuples for each
        arrival time at the route/direction/stop.
    """
    for r, d, s in reports:
        arrivals = []
        date_iter = iter(sorted( reports[r,d,s] ))

        date_current= next(date_iter)
        datetime_current= datetime.datetime.combine( date_current, time=datetime.time(0,0,0) )
        visits= list( sorted( [(dt-datetime_current).seconds] for dt in reports[r,d,s][date_current] ) )
        ##print( date_current, visits )

        for date_current in date_iter:
            datetime_current= datetime.datetime.combine( date_current, time=datetime.time(0,0,0) )
            stops= tuple( sorted( (r-datetime_current).seconds for r in reports[r,d,s][date_current] ) )
            ##print( r, d, s, date_current, stops )
            for stop in stops:
                deltas = []
                for i in range(len(visits)):
                    deltas.append( (math.sqrt(sum( (v-stop)**2 for v in visits[i] )/len(visits[i])), i) )
                min_value, index = min(deltas)
                if min_value < 480: # Assumption: 10 minutes between stops plus or minus 2.
                    visits[index].append(stop)
                else:
                    visits.append( [stop] )
                    visits.sort()
            ##print( date_current, visits )

        for candidate_times in visits:
            m_time = mean(candidate_times)
            if len(candidate_times)>2:
                s_time= stddev(candidate_times)
            else:
                s_time= None
            hh = int(m_time//3600)
            mm = int((m_time-3600*hh)//60)
            ss = int(m_time-(60*hh+mm)*60)
            arrivals.append( ( datetime.time(hh,mm,ss), s_time ) )
        arrivals.sort()
        yield (r,d,s), arrivals

def build_route( schedule ):
    """Build the route/direction summary as a sequence of stops throughout
    the day.  This is a small reorganization of the R/D/S schedule
    information to be a dictionary, keyed by R/D with a sequence of time-ordered stops.

    :param schedule: An iterator over 2-tuples of (R,D,S) and ( (time,std), (time,std), ... )
    :return: A dictionary with keys of (R,D) and values of ( (S,Time,Std), ... )
    """
    route = defaultdict(list)
    for rds, arrivals in schedule:
        r, d, s = rds
        for time_0, std_time in  arrivals:
            route[r,d].append( (s,time_0,std_time) )
    for r,d in route:
        route[r,d].sort(key=lambda t:t[1])
    return route

def main():
    # Step 1.  Organize raw data by route/direction/stop.
    reports = group_by_rte_dir_stop( synth_data_iter() )
    ##pprint.pprint( dict(reports) )

    # Step 2.  Correlate times to discover repeat visits to a stop.
    schedule_iter= cluster_times( reports )
    #schedule= dict( schedule_iter )
    #pprint.pprint( schedule )
    #schedule_iter= schedule.items()

    # Step 3. Transform to a route/direction structure with a time-ordered
    # sequence of stops that spans the entire day.
    route= build_route( schedule_iter )

    pprint.pprint( dict( route ) )

    ## Given the routes, we can then do a search based on stop and current time
    ## to locate next stop.

if __name__ == "__main__":
    main()