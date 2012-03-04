#!/usr/bin/env python2.7
"""Caravel Report object construction.

This reads one (or more) YYYYMMDDHHMM.rpt raw files and creates
a sequence of Report instances.  The subclasses include

-   Location - a simple location report; rte is None and dwell is None.

-   Dwell - a Report with route/direction/stop and dwell time;
    rte is not None and dwell is not None.

-   Arrival - a Report with route/direction/stop arrived instead of dwell time
    rte is not None and dwell is None.

The fourth possible combination (rte is None and dwell is not None) cannot occur.

Report Objects
=================

..  autoclass:: Report
..  autoclass:: Location
..  autoclass:: Arrival
..  autoclass:: Dwell

Report Factory
================

..  autoclass:: ReportReader
    :members:
    :special-members:

..  autoclass:: ReportReader_v1
    :members:

..  autoclass:: ReportReader_v2
    :members:

..  autofunction:: report_iter

JSON Codec
================

..  autoclass:: JSONEncoder
..  autoclass:: JSONDecoder
"""
from __future__ import print_function, division
import datetime
from collections import namedtuple, defaultdict, Iterable
import csv
import pprint
import re
import logging
import sys
import os.path
import json
from abc import abstractmethod
from couchdbkit import Document
from couchdbkit import schema

logger= logging.getLogger( __name__ )

headings = ['timestamp', 'id',
    'lat', 'lon', 'll_valid',
    'adher', 'adher_valid',
    'odom', 'odom_valid', 'dgps', 'fom',
    'time', 'dwell', 'rte',  'dir',  'stop',
     'tp', 'svc', 'blk',
]

class Report( Document ):
    """Abstract superclass of the various kinds of reports."""
    timestamp= schema.DateTimeProperty()
    id= schema.StringProperty()
    def as_dict( self ):
        return dict(
            timestamp= self.timestamp,
            id= self.id,
            lat= self.lat,
            lon= self.lon,
            ll_valid= self.ll_valid,
            adher= self.adher,
            adher_valid= self.adher_valid,
            #odom= self.odom,
            #odom_valid= self.odom_valid,
            #dgps= self.dgps,
            #fom= self.fom,
            time= self.time,
            #dwell= self.dwell,
            rte= self.rte,
            dir= self.dir,
            stop= self.stop,
            #tp= self.tp,
            #svc= self.svc,
            #blk= self.blk,
        )

class Location( Report ):
    """A Location report for a Vehicle in motion.
    """
    lat= schema.FloatProperty()
    lon= schema.FloatProperty()
    ll_valid= schema.StringProperty()
    adher= schema.IntegerProperty()
    adher_valid= schema.StringProperty()
    #odom= schema.IntegerProperty()
    #odom_valid= schema.StringProperty()
    #dgps= schema.StringProperty()
    #fom= schema.IntegerProperty()
    time= schema.IntegerProperty()
    rte= schema.StringProperty()
    dir= schema.StringProperty()
    stop= schema.StringProperty()
    #tp= schema.StringProperty()
    #svc= schema.StringProperty()
    #blk= schema.StringProperty()
    def __repr__( self ):
        return "{0.__class__.__name__}( '{0.timestamp!s}', {0.id!r}, {0.lat!r}, {0.lon!r}, ll_valid={0.ll_valid!r} )".format( self )
    def __eq__( self, other ):
        return all(
            self.timestamp== other.timestamp,
            self.lat== other.lat,
            self.lon== other.lon,
            self.ll_valid == other.ll_valid,
            self.adher == other.adher,
            self.ader_valid == other.aher_valid,
            self.time== other.time,
            self.rte == other.rte,
            self.dir == other.dir,
            self.stop == other.stop,
        )

class Arrival( Location ):
    """A Location report for a Vehicle arriving at a stop.
    """
    def __repr__( self ):
        return "{0.__class__.__name__}( '{0.timestamp!s}', {0.id!r}, {0.lat:.6f}, {0.lon:.6f}, valid={0.ll_valid}, time='{0.time!s}', rte={0.rte!r}, dir={0.dir!r}, stop={0.stop!r} )".format( self )

