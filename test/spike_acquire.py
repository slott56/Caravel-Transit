"""Read HRT Bus Information.
"""
from __future__ import print_function, division
import ftplib
from contextlib import closing
import datetime
from collections import namedtuple, defaultdict, Callable
import csv
import pprint
import re
import logging
import sys
import glob
import os.path

Directory = namedtuple( "Directory", ['name', 'timestamp', 'size'] )

def get_files( **access ):
    if not access:
        access = dict(host='216.54.15.3', user='anonymous', passwd='slott56@gmail.com')
    log= logging.getLogger( 'get_files' )
    file_status = {}
    def get_directory( line ):
        print( repr(line) )
        date, time, size_str, name = tuple(l.strip() for l in line.split())
        timestamp= datetime.datetime.strptime( date+time, "%m-%d-%y%I:%M%p" )
        size= int(size_str)
        file_status[name]= Directory( name, timestamp, size )
    with closing(ftplib.FTP(**access)) as data:
        data.dir("Anrd", get_directory)
        try:
            local_timestamp= datetime.datetime.fromtimestamp(os.path.getmtime( 'vid.csv' ) )
        except Exception:
            local_timestamp= None
        if not local_timestamp or file_status['vid.csv'].timestamp > local_timestamp:
            log.info( "Getting vid.csv" )
            with open( "vid.csv", 'wb') as target:
                data.retrbinary("RETR Anrd/vid.csv", target.write) # Slowly Changing
        name= file_status['hrtrtf.txt'].timestamp.strftime( "%Y%m%d%H%M.rpt")
        with open( name, 'w' ) as target:
            log.info( "Getting {0}".format( name ) )
            def writeline( line ):
                print( line, file=target )
            data.retrlines("RETR Anrd/hrtrtf.txt", writeline ) # Real Time

def get_vehicle_route():
    with open("vid.csv",'rb') as vehicles:
        rdr= csv.DictReader( vehicles )
        #return dict( (v['VehID'], v['RID']) for v in rdr )
        return dict( (v['RID'], v['VehID']) for v in rdr )

class Report( object ):
    def __init__( self, timestamp, id ):
        self.timestamp= timestamp
        self.id= id

class Location( Report ):
    def __init__( self, timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom ):
        super( Location, self ).__init__( timestamp, id )
        self.lat= lat
        self.lon= lon
        self.ll_valid= ll_valid
        self.adher= adher
        self.odom= odom
        self.dgps= dgps
        self.fom= fom
        self.dwell= None
        self.rte= None
        self.dir= None
        self.stop= None
    def __repr__( self ):
        return "{0.__class__.__name__}( '{0.timestamp!s}', {0.id!r}, {0.lat!r}, {0.lon!r} )".format( self )

class Arrival( Location ):
    """At a given stop on a route?"""
    def __init__( self, timestamp, id, lat, lon, ll_valid, adher, adher_valid, odom, odom_valid, dgps, fom,
            time, rte, dir, tp, stop, svc, blk ):
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
        """Parse the fields, returning Arrival, Dwell or Location."""
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
    for report_file in files:
        ts= datetime.datetime.fromtimestamp(os.path.getmtime( report_file ) )
        report_factory.year= ts.year
        with open(report_file) as real_time:
            for line in real_time:
                if not line: continue
                fields= tuple( f.strip() for f in line.rstrip().split() )
                report= report_factory( fields )
                if report is None: continue
                yield report

def route_dir_stop():
    log= logging.getLogger( "route_dir_stop" )

    # Accumulate Route/Direction/Stop history
    started= datetime.datetime.now()
    report_factory= ReportFactory()
    route_dir= defaultdict(list)
    count= 0
    for rpt in report_iter( report_factory, glob.glob("*.rpt") ):
        count += 1
        if rpt.rte and rpt.dir:
            route_dir[rpt.rte,rpt.dir,rpt.stop].append( rpt )
    finished= datetime.datetime.now()
    log.info( "{0:d} reports in {1:s} seconds".format( count, finished-started ) )

    print( "History By Route, Direction, Stop")
    print( "=================================")
    for r,d,s in sorted(route_dir):
        print( "{0:3d} {1:1d} {2:3d} {3:s}".format(r,d,s, route_dir[r,d,s]) )

def grid_size( ):
    """Profile lat/lon to get the extent of HRT services."""
    lat = []
    lon = []
    report_factory= ReportFactory()
    for rpt in report_iter( report_factory, glob.glob("*.rpt") ):
        if rpt.ll_valid:
            lat.append( rpt.lat )
            lon.append( rpt.lon )
    print( "Latitude", min(lat), max(lat) )
    print( "Longitude", min(lon), max(lon) )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    #get_files()
    route_dir_stop()
    #grid_size()