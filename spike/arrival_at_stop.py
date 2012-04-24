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

    ..  option:: --format number

        Format number.  Generally maps to a subclass of :class:`caravel.report.ReportReader`.

    ..  option:: --new

        Get a new .rpt file and process it.

    ..  option:: --transit transit_details, -t transit_details

        Directory (or .ZIP) with HRT details.

    ..  option:: --reject no_stop.csv, -r no_stop.csv

        Reject file to which Reports are written for which there is no stop.

    ..  option:: --stop stop.csv, -s stop.csv

        Stops file to which Report, Stop, Stop Time, Route and Trip information
        is written.

Algorithm Components

    The core stop-finding algorithm is implemented via the :class:`StopFinder`
    class hierarchy.

    The :func:`arrival_at_stop` process applies this algorithm, and writes
    the successful results using a :class:`WriteStop` instance.  The failures
    are written using a :class:`WriteNoStop` instance.

    ..  autofunction:: arrival_at_stop

    ..  autoclass:: InvalidReport
    ..  autoclass:: NoStopFound

    ..  autoclass:: StopFinder
        :members:

    ..  autoclass:: StopFinder_Route_Trip
        :members:

    ..  autoclass:: StopFinder_Next_Stop
        :members:

Output Components

    ..  autofunction:: prefix_fields
    ..  autofunction:: prefix_dict

    ..  autoclass:: WriteStop
        :members:
        :special-members:

    ..  autoclass:: WriteNoStop
        :members:
        :special-members:

    ..  autofunction:: get_args