class Dwell( Arrival ):
    """A Location report for a Vehicle paused at a stop.
    This is less helpful and may get filtered out.
    """
    dwell= schema.IntegerProperty()
    def __repr__( self ):
        return "{0.__class__.__name__}( '{0.timestamp!s}', {0.id!r}, {0.lat:.6f}, {0.lon:.6f}, valid={0.ll_valid}, time='{0.time!s}', rte={0.rte!r}, dir={0.dir!r}, stop={0.stop!r}, dwell={0.dwell!r} )".format( self )

class ReportReader( Iterable ):
    """An iterator over Report items (:class:`Location`, :class:`Arrival`, :class:`Dwell`).

    This is the abstract superclass for various reader implementations.

    Requires :meth:`ReportReader.open`
    and :meth:`ReportReader.factory`.

    """
    def __init__( self, year=None ):
        """Build a ReportReader_v1 with a given default year.

        The year is required because the timestamps only have month and day.

        :param year: Year extracted from file name.
        """
        self.log= logging.getLogger( self.__class__.__name__ )
        if year:
            self.year= year
        else:
            today= datetime.date.today()
            self.year= today.year
    def __iter__( self ):
        """Iterate over Report instances in this source."""
        for line in self.source:
            if not line: continue
            yield self.factory( line )
    @abstractmethod
    def open( self, source, year= None ):
        """Open a given source for processing.

        :param source: an open file-like source.
        :param year: a potential override for the default year.
        """
        raise NotImplementedError()
    @abstractmethod
    def factory( self, line ):
        """Parse the fields, returning Arrival, Dwell or Location.

        :param line: line of raw input.
        :returns: Report instance, if possible.  ``None`` if the fields can't be parsed.
        """
        raise NotImplementedError()


