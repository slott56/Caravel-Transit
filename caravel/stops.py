#!/usr/bin/env python2.7
"""Simple route and stop analysis to cluster location reports by
reported route and direction.

Synopsis

    python2.7 -m caravel.stops source...

Description

    For each source file, filter the invalid Reports.  Summarize the
    Arrival and Dwell reports.


Options

    ..  program:: stops

    .. option:: --debug, -d

        Set logging level.

    ..  option:: --format number

        Format number.  Generally maps to a subclass of :class:`caravel.report.ReportReader`.

    .. option:: source...

        List of source files to process.

Components

    ..  autofunction:: group_by_rte_dir_stop

    ..  autofunction:: display

    ..  autofunction:: get_args
"""
from __future__ import print_function, division
from collections import defaultdict, namedtuple, OrderedDict
import datetime
import pprint
import logging
import sys
import argparse
import caravel.report

logger= logging.getLogger( __name__ )

Details = namedtuple( 'Details', [ 'rte', 'dir', 'stop', 'id', 'dwell', 'time' ])

def group_by_rte_dir_stop( report_iter ):
    """Accumulate stops from a sequence of Arrivals.

    Generally, the report_iter is an instance of :func:`caravel.report.report_iter`.

    It's usually built like this::

        reader= caravel.report.ReportReader_v1()
        rpt_iter= caravel.report.report_iter( reader, [list,of,files] )

    This iterator will examine all the files in the list, extracting
    all Report objects.

    :param report_iter: an iterator over :class:`caravel.report.Report` instances.
    :returns: two values: (counts, route).  The counts is a dictinary of input, excluded, invalid
        and arrivals actually processed.
        The route is an OrderedDict, keyed by Route/Dir/Stop with sequence of arrival times.
    """
    counts= {'source':0, 'excluded': 0, 'invalid':0, 'arrival':0}
    route_dir= defaultdict(list)

    for item in report_iter:
        counts['source'] += 1
        if not item:
            counts['invalid'] += 1
            continue
        if not item.ll_valid:
            logger.debug( 'Excluded {0!r}'.format(item) )
            counts['excluded'] += 1
            continue
        if not item.rte:
            logger.debug( 'Excluded {0!r}'.format(item) )
            counts['excluded'] += 1
            continue
        counts['arrival'] += 1

        try:
            dwell= item.dwell
        except AttributeError:
            dwell= None
        dtl= Details( item.rte, item.dir, item.stop, item.id, dwell, item.time )
        route_dir[dtl.rte,dtl.dir,dtl.stop].append( dtl )

    for rds in route_dir:
        route_dir[rds].sort()

    return counts, OrderedDict( sorted( route_dir.items() ) )

def display( route_dir ):
    """Display the accumulated raw data.

    :param route_dir: OrderedDict, keyed by Route/Dir/Stop with sequence of arrival times.
    """
    print( "Route, Direction, Stop, Time and Dwell")
    print( "  R D    S Time and Dwell")
    print( "=== = ==== ==============")
    for r,d,s in route_dir:
        times= tuple( "{0.time} {0.dwell!r}".format(rpt) for rpt in route_dir[r,d,s] )
        print( "{0:3s} {1:1s} {2:4s} {3:s}".format(r,d,s, times) )

    return counts

def get_args():
    """Parse command-line arguments.
    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'files', action='store', nargs='*' )
    parser.add_argument( '--format', '-f', action='store', default='2' )
    parser.add_argument( '--debug', '-d', action='store_true', default=False )
    args= parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    args= get_args()
    if args.debug:
        logging.getLogger().setLevel( logging.DEBUG )
    rdr_class = {
        '1': caravel.report.ReportReader_v1,
        '2': caravel.report.ReportReader_v2,
        '3': caravel.report.ReportReader_v3,
        }
    reader= rdr_class[args.format]()
    started= datetime.datetime.now()
    counts, route = group_by_rte_dir_stop(
        caravel.report.report_iter( reader, args.files ) )
    display( route )
    finished= datetime.datetime.now()
    logger.info( "Time {0}; Counts {1}".format( finished-started, pprint.pformat( counts ) ) )
    logging.shutdown()
