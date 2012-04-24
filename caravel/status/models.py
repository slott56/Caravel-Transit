#!/usr/bin/env python2.7
"""Caravel Status object definitions.

..  autoclass:: Route

..  autoclass:: RouteStop

..  autoclass:: Stop

..  autoclass:: Vehicle


"""
from __future__ import print_function, division
import datetime
import logging
from couchdbkit import Document
from couchdbkit import schema

logger= logging.getLogger( __name__ )

class Route( Document ):
    """Stop Reports along this route."""
    date= schema.DateProperty()
    route= schema.StringProperty()
    direction= schema.StringProperty()
    history = schema.ListProperty()
    def save( self, **params ):
        self._id = "{0.route}-{0.direction}".format( self )
        super( Route, self ).save( **params )
    def __repr__( self ):
        return "Route(date={0.date}, route={0.route}, direction={0.direction}, history={0.history})".format(self)

class RouteStop( Document ):
    """Reports for a Stop (and associated Route)."""
    date= schema.DateProperty()
    route= schema.StringProperty()
    direction= schema.StringProperty()
    stop= schema.StringProperty()
    history = schema.ListProperty()
    def save( self, **params ):
        self._id = "{0.route}-{0.direction}-{0.stop}".format( self )
        super( RouteStop, self ).save( **params )
    def __repr__( self ):
        return "RouteStop(date={0.date}, route={0.route}, direction={0.direction}, stop={0.stop}, history={0.history})".format(self)

class Stop( Document ):
    """History of this stop."""
    date= schema.DateProperty()
    stop = schema.StringProperty()
    history = schema.ListProperty()
    def save( self, **params ):
        self._id = "{0.stop}".format( self )
        super( Stop, self ).save( **params )
    def __repr__( self ):
        return "Stop(date={0.date}, stop={0.stop}, history={0.history})".format(self)

class Vehicle( Document ):
    """History of this vehicle."""
    date= schema.DateProperty()
    vehicle= schema.StringProperty()
    history = schema.ListProperty()
    def save( self, **params ):
        self._id = "{0.vehicle}".format( self )
        super( Vehicle, self ).save( **params )
    def __repr__( self ):
        return "Vehicle(date={0.date}, vehicle={0.vehicle}, history={0.history})".format(self)