class ReportReader_v1( ReportReader ):
    """An iterator over Report items (:class:`Location`, :class:`Arrival`, :class:`Dwell`).

    This handles V1 format, with space-delimited fields in the following form.

    ::

        07:04:42 02/15  V.1.2233  H.0.0  MT_LOCATION    Lat/Lon:370620935/-763413842 [Valid]  Adher:-1 [Valid]  Odom:2668 [Valid]  DGPS:On  FOM:2

    This is an iterable object, generally something like the following is done::

        reader= ReportReader_v1()
        with open(some_file) as source:
            reader.open(some_file)
            for report in reader:
                # process report
    """
    vehicle_pat= re.compile( r"V\.\d+\.(\d+)" )

    def label_str( self, field, expected ):
        """Split a "label:value" field, doing no further conversion.
        If the label is not as expected, raise an exception.

        :param field: a "label:value field
        :param expected: the expected label.
        :returns: the string value
        """
        label, _, value = field.partition(":")
        assert expected == label, "expected {0!r} not actual {1!r}".format( expected, label )
        return value

    def label_int( self, field, expected ):
        """Split a "label:value" field, attempting an integer conversion.
        If the label is not as expected, raise an exception.

        :param field: a "label:value field
        :param expected: the expected label.
        :returns: the integer value
        """
        value= self.label_str( field, expected )
        if value:
            return int(value)
        return None

    def label_lat_lon( self, field, expected="Lat/Lon" ):
        """Split a "label:lat/lon" field, attempting an fairly complex conversion.
        If the label is not as expected, raise an exception.

        :param field: a "label:lat/lon field
        :param expected: the expected label.
        :returns: (lat, lon) 2-tuple
        """
        latlon= self.label_str( field, expected )
        lat_st, _, lon_st = latlon.partition('/')
        lat= int(lat_st)/10000000
        lon= int(lon_st)/10000000
        return lat, lon

    def label_time( self, field, expected ):
        """Split a "label:time" field, to create a seconds-after-midnight value.
        If the label is not as expected, raise an exception.

        :param field: a "label:time field
        :param expected: the expected label.
        :returns: datetime.time() object.
        """
        value= self.label_str( field, expected )
        hh, mm, ss = map( int, value.split(":") )
        return (hh*60+mm)*60+ss

    def common_fields( self, fields ):
        """Parse the common set of fields.
        These are Fields 13-20 of MT_TIMEPOINTCROSSING.
        They are also Fields 5-12 of MT_LOCATION.

        These fields are

        -   "Lat/Lon" and the following "[Valid]"/"[Invalid]" flag.
        -   "Adher" and the following "[Valid]"/"[Invalid]" flag.
        -   "Odom" and the following "[Valid]"/"[Invalid]" flag.
        -   "DGPS"
        -   "FOM"

        :returns: tuple of (lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom)
        """
        try:
            lat, lon = self.label_lat_lon( fields[0], "Lat/Lon" )
            ll_valid= 'V' if fields[1] == "[Valid]" else "I"
            adher= self.label_int( fields[2], 'Adher' )
            adher_valid=  'V' if fields[3] == "[Valid]" else "I"
            odom= self.label_int( fields[4], 'Odom' )
            odom_valid = 'V' if fields[5] == "[Valid]" else "I"
            dgps = self.label_str( fields[6], "DGPS" )
            fom= self.label_int( fields[7], 'FOM' )
            return lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom
        except Exception:
            self.log.error( "Invalid Common Fields {0!r}".format(fields) )
            raise

    def open( self, source, year=None ):
        """Open a given source for processing.

        :param source: an open file-like source.
        :param year: a potential override for the default year.
        """
        if year:
            self.year= year
        self.source= source

    def factory( self, line ):
        """Parse the fields, returning Arrival, Dwell or Location.

        :param line: line of raw input.
        :returns: Report instance, if possible.  ``None`` if the fields can't be parsed.
        """
        try:
            fields= line.rstrip().split()
            partial_ts= datetime.datetime.strptime( fields[0]+fields[1], "%H:%M:%S"+"%m/%d" )
            timestamp= partial_ts.replace( year=self.year )
            vehicle= self.vehicle_pat.match( fields[2] ).group(1)
            assert fields[4] in ('MT_TIMEPOINTCROSSING', 'MT_LOCATION')
            assert len(fields) == (21 if fields[4] == 'MT_TIMEPOINTCROSSING' else 13)
        except Exception as e:
            self.log.error( "Invalid {0!r}".format(line) )
            return

        if fields[4] == 'MT_TIMEPOINTCROSSING':
            # Field 6 is Dwell or Arrival
            # Fields 5-12 are unique
            # Fields 13-20 repeat fields 5-12 of MT_LOCATION
            lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom = self.common_fields( fields[13:] )
            time= self.label_time( fields[5], "Time" )
            rte= self.label_str( fields[7], "Rte" )
            dir= self.label_str( fields[8], "Dir" )
            tp= self.label_str( fields[9], "TP" )
            stop= self.label_str( fields[10], "Stop" )
            svc= self.label_str( fields[11], "Svc" )
            blk= self.label_str( fields[12], "Blk" )
            if fields[6] == "Arrival":
                return Arrival(
                    timestamp=timestamp,
                    id=vehicle,
                    lat=lat, lon=lon, ll_valid=ll_valid,
                    adher=adher, adher_valid=adher_valid,
                    odom=odom, odom_valid=odom_valid, dgps=dgps, fom=fom,
                    time=time, rte=rte, dir=dir, tp=tp, stop=stop, svc=svc,
                    blk=blk,
                    )
            else:
                dwell= self.label_int( fields[6], "Dwell")
                return Dwell(
                    timestamp=timestamp,
                    id=vehicle,
                    lat=lat, lon=lon, ll_valid=ll_valid,
                    adher=adher, adher_valid=adher_valid,
                    odom=odom, odom_valid=odom_valid, dgps=dgps, fom=fom,
                    time=time, rte=rte, dir=dir, tp=tp, stop=stop, svc=svc,
                    blk=blk, dwell=dwell,
                    )
        elif fields[4] == 'MT_LOCATION':
            # Fields 5, 7, 9, 11 and 12 are label:value
            # Fields 6, 8, 10 are [valid]/[invalid]
            lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom = self.common_fields( fields[5:] )
            return Location(
                    timestamp=timestamp,
                    id=vehicle,
                    lat=lat, lon=lon, ll_valid=ll_valid,
                    adher=adher, adher_valid=adher_valid,
                    odom=odom, odom_valid=odom_valid, dgps=dgps, fom=fom,
                    )
        else:
            self.log.error( "Unrecognized {0!r}".format(fields) )

