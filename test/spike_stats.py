#!/usr/bin/env python2.7
from __future__ import print_function, division
import csv
import glob
from collections import defaultdict

def rows():
    for f in glob.glob("*.rpt"):
        with open(f,'r') as source:
            rdr= csv.DictReader( source )
            for r in rdr:
                if r['Location Valid/Invalid'] != 'V': continue
                lat_str, _, lon_str = r['Lat/Lon'].partition("/")
                lat= float( lat_str[:2] + "." + lat_str[2:] )
                lon= float( lon_str[:3] + "." + lon_str[3:] )
                yield lat, lon, r['Route'], r['Stop]']

def range():
    count= 0
    routes= defaultdict(int)
    stops= defaultdict(int)
    ll_iter= iter(rows())
    lat, lon, rte, stop = next(ll_iter)
    min_lat = max_lat = lat
    min_lon = max_lon = lon
    routes[rte] += 1
    stops[stop] += 1
    for lat, lon, rte, stop in ll_iter:
        min_lat= min(min_lat, lat)
        max_lat= max(max_lat, lat)
        min_lon= min(min_lon, lon)
        max_lon= max(max_lon, lon)
        count += 1
        routes[rte] += 1
        stops[stop] += 1

    print( count )
    print( min_lat, max_lat )
    print( min_lon, max_lon )
    print( len(routes), dict(routes), sum(routes.values()) )
    print( len(stops), dict(stops), sum(stops.values()) )

if __name__ == "__main__":
    range()