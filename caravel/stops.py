#!/usr/bin/env python2.7
"""Caravel route and stop analysis.

Synopsis:

    python2.7 -m caravel.stops source...

Description:

For each source file, filter the invalid Reports.  Summarize the
Arrival and Dwell reports.

..  autofunction:: stops

..  autofunction:: get_args
"""
from __future__ import print_function, division
from collections import defaultdict, namedtuple
import datetime
import pprint
import logging
import sys
import argparse
import caravel.report

logger= logging.getLogger( __name__ )

Details = namedtuple( 'Details', [ 'rte', 'dir', 'stop', 'id', 'dwell', 'time' ])

def stops( report_iter ):
    """Accumulate stops from a sequence of Arrivals.

    Generally, the report_iter is an instance of :func:`caravel.report.report_iter`.

    It's usually built like this::

        factory= caravel.report.ReportFactory()
        rpt_iter= caravel.report.report_iter( factory, [list,of,files] )

    This iterator will examine all the files in the list, extracting
    all Report objects.

    :param report_iter: an iterator over :class:`caravel.report.Report` instances.
    """
    counts= {'source':0, 'excluded': 0, 'invalid':0, 'arrival':0}
    route_dir= defaultdict(list)

    for item in report_iter:
        counts['source'] += 1
        if not item:
            counts['invalid'] += 1
            continue
        if not (item.ll_valid and item.odom_valid):
            logger.debug( 'Excluded {0!r}'.format(item) )
            counts['excluded'] += 1
            continue
        if not item.rte:
            logger.debug( 'Excluded {0!r}'.format(item) )
            counts['excluded'] += 1
            continue
        counts['arrival'] += 1

        dtl= Details( item.rte, item.dir, item.stop, item.id, item.dwell, item.time )
        route_dir[dtl.rte,dtl.dir,dtl.stop].append( dtl )

    print( "History By Route, Direction, Stop")
    print( "=================================")
    for r,d,s in sorted(route_dir):
        times= tuple( "{0.time} {0.dwell!r}".format(rpt) for rpt in route_dir[r,d,s] )
        print( "{0:3d} {1:1d} {2:3d} {3:s}".format(r,d,s, times) )

    return counts

def get_args():
    """Parse command-line arguments.
    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'files', action='store', nargs='*' )
    parser.add_argument( '--debug', '-d', action='store_true', default=False )
    args= parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    args= get_args()
    if args.debug:
        logging.getLogger().setLevel( logging.DEBUG )
    started= datetime.datetime.now()
    factory= caravel.report.ReportFactory()
    counts= stops(
        caravel.report.report_iter( factory, args.files ) )
    finished= datetime.datetime.now()
    logger.info( "Time {0}; Counts {1}".format( finished-started, pprint.pformat( counts ) ) )
    logging.shutdown()