class ReportReader_v2( ReportReader ):
    """An iterator over Report items (:class:`Location`, :class:`Arrival`, :class:`Dwell`).

    This handles V2 format, which is CSV.

    First Line::

        Time,Date,RID,Lat/Lon,Location Valid/Invalid,Adherence,Adherence Valid/Invalid[,Route,Direction,StopID]

    Column Titles:

        -   'Time'
        -   'Date'
        -   'RID'
        -   'Lat/Lon'
        -   'Location Valid/Invalid'
        -   'Adherence'
        -   'Adherence Valid/Invalid[' # Really.
        -   'Route'
        -   'Direction'
        -   'StopID]' # Also peculiar.

    This is an iterable object, generally something like the following is done::

        reader= ReportReader_v2()
        with open(some_file) as source:
            reader.open(some_file)
            for report in reader:
                # process report
    """
    columns= [
        'Time', 'Date', 'RID', 'Lat/Lon', 'Location Valid/Invalid',
        'Adherence', 'Adherence Valid/Invalid[', 'Route', 'Direction', 'StopID]']
    def open( self, source, year=None ):
        """Open a given source for processing.

        :param source: an open file-like source.
        :param year: a potential override for the default year.
        """
        if year:
            self.year= year
        self.source= csv.DictReader( source )
        assert self.columns==self.source.fieldnames, "Unrecognized Heading {0!r}".format( self.source.fieldnames )

    def factory( self, line ):
        """Parse the fields, returning Arrival, Dwell or Location.

        :param line: CSV line of raw input.
        :returns: Report instance, if possible.  ``None`` if the fields can't be parsed.
        """
        dt = datetime.datetime.strptime( line['Date'], "%m/%d" ).date().replace( year=self.year )
        tm= datetime.datetime.strptime( line['Time'], "%H:%M:%S" ).time()
        timestamp= datetime.datetime.combine( dt, tm )
        lat_st, _, lon_st = line['Lat/Lon'].partition('/')
        lat= int(lat_st)/10000000
        lon= int(lon_st)/10000000
        time= (tm.hour*60+tm.minute)*60+tm.second
        adher= int(line['Adherence'])
        if all( (line['Route'], line['Direction'], line['StopID]']) ):
            return Arrival(
                timestamp=timestamp,
                id=line['RID'],
                lat=lat, lon=lon, ll_valid=line['Location Valid/Invalid'],
                adher= adher, adher_valid= line['Adherence Valid/Invalid['],
                time=time,
                rte=line['Route'], dir=line['Direction'], stop=line['StopID]'] )
        return Location(
                id=line['RID'],
                lat=lat, lon=lon, ll_valid=line['Location Valid/Invalid'],
                adher= adher, adher_valid= line['Adherence Valid/Invalid['],
                )

