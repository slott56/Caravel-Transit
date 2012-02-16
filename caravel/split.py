#!/usr/bin/env python2.7
"""Caravel raw file filter and split.

Synopsis:

    python2.7 -m caravel.split [-l location] [-a arrival] source...

Description:

For each source file, filter the invalid Reports.  Split into two CSV files.
One file gets Arrival and Dwell reports.  The other file gets Location reports.

"""
from __future__ import print_function, division
import csv
import pprint
import logging
import sys
import argparse
import caravel.report

logger= logging.getLogger( __name__ )

def split( report_iter, location_csv, arrival_csv ):
    """Split a collection of reports into two subclass: Locations and Arrivals.

    Generally, the report_iter is an instance of :func:`caravel.report.report_iter`.

    It's usually built like this::

        factory= caravel.report.ReportFactory()
        rpt_iter= caravel.report.report_iter( factory, [list,of,files] )

    This iterator will examine all the files in the list, extracting
    all Report objects.

    :param report_iter: an iterator over :class:`caravel.report.Report` instances.
    :param location_csv: Name of a file to open and write.  This gets Location reports.
    :param arrival_csv: Name of a file to open and write. This gets
        Arrival and Dwell reports.
    """
    counts= {'source':0, 'excluded': 0, 'invalid':0, 'location':0, 'arrival':0}
    with open(location_csv,'wb') as loc_file:
        loc_wtr= csv.DictWriter( loc_file, caravel.report.Report.headings )
        loc_wtr.writeheader()
        with open(arrival_csv,'wb') as arr_file:
            arr_wtr= csv.DictWriter( arr_file, caravel.report.Report.headings )
            arr_wtr.writeheader()
            for item in report_iter:
                counts['source'] += 1
                if not item:
                    counts['invalid'] += 1
                    continue
                if not (item.ll_valid and item.odom_valid):
                    logger.debug( 'Excluded {0!r}'.format(item) )
                    counts['excluded'] += 1
                    continue

                if item.rte:
                    # Route?  It's an Arrival or a Dwell
                    arr_wtr.writerow( item.as_dict() )
                    counts['arrival'] += 1
                else:
                    # No Route?  It's a Location
                    loc_wtr.writerow( item.as_dict() )
                    counts['location'] += 1
    return counts

def get_args():
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'files', action='store', nargs='*' )
    parser.add_argument( '--location', '-l', action='store', default='location.csv' )
    parser.add_argument( '--arrival', '-a', action='store', default='arrival.csv' )
    parser.add_argument( '--debug', '-d', action='store_true', default=False )
    args= parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    args= get_args()
    if args.debug:
        logging.getLogger().setLevel( logging.DEBUG )
    factory= caravel.report.ReportFactory()
    counts= split(
        caravel.report.report_iter( factory, args.files ),
        args.location,
        args.arrival )
    logger.info( "Counts {0}".format( pprint.pformat( counts ) ) )
    logging.shutdown()
