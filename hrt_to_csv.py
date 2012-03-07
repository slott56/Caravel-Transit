#!/usr/bin/env python2.7
from __future__ import print_function
import urllib2
import json
import csv

headings= [
    "_id","_rev","date","time","vehicle","lat/lon","loc_valid",
    "adherence","adh_valid","route","description","stopid"]

source = urllib2.urlopen( "http://hrt.iriscouch.com/hrtransit/_design/app/_view/all/")
reports= json.loads( source.read() )
print( reports['total_rows'] )
with open("hrtransit.csv","wb") as target:
    wtr= csv.DictWriter(target, headings)
    for row in reports['rows']:
        wtr.writerow( row['value'] )
        if target.tell() > 10000000: break