class ReportReader_v3( ReportReader_v2 ):
    """An iterator over Report items (:class:`Location`, :class:`Arrival`, :class:`Dwell`).

    This handles V3 format, which is CSV.

    First Line::

        Time,Date,RID,Lat/Lon,Location Valid/Invalid,Adherence,Adherence Valid/Invalid[,Route,Direction,StopID]

    Column Titles:

        -   'Time'
        -   'Date'
        -   'Vehicle'
        -   'Lat/Lon'
        -   'Location Valid/Invalid'
        -   'Adherence'
        -   'Adherence Valid/Invalid[' # Really.
        -   'Route'
        -   'Direction'
        -   'Stop]' # Also peculiar.

    This is an iterable object, generally something like the following is done::

        reader= ReportReader_v3()
        with open(some_file) as source:
            reader.open(some_file)
            for report in reader:
                # process report
    """
    columns=  [
        'Time', 'Date', 'Vehicle', 'Lat/Lon', 'Location Valid/Invalid',
        'Adherence', 'Adherence Valid/Invalid[', 'Route', 'Direction', 'Stop]']
    def factory( self, line ):
        """Parse the fields, returning Arrival, Dwell or Location.

        :param line: CSV line of raw input.
        :returns: Report instance, if possible.  ``None`` if the fields can't be parsed.
        """
        dt = datetime.datetime.strptime( line['Date'], "%m/%d" ).date().replace( year=self.year )
        tm= datetime.datetime.strptime( line['Time'], "%H:%M:%S" ).time()
        timestamp= datetime.datetime.combine( dt, tm )
        lat_st, _, lon_st = line['Lat/Lon'].partition('/')
        lat= int(lat_st)/10000000
        lon= int(lon_st)/10000000
        time= (tm.hour*60+tm.minute)*60+tm.second
        adher= int(line['Adherence'])
        if all( (line['Route'], line['Direction'], line['Stop]']) ):
            return Arrival(
                timestamp=timestamp,
                id=line['Vehicle'],
                lat=lat, lon=lon, ll_valid=line['Location Valid/Invalid'],
                adher= adher, adher_valid= line['Adherence Valid/Invalid['],
                time=time,
                rte=line['Route'], dir=line['Direction'], stop=line['Stop]'] )
        return Location(
                id=line['Vehicle'],
                lat=lat, lon=lon, ll_valid=line['Location Valid/Invalid'],
                adher= adher, adher_valid= line['Adherence Valid/Invalid['],
                )

def report_iter( report_reader, files ):
    """An iterator which applies the ``report_reader`` instance to all
    of the named files.

    :param report_reader: an instance of :class:`ReportReader` which parses
        input lines and creates :class:`Report` instances.
    :param files: an iterable over the file names.
        To process a single file, use ``report_iter( report_reader, [one_file] )``
    """
    for report_file in files:
        ts= datetime.datetime.fromtimestamp(os.path.getmtime( report_file ) )
        with open(report_file) as source:
            report_reader.open(source, ts.year)
            for report in report_reader:
                yield report

class JSONEncoder( json.JSONEncoder ):
    """Encode any of the Report subclasses into JSON.

    Not needed, since couchdbkit.schema.Document objects
    have a :meth:`couchdbkit.schema.Document.to_json` method that
    handles some of the conversion.

    ::

        json.dumps( rpt.to_json() )

    Far better than this.
    """
    def default( self, obj ):
        if isinstance(obj, Report):
            as_dict= obj.as_dict()
            as_dict['doc_type']= obj.__class__.__name__
            as_dict['timestamp']= obj.timestamp.strftime("%Y-%m-%dT%XZ")
            return as_dict
        super( JSONEncoder, self ).default( obj )

class JSONDecoder( json.JSONDecoder ):
    """Decode any of the Report subclasses from JSON."""
    def __init__( self, *args, **kwargs ):
        super( JSONDecoder, self ).__init__( *args, object_hook=self.make_report, **kwargs )
    def make_report( self, as_dict ):
        if "doc_type" in as_dict:
            try:
                cn= eval(as_dict.pop('doc_type'))
                timestamp= datetime.datetime.strptime(as_dict['timestamp'],"%Y-%m-%dT%XZ")
                as_dict['timestamp']= timestamp
                return cn(**as_dict)
            except TypeError:
                print( cn, as_dict, cn.__init__.__code__.co_varnames )
                print( set(as_dict.keys()) -  set(cn.__init__.__code__.co_varnames) )
                print( set(cn.__init__.__code__.co_varnames) - set(as_dict.keys()) )
                raise
        else:
            return as_dict