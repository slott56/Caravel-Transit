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
"""
from __future__ import print_function, division
import datetime
from collections import namedtuple, defaultdict, Callable
import csv
import pprint
import re
import logging
import sys
import os.path
import json

logger= logging.getLogger( __name__ )

class Report( object ):
    """Abstract superclass of the various kinds of reports."""
    headings = [
        '__class__', 'adher', 'adher_valid', 'blk', 'dgps', 'dir', 'dwell',
        'fom', 'id', 'lat', 'll_valid', 'lon', 'odom', 'odom_valid', 'rte',
        'stop', 'svc', 'time', 'timestamp', 'tp'
    ]
    def __init__( self, timestamp, id ):
        self.timestamp= timestamp
        self.id= id

class Location( Report ):
    """A Location report for a given vehicle."""
    def __init__( self, timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom, **kwargs ):
        super( Location, self ).__init__( timestamp, id )
        self.lat= lat
        self.lon= lon
        self.ll_valid= ll_valid
        self.adher= adher
        self.adher_valid= adher_valid
        self.odom= odom
        self.odom_valid= odom_valid
        self.dgps= dgps
        self.fom= fom
        self.time= None
        self.dwell= None
        self.rte= None
        self.dir= None
        self.stop= None
        self.tp= None
        self.svc= None
        self.blk= None
        if kwargs:
            assert all( kwargs[k] is None for k in kwargs ), "Extra {0!r}".format(kwargs)
    def __repr__( self ):
        return "{0.__class__.__name__}( '{0.timestamp!s}', {0.id!r}, {0.lat!r}, {0.lon!r}, ll_valid={0.ll_valid!r}, odom_valid={0.odom_valid!r} )".format( self )
    def as_dict( self ):
        return dict(
            timestamp= self.timestamp,
            id= self.id,
            lat= self.lat,
            lon= self.lon,
            ll_valid= self.ll_valid,
            adher= self.adher,
            adher_valid= self.adher_valid,
            odom= self.odom,
            odom_valid= self.odom_valid,
            dgps= self.dgps,
            fom= self.fom,
            time= self.time,
            dwell= self.dwell,
            rte= self.rte,
            dir= self.dir,
            stop= self.stop,
            tp= self.tp,
            svc= self.svc,
            blk= self.blk,
            __class__= self.__class__.__name__
        )

class Arrival( Location ):
    """At a given stop on a route?"""
    def __init__( self, timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom,
            time, rte, dir, tp, stop, svc, blk, **kwargs):
        super( Arrival, self ).__init__( timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom )
        self.time = time
        self.dwell= None
        self.rte = rte
        self.dir = dir # 1 == out? 2 == in?
        self.tp = tp
        self.stop = stop
        self.svc = svc
        self.blk = blk
    def __repr__( self ):
        return "{0.__class__.__name__}( '{0.timestamp!s}', {0.id!r}, {0.lat:.6f}, {0.lon:.6f}, time='{0.time!s}', rte={0.rte!r}, dir={0.dir!r}, tp={0.tp!r}, stop={0.stop!r}, svc={0.svc!r}, blk={0.blk!r}, dwell={0.dwell!r} )".format( self )

class Dwell( Arrival ):
    """Paused in traffic?"""
    def __init__( self, timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom,
            time, dwell, rte, dir, tp, stop, svc, blk ):
        super( Arrival, self ).__init__( timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom )
        self.time = time
        self.dwell = dwell
        self.rte = rte
        self.dir = dir # 1 == out? 2 == in?
        self.tp = tp
        self.stop = stop
        self.svc = svc
        self.blk = blk

class ReportFactory( Callable ):
    """Emit Report items (Location, Arrival, Dwell).
    A subclass can implement different parsing rules.
    """
    vehicle_pat= re.compile( r"V\.\d+\.(\d+)" )
    def __init__( self, year=None ):
        """Build a ReportFactory with a given default year.

        The year is required because the timestamps only have month and day.

        :param year: Year extracted from file name.
        """
        self.log= logging.getLogger( self.__class__.__name__ )
        if year:
            self.year= year
        else:
            today= datetime.date.today()
            self.year= today.year

    def label_str( self, field, expected ):
        label, _, value = field.partition(":")
        assert expected == label, "expected {0!r} not actual {1!r}".format( expected, label )
        return value

    def label_int( self, field, expected ):
        value= self.label_str( field, expected )
        if value:
            return int(value)
        return None

    def label_lat_lon( self, field, expected="Lat/Lon" ):
        latlon= self.label_str( field, expected )
        lat_st, _, lon_st = latlon.partition('/')
        lat= int(lat_st)/10000000
        lon= int(lon_st)/10000000
        return lat, lon

    def label_time( self, field, expected ):
        value= self.label_str( field, expected )
        return datetime.datetime.strptime( value, "%H:%M:%S" ).time()

    def common_fields( self, fields ):
        """Fields 13-20 of MT_TIMEPOINTCROSSING
        Fields 5-12 of MT_LOCATION

        :returns: tuple of (lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom)
        """
        try:
            lat, lon = self.label_lat_lon( fields[0] )
            ll_valid= fields[1] == "[Valid]"
            adher= self.label_int( fields[2], 'Adher' )
            adher_valid= fields[3] == "[Valid]"
            odom= self.label_int( fields[4], 'Odom' )
            odom_valid = fields[5] == "[Valid]"
            label, _, dgps = fields[6].partition(":")
            assert label == "DGPS"
            fom= self.label_int( fields[7], 'FOM' )
            return lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom
        except Exception:
            self.log.error( "Invalid Common Fields {0!r}".format(fields) )
            raise

    def __call__( self, fields ):
        """Parse the fields, returning Arrival, Dwell or Location.

        :param fields: tuple of fields, already split and stripped.
        :returns: Report instance, if possible.  ``None`` if the fields can't be parsed.
        """
        try:
            partial_ts= datetime.datetime.strptime( fields[0]+fields[1], "%H:%M:%S"+"%m/%d" )
            timestamp= partial_ts.replace( year=self.year )
            vehicle= self.vehicle_pat.match( fields[2] ).group(1)
            assert fields[4] in ('MT_TIMEPOINTCROSSING', 'MT_LOCATION')
            assert len(fields) == (21 if fields[4] == 'MT_TIMEPOINTCROSSING' else 13)
        except Exception as e:
            self.log.error( "Invalid {0!r}".format(fields) )
            return

        if fields[4] == 'MT_TIMEPOINTCROSSING':
            # Field 6 is Dwell or Arrival
            # Fields 5-12 are unique
            # Fields 13-20 repeat fields 5-12 of MT_LOCATION
            lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom = self.common_fields( fields[13:] )
            time= self.label_time( fields[5], "Time" )
            rte= self.label_int( fields[7], "Rte" )
            dir= self.label_int( fields[8], "Dir" )
            tp= self.label_str( fields[9], "TP" )
            stop= self.label_int( fields[10], "Stop" )
            svc= self.label_str( fields[11], "Svc" )
            blk= self.label_str( fields[12], "Blk" )
            if fields[6] == "Arrival":
                return Arrival(timestamp, vehicle,
                    lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom,
                    time, rte, dir, tp, stop, svc, blk,
                    )
            else:
                dwell= self.label_int( fields[6], "Dwell")
                return Dwell(timestamp, vehicle,
                    lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom,
                    time, dwell, rte, dir, tp, stop, svc, blk,
                    )
        elif fields[4] == 'MT_LOCATION':
            # Fields 5, 7, 9, 11 and 12 are label:value
            # Fields 6, 8, 10 are [valid]/[invalid]
            lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom = self.common_fields( fields[5:] )
            return Location(timestamp, vehicle,
                lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom )
        else:
            self.log.error( "Unrecognized {0!r}".format(fields) )

def report_iter( report_factory, files ):
    """An iterator which applies the report_factory to all lines
    in all of the named files.

    :param report_factory: a function (or callable object) which parses
        input lines and creates Report instances.
    :param: files an iterable over file names.  To process
        a single file, use ``report_iter( report_factor, [one_file] )``
    """
    for report_file in files:
        ts= datetime.datetime.fromtimestamp(os.path.getmtime( report_file ) )
        report_factory.year= ts.year
        with open(report_file) as source:
            for line in source:
                if not line: continue
                fields= tuple( f.strip() for f in line.rstrip().split() )
                report= report_factory( fields )
                yield report

class JSONEncoder( json.JSONEncoder ):
    def default( self, obj ):
        if isinstance(obj, Report):
            as_dict= obj.as_dict()
            as_dict['timestamp']= obj.timestamp.strftime("%x %X")
            if as_dict.get('time'):
                as_dict['time']= obj.time.strftime("%X")
            return as_dict
        super( JSONEncoder, self ).default( obj )

class JSONDecoder( json.JSONDecoder ):
    def __init__( self, *args, **kwargs ):
        super( JSONDecoder, self ).__init__( *args, object_hook=self.make_report, **kwargs )
    def make_report( self, as_dict ):
        if "__class__" in as_dict:
            try:
                cn= eval(as_dict.pop('__class__'))
                timestamp= datetime.datetime.strptime(as_dict['timestamp'],"%x %X")
                as_dict['timestamp']= timestamp
                if as_dict.get('time'):
                    timestamp= datetime.datetime.strptime(as_dict.get('time'),"%X")
                    as_dict['time']= timestamp
                return cn(**as_dict)
            except TypeError:
                print( cn, as_dict, cn.__init__.__code__.co_varnames )
                print( set(as_dict.keys()) -  set(cn.__init__.__code__.co_varnames) )
                print( set(cn.__init__.__code__.co_varnames) - set(as_dict.keys()) )
                raise
        else:
            return as_dict