#!/usr/bin/env python2.7
"""Filter and split raw input to separate Location reports from Arrival reports.

Synopsis

::

    python2.7 -m caravel.split [--new] [-l location] [-a arrival] source...

Description

    For each source file, filter the invalid Reports.  Split into two CSV files.
    One file gets Arrival and Dwell reports.  The other file gets Location reports.

Options

    ..  program:: split

    ..  option:: --format number

        Format number.  Generally maps to a subclass of :class:`caravel.report.ReportReader`.

    ..  option:: --new, -n

        Get a new, live report file.

    .. option:: --location <file>, -l <file>

        The name of the Location reports ('location.csv' is the default)

    .. option:: --arrival <file>, -a <file>

        The name of the Arrival/Dwell reports ('arrival.csv' is the default)

    .. option:: source...

        List of source files to process.

Components

    ..  autofunction:: split

    ..  autofunction:: get_args
"""
from __future__ import print_function, division
import csv
import pprint
import logging
import sys
import argparse
import caravel.report
import caravel.acquire

logger= logging.getLogger( __name__ )

def split( report_iter, location_csv, arrival_csv ):
    """Split a collection of reports into two subclass: Locations and Arrivals.

    Generally, the report_iter is an instance of :func:`caravel.report.report_iter`.

    It's usually built like this::

        reader= caravel.report.ReportReader_v1()
        rpt_iter= caravel.report.report_iter( reader, [list,of,files] )

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
                if not item.ll_valid:
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
    """Parse command-line arguments.
    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'files', action='store', nargs='*' )
    parser.add_argument( '--format', '-f', action='store', default='2' )
    parser.add_argument( '--new', '-n', action='store_true', default=False, dest='acquire' )
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
    if args.acquire:
        files= [caravel.acquire.get_reports()] + args.files
    else:
        files= args.files
    rdr_class = {
        '1': caravel.report.ReportReader_v1,
        '2': caravel.report.ReportReader_v2,
        }
    reader= rdr_class[args.format]()
    counts= split(
        caravel.report.report_iter( reader, files ),
        args.location,
        args.arrival )
    logger.info( "Counts {0}".format( pprint.pformat( counts ) ) )
    logging.shutdown()
