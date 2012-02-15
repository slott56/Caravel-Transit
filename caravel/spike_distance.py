"""Compare three distance calculations.

Proper calculation from http://williams.best.vwh.net/avform.htm#Dist

From http://www.movable-type.co.uk/scripts/latlong.html

For a more accurate Haversine formula and the Equirectangular Projection approximation

"""
from __future__ import print_function, division
import math

def radians( degrees ):
    return math.pi*degrees/180

def degrees( radians ):
    return 180*radians/math.pi

def dist_proper( p1, p2 ):
    lat1, lon1 = map( radians, p1 )
    lat2, lon2 = map( radians, p2 )
    a= (math.sin((lat1-lat2)/2))**2 + math.cos(lat1)*math.cos(lat2)*(math.sin((lon1-lon2)/2))**2
    c= 2*math.asin(math.sqrt(a))
    return 60.0*degrees(c) # nm; use 69.091 for statue mules

def dist_exact( p1, p2 ):
    lat1, lon1 = map( radians, p1 )
    lat2, lon2 = map( radians, p2 )
    a= (math.sin((lat1-lat2)/2))**2 + math.cos(lat1)*math.cos(lat2)*(math.sin((lon1-lon2)/2))**2
    c= 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return 3440.07*c # 3440.07 for nm, 3961.3 for statute miles, 6378.1 for km

def dist_approx( p1, p2 ):
    lat1, lon1 = map( radians, p1 )
    lat2, lon2 = map( radians, p2 )
    x = (lon2-lon1) * math.cos((lat1+lat2)/2)
    y = (lat2-lat1)
    c = math.hypot(x,y)
    return 3440.07*c

def compare( p1, p2 ):
    print( p1, p2, dist_proper(p1,p2), dist_exact(p1,p2), dist_approx(p1,p2) )

compare( p1 = (36.7098471, -76.7078159), p2 = (37.2758526, -75.9742827) )

compare( p1 = (36.7098471, -76.7078159),  p2 = (36.7098471, -75.9742827) )

compare( p1 = (37.2758526, -76.7078159), p2 = (37.2758526, -75.9742827) )

compare( p1 = ( 36.808970, -76.353444), p2 = (36.808977, -76.353416) )