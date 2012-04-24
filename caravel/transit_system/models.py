#!/usr/bin/env python2.7
"""Caravel Transit System "database".

..  autoclass:: Service
..  autoclass:: Route_Definition
..  autoclass:: Stop_Definition

..  autofunction:: radians
..  autofunction:: degrees
..  autofunction:: dist_approx

"""
from __future__ import print_function, division
from couchdbkit import Document
from couchdbkit import schema
import math
from caravel.conf import settings

class Service( Document ):
    date= schema.DateProperty()
    day_of_week= schema.StringProperty()
    services= schema.ListProperty()
    def __repr__( self ):
        return "Service(date={0.date}, day_of_week={0.day_of_week}, services={0.services})".format( self )

class Route_Definition( Document ):
    route_id= schema.StringProperty()
    route_short_name= schema.StringProperty()
    route_long_name= schema.StringProperty()
    route_desc= schema.StringProperty()
    route_type= schema.StringProperty()
    route_url= schema.StringProperty()
    trips= schema.DictProperty() # Service is required to identify a given trip.
    # Trip is { trip_id:..., direction_id:..., block_id:..., stops:{ ... } }
    def __repr__( self ):
        return ("Route_Definition( route_id={0.route_id}, "
                "route_short_name= {0.route_short_name}, "
                "route_long_name= {0.route_long_name}, "
                "route_desc= {0.route_desc}, "
                "route_type= {0.route_type}, "
                "route_url= {0.route_url}, "
                "trips= {0.trips!r} )").format( self )
    def stops( self ):
        """Flat list of stops on this route."""
        for svc in self.trips:
            for trip in self.trips[svc]:
                for s in self.trips[svc][trip]['stops']:
                    yield s

class Stop_Definition( Document ):
    stop_id= schema.StringProperty()
    stop_name= schema.StringProperty()
    stop_lat= schema.FloatProperty()
    stop_lon= schema.FloatProperty()
    trips= schema.DictProperty() # Service is required to identify a given trip.
    def __repr__( self ):
        return ("Stop_Definition( stop_id={0.stop_id}, "
                "stop_name= {0.stop_name}, "
                "stop_lat= {0.stop_lat}, "
                "stop_lon= {0.stop_lon}, "
                "trips= {0.trips!r} )").format( self )
    def distance_from( self, lat, lon ):
        """Distance from a given point, in miles."""
        return dist_approx( (self.stop_lat, self.stop_lon), (lat,lon) )

def radians( degrees ):
    """Convert Lat/Lon degrees to radians.

    :param degrees: Latitude or Longitude
    :returns: Radians
    """
    return math.pi*degrees/180

def degrees( radians ):
    """Convert radians to Lat/Lon degrees.

    :param radians: angle in radians, usually from a distance calculation
    :returns: Degrees
    """
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