"""
from __future__ import print_function, division
from collections import defaultdict, Callable, namedtuple, Sequence
import datetime
import csv
import os
import glob
import caravel.report
import caravel.transit_system.load
import caravel.LogCapture.ftp_acquire
import pprint
import logging
import sys
import argparse
import math

logger= logging.getLogger( __name__ )

class InvalidReport( Exception ):
    """The Report was either a Location or invalid in some other way
    for locating a stop."""
    pass

class NoStopFound( Exception ):
    """No stop could be found.  The arguments include
    a message, and up to two candidate stops.
    """
    pass

Candidate = namedtuple('Candidate', ['distance', 'time', 'stop', 'stop_time'] )

def radians( degrees ):
    return math.pi*degrees/180

def degrees( radians ):
    return 180*radians/math.pi

def dist_approx( p1, p2 ):
    """The Equirectangular Approximation for distance between two coordinates.
    Fast and reasonably accurate.

    See :ref:`design.distance` for details.

    :param p1: (lat,lon) 2-tuple
    :param p2: (lat,lon) 2-tuple
    :returns: distance in statute miles.
    """
    lat1, lon1 = map( radians, p1 )
    lat2, lon2 = map( radians, p2 )
    x = (lon2-lon1) * math.cos((lat1+lat2)/2)
    y = (lat2-lat1)
    c = math.hypot(x,y)
    return 3961.3*c # 3440.07 for nm, 3961.3 for statute miles, 6378.1 for km, 20915664.0 for feet

def time_parse( text ):
    """Transform HH:MM:SS string into seconds past midnight.
    Unlike :mod:`datetime`, this does not mind times >= 24:00:00.

    :param string: String of the form HH:MM:SS
    :return: seconds past midnight
    """
    hh, mm, ss = map(int, text.split(':'))
    return (hh*60+mm)*60+ss

class MockDB( object ):
    """A database-like structure for transit system queries."""
    weekday_name = 'monday,tuesday,wednesday,thursday,friday,saturday,sunday'.split(',')
    def __init__( self, accessor ):
        self.accessor= accessor
        if self.accessor:
            # load various working tables.
            with self.accessor.open( 'calendar.txt' ) as source:
                rdr= csv.DictReader( source )
                self._load_calendar(rdr)
            with self.accessor.open( 'calendar_dates.txt' ) as source:
                rdr= csv.DictReader( source )
                self._load_calendar_dates(rdr)
            with self.accessor.open( 'routes.txt' ) as source:
                rdr= csv.DictReader( source )
                self._load_routes(rdr)
            with self.accessor.open('stops.txt' ) as source:
                rdr= csv.DictReader( source )
                self._load_stops(rdr)
            with self.accessor.open( 'trips.txt' ) as source:
                rdr= csv.DictReader( source )
                self._load_trips(rdr)
            with self.accessor.open('stop_times.txt' ) as source:
                rdr= csv.DictReader( source )
                self._load_stop_times(rdr)
    def _load_calendar(self, rdr):
        services_by_date= defaultdict(set)
        for row in rdr:
            start_date= datetime.datetime.strptime( row['start_date'], '%Y%m%d' ).date()
            end_date= datetime.datetime.strptime( row['end_date'], '%Y%m%d' ).date()
            for d in xrange((end_date-start_date).days+1):
                date= start_date + datetime.timedelta(days=d)
                day_name= self.weekday_name[date.weekday()]
                if row[day_name] == '1':
                    services_by_date[date].add(row['service_id'])
        self.services_by_date= services_by_date
    def _load_calendar_dates(self, rdr):
        for row in rdr:
            date= datetime.datetime.strptime( row['date'], '%Y%m%d' ).date()
            serv= self.services_by_date[date]
            if serv:
                if row['exception_type'] == '1': # Add
                    serv.add( row['service_id'])
                elif row['exception_type'] == '2' and row['service_id'] in serv: # Remove
                    serv.remove( row['service_id'])
                elif row['exception_type'] == '2' and row['service_id'] not in serv:
                    # Wasn't there to begin with?  Weird.
                    pass
                else:
                    raise GTFException( "Unknown Calendar Date {0!r}".format(row) )
            else:
                # Missing date?  Weird.
                pass
    def _load_routes(self, rdr):
        self.routes= {}
        for row in rdr:
            row['trips']= {}
            self.routes[row['route_id']]= row
    def _load_stops(self, rdr):
        self.stops= {}
        for row in rdr:
            row['stop_lat']= float(row['stop_lat'])
            row['stop_lon']= float(row['stop_lon'])
            row['trips']= {}
            self.stops[row['stop_id']]= row
    def _load_trips(self, rdr):
        self.trip= {}
        self.trip_by_route= defaultdict(list)
        for row in rdr:
            self.trip[ row['trip_id'] ]= row
            self.trip_by_route[ row['route_id'] ].append( row )
    def _load_stop_times(self, rdr):
        for row in rdr:
            row['arrival_time']= time_parse(row['arrival_time'])
            row['departure_time']= time_parse(row['departure_time'])

            trip= self.trip[row['trip_id']]

            route= self.routes[trip['route_id']]
            if trip['service_id'] not in route['trips']:
                route['trips'][ trip['service_id'] ]= {}
            if trip['trip_id'] not in route['trips'][trip['service_id']]:
                route['trips'][ trip['service_id'] ][trip['trip_id']] = dict(
                        direction_id= trip['direction_id'],
                        block_id= trip['block_id'],
                        stops= [], )
            route_trip= route['trips'][ trip['service_id'] ][trip['trip_id']]
            route_trip['stops'].append( row )

            stop = self.stops[row['stop_id']]
            if trip['service_id'] not in stop['trips']:
                stop['trips'][ trip['service_id'] ]= {}
            if trip['trip_id'] not in stop['trips'][trip['service_id']]:
                stop['trips'][ trip['service_id'] ][trip['trip_id']] = dict(
                        direction_id= trip['direction_id'],
                        block_id= trip['block_id'],
                        route= trip['route_id'],
                        times= [], )
            stop_trip= stop['trips'][ trip['service_id'] ][trip['trip_id']]
            stop_trip['times'].append( row )

    def get_services_today( self, date ):
        return self.services_by_date[date]

    def get_closest_times_in_service( self, stop_id, time, services, min_time=None, max_time=None ):
        stop= self.stops[stop_id]
        trips = []
        for svc in services:
            trips.extend( stop['trips'].get(svc,{}).values() )
        times = ( (st['arrival_time']-time, st)
            for t in trips
            for st in t['times']
            )
        if min_time is not None:
            times = ( (time,stop) for time,stop in times if time >= min_time )
        if max_time is not None:
            times = ( (time,stop) for time,stop in times if time < max_time )
        return sorted(times, key=lambda x: abs(x[0]) )

    def get_closest_stops( self, lat_lon, max_dist=None ):
        distances= ( (dist_approx( lat_lon, (s['stop_lat'],s['stop_lon']) ), s)
            for s in self.stops.values() )
        if max_dist is not None:
            distances = ( (dist,stop) for dist,stop in distances if dist < max_dist )
        return sorted(distances)

    def get_candidate_stops( self, lat_lon, time, services, max_dist=None, min_time=None, max_time=None, count=6 ):
        if max_dist is None: max_dist = 0.1 # subjective break between continuous and sparse
        if min_time is None: min_time = -(96.2+92.4*1)
        if max_time is None: max_time = 96.2+92.4*3
        distances= self.get_closest_stops( lat_lon, max_dist=max_dist )
        for distance, stop in distances:
            h= 0
            for delta, stop_time in self.get_closest_times_in_service( stop['stop_id'], time, services, min_time=min_time, max_time=max_time ):
                h= 1
                yield Candidate(int(distance*5280), delta, stop, stop_time)
            count -= h
            if count == 0: break
    def get_route_from_stop_time( self, candidate ):
        ##print( "get_route_from_stop_time", candidate )
        trip= self.trip[ candidate['trip_id'] ]
        return self.routes[trip['route_id']]
    def get_trip_from_stop_time( self, candidate ):
        ##print( "get_trip_from_stop_time", candidate )
        trip= self.trip[ candidate['trip_id'] ]
        return self.trip[trip['trip_id']]
    def get_next_stop_time( self, candidate, services ):
        ##print( "get_next_stop_time", candidate )
        # Given trip_id, get trip.
        trip= self.trip[ candidate['trip_id'] ]
        route= self.routes[ trip['route_id'] ]
        # Given stop sequence, find next step
        for svc in services:
            stops= route['trips'].get(svc,{})
            if stops:
                for dir in stops.values():
                    for s in dir['stops']:
                        if s['stop_sequence'] > candidate['stop_sequence']:
                            yield s

class StopFinder( object ):
    """The Stop-Finder algorithm."""
    def __init__( self, connection ):
        """Build a StopFinder for a given :class:`caravel.transit_system.load.Accessor`.

        :param connection: open :class:`caravel.transit_system.load.Accessor`.
        """
        self.connection= MockDB(connection)
    def process_report( self, report ):
        """Process a single Arrival or Dwell report.

        1.  Get services available for this date.

        2.  Get closest stops.

        3.  Get stops closest in time.

        4.  Add supplemental data.

        :param report: :class:`caravel.report.Report` instance.
        """
        if not (report and report.rte): # Arrival or Dwell
            raise InvalidReport( report )

        services= tuple( self.connection.get_services_today( report.timestamp.date() ) )
        if not services:
            raise NoStopFound( "Bad Date" )

        # Some analysis seems to indicate that 528 feet is far enough away.
        candidates = list( self.connection.get_candidate_stops( (report.lat, report.lon), report.time, services, max_dist=0.10) )

        if len(candidates) == 0:
            wider= 0.5 # # Search out as far as 2640 feet away.
            candidates = list( self.connection.get_candidate_stops( (report.lat, report.lon), report.time, services, max_dist=wider) )
            try:
                dist_fit= min( candidates, key=lambda x: x.distance )
                time_fit= min( candidates, key=lambda x: abs(x.time) )
                if dist_fit.distance == time_fit.distance and dist_fit.time == time_fit.time:
                    raise NoStopFound( ">0.10", dist_fit )
                else:
                    raise NoStopFound( ">0.10", dist_fit, time_fit )
            except ValueError:
                # usually ValueError: min() arg is an empty sequence
                raise NoStopFound( ">{0:.2f}".format(wider) )

        # Candidate with minimum time from scheduled stop.
        best_candidate= min( candidates, key=lambda x: abs(x.time) )

        # Fold in supplemental data.
        self.services= services
        return self.supplement( best_candidate )
    @staticmethod
    def heading( ):
        """Return headings which match the return value from :meth:`supplement`."""
        return ( caravel.report.headings
        + [ 'distance', 'time', ]
        + prefix_fields('stop', 'stop_id,stop_name,stop_lat,stop_lon'.split(',') )
        + prefix_fields('stop_time', 'trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint'.split(',') ) )
    def supplement( self, candidate ):
        """Fold in supplemental data.  The superclass does nothing extra.

        :param best_fit: a :class:`Candidate` instance.
        :returns: a new Best_Fit instance or possibly the unmodified candidate.
        """
        return candidate

class StopFinder_Route_Trip( StopFinder ):
    """The Stop-Finder algorithm.  This folds in route and trip
    supplemental data.
    """
    Best_Fit= namedtuple( "Best_Fit", ['distance', 'time', 'stop', 'stop_time', 'route', 'trip'] )

    @staticmethod
    def heading( ):
        """Return headings which match the return value from :meth:`supplement`."""
        return ( StopFinder.heading()
        + prefix_fields('route', 'route_id,route_short_name,route_long_name,route_desc,route_type,route_url'.split(','))
        + prefix_fields('trip', 'route_id,service_id,trip_id,direction_id,block_id'.split(',')) )

    def supplement( self, best_fit ):
        """Fold in some extra data, the route and trip that apply to this stop.

        :param best_fit: :class:`Candidate` object
        :returns: a :class:`StopFinder_Route_Trip.Best_Fit` instance.
        """
        row= super( StopFinder_Route_Trip, self ).supplement( best_fit )
        route= self.connection.get_route_from_stop_time( best_fit.stop_time )
        trip= self.connection.get_trip_from_stop_time( best_fit.stop_time )

        return StopFinder_Route_Trip.Best_Fit( row.distance, row.time, row.stop, row.stop_time, route, trip )

class StopFinder_Next_Stop( StopFinder ):
    """The Stop-Finder algorithm.  This folds in route and next stop_time
    supplemental data.
    """
    Best_Fit= namedtuple( "Best_Fit", ['distance', 'time', 'stop', 'stop_time', 'route', 'next'] )
    @staticmethod
    def heading( ):
        """Return headings which match the return value from :meth:`supplement`."""
        return ( StopFinder.heading()
        + prefix_fields('route', 'route_id,route_short_name,route_long_name,route_desc,route_type,route_url'.split(',') )
        + prefix_fields('next', 'stop_id,stop_name,stop_lat,stop_lon'.split(',')) )

    def supplement( self, best_fit ):
        """Fold in some extra data, the next scheduled stop.

        :param best_fit: :class:`Candidate` object
        :returns: a :class:`StopFinder_Next_Stop.Best_Fit` instance.
        """
        row= super( StopFinder_Next_Stop, self ).supplement( best_fit )
        next_stops= self.connection.get_next_stop_time( best_fit.stop_time, self.services )
        try:
            single_next= next( next_stops )
        except StopIteration:
            # Empty List!
            trip= self.connection.get_trip_from_stop_time( best_fit.stop_time )
            logger.error( 'No Next Stop for {0!r} on {1!r}'.format( best_fit, trip ) )
            raise NoStopFound( "No Next", best_fit, None )

        route= self.connection.get_route_from_stop_time( best_fit.stop_time )
        return StopFinder_Next_Stop.Best_Fit( row.distance, row.time, row.stop, row.stop_time, route, single_next )

def prefix_fields( prefix, fieldnames ):
    """Return the list of field names with a prefix."""
    return list(prefix+'_'+f for f in fieldnames)

def prefix_nt( prefix, nt_obj ):
    """Create a dictionary from a namedtuple applying a prefix to the field names."""
    return dict(
        (prefix+'_'+f,getattr(nt_obj,f)) for f in nt_obj._fields
    )

def prefix_dict( prefix, dict_obj ):
    """Flatten a dictionary from a dictionary applying a prefix to the field names."""
    return dict(
        (prefix+'_'+f,dict_obj[f]) for f in dict_obj
    )

class WriteStop( Callable ):
    """A callable writer for reports that have been matched to a stop.
    This creates a CSV-format file attributes from
    :class:`caravel.report.Report`,
    :class:`caravel.transit_system.Stop`,
    :class:`caravel.transit_system.Stop_Time`

    How to create an object usable a callback with :func:`arrival_at_stop`.
    ::

        with open( args.stop, 'wb') as stop_file:
            stop= Stop( connection, stop_file )

    This creates a callable ``stop`` function that can be used like this
    ::

        stop( report, candidate )
    """
    def __init__( self, stop_finder, target=None ):
        """Create the CSV writer around the target file.

        :param stop_finder: :class:`StopFinder` object.
        :param target: file-like object suitable to CSV writer.
        """
        self.heading= stop_finder.heading()
        self.wtr= csv.DictWriter( target, self.heading )
        self.wtr.writeheader()
        self.fieldnames= self.wtr.fieldnames
        self.count= 0
    def __call__( self, report, best_fit ):
        """Write a row to the stop file.

        :param report: :class:`caravel.report.Report` object
        :param best_fit: :class:`Candidate` object
        """
        row= report.as_dict()
        for name in best_fit._fields:
            value= getattr(best_fit, name)
            if isinstance(value, dict):
                row.update( prefix_dict(name, value) )
            else:
                row[name]= value
        ##print( "WriteStop", self.heading )
        ##print( "         ", row )
        self.wtr.writerow( row )
        self.count += 1

class WriteNoStop( Callable ):
    """A callable writer for reports that have been matched to a stop.
    This creates a CSV-format file attributes from
    :class:`caravel.report.Report` and the stop definitions.

    How to create an object usable a callback with :func:`arrival_at_stop`.
    ::

        with open( args.reject, 'wb') as no_stop_file:
            no_stop= NoStop( no_stop_file )

    This creates a callable ``no_stop`` function.
    """
    heading= ( ['status']
        + caravel.report.headings
        + prefix_fields('candidate_1', Candidate._fields)
        + prefix_fields('candidate_2', Candidate._fields)
        )
    def __init__( self, target=None ):
        """Create the CSV writer around the target file.

        :param target: file-like object suitable to CSV writer.
        """
        self.wtr= csv.DictWriter( target, WriteNoStop.heading )
        self.wtr.writeheader()
        self.count= 0
    def __call__( self, status, report, dist_fit=None, time_fit=None ):
        """Write a row to the no-stop file.

        :param message: Short string explanation
        :param report: :class:`caravel.report.Report` object
        :param dist_fit: ``Stop`` object or ``None``
        :param time_fit: ``Stop`` object or ``None``
        """
        row= report.as_dict()
        row['status']= status
        if dist_fit:
            row.update( prefix_dict('candidate_1', dist_fit ) )
        if time_fit:
            row.update( prefix_dict('candidate_2', time_fit ) )
        # print( self.heading )
        # print( row )
        self.wtr.writerow( row )
        self.count += 1

def arrival_at_stop( reader, stop_finder, files, no_stop=print, stop=print ):
    """Locate closest stop to the Report objects in the given file(s).
    Create two outputs via callback functions.

    -   ``no_stop`` is called with reports to which a stop could not be reliably assigned.
        This function is called with four positional parameters.

        ..  function:: no_stop( message, report, candidate_1, candidate_2 )

            Callback function to write a report that could not be matched
            reliably to a stop.

            :param message: Short string explanation
            :param report: :class:`caravel.report.Report` object
            :param candidate_1: :class:`caravel.transit_system.Stop` object or ``None``
            :param candidate_2: :class:`caravel.transit_system.Stop` object or ``None``

    -   ``stop`` is called with the reports to which a stop could be assigned.

        ..  function:: stop( report, best_fit )

            Callback function to write a report was matched
            reliably to a stop.

            :param report: :class:`caravel.report.Report` object
            :param best_fit: :class:`Candidate` object

    :param reader: An object of :class:`caravel.report.ReportReader`.
    :param stop_finder: An  :class:`StopFinder` instance.
    :param files: a sequence of report files.
    :param no_stop: an open file to which 4-tuples are written.
    :param stop: an open file to which 7-tuples are written.
    :returns: dictionary of counts
    """
    counts= defaultdict(int)
    for report in caravel.report.report_file_iter( reader, files ):
        counts['input'] += 1
        try:
            best_fit= stop_finder.process_report( report )
            #print( '  fit', report, services, best_fit )
            stop( report, best_fit )
            counts['good']  += 1
        except InvalidReport:
            counts['excluded'] += 1
            continue
        except NoStopFound as ex:
            c1= None
            c2= None
            if len(ex.args) == 1:
                message= ex.args
            elif len(ex.args) == 2:
                message, c1 = ex.args
            else:
                message, c1, c2 = ex.args
            counts[message] += 1
            no_stop( message, report, c1, c2 )
            continue
    return counts

def get_args():
    """Parse command-line arguments.
    :returns: Arguments object.
    """
    parser= argparse.ArgumentParser( )
    parser.add_argument( 'files', action='store', nargs='*' )
    parser.add_argument( '--format', '-f', action='store', default='22' )
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
        caravel.transit_system.load.get_source_data()
        latest= caravel.LogCapture.ftp_acquire.get_report_files()
        files= [latest] + args.files
    else:
        files= args.files

    rdr_class = {
        '1': caravel.report.ReportReader_v1,
        '21': caravel.report.ReportReader_v21,
        '22': caravel.report.ReportReader_v22,
        }
    reader= rdr_class[args.format]()

    conn= caravel.transit_system.load.AccessZip( args.transit )

    stop_finder= StopFinder_Next_Stop( conn )

    with open( args.stop, 'wb' ) as stop_file:
        with open( args.reject, 'wb') as no_stop_file:
            stop= WriteStop( stop_finder, stop_file )
            no_stop= WriteNoStop( no_stop_file )
            counts= arrival_at_stop( reader, stop_finder, files, no_stop= no_stop, stop=stop )

    logger.info( "Counts {0}".format( pprint.pformat( dict(counts) ) ) )
    logging.shutdown()
