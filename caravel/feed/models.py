#!/usr/bin/env python2.7
"""HRT Couch DB LogCapture Feed Models.

This describes the data pushed by LogCapture.
"""
from __future__ import print_function
from couchdbkit import Server
from couchdbkit import Document, ResourceNotFound
from couchdbkit import schema

class Feed( Document ):
    """A Feed file; the "feed" attachment is the raw CSV feed data."""
    timestamp= schema.DateTimeProperty()
    status= schema.StringProperty() # initially "new"
    def __repr__( self ):
        return "Feed( timestamp={0:s}, status={1:s} )".format( self.timestamp.strftime("%x %X"), self.status )

class Mapping( Document ):
    """A Mapping file; the "content" attachment is the raw CSV mapping data.

    :var timestamp: The file's modified time; used to locate newest version.
    :var effective_date: The first date on which to use this mapping.
    :var ending_date: The first date to **not** use this mapping.
        This should match the effective date of the next mapping to use.
    :var mapping_type: One of "vehicle", "route", "stop".
    :var status: ``None`` for new mappings.
        After validation is can be an error message
        Or "valid" for a valid mapping.
    """
    timestamp= schema.DateTimeProperty()
    effective_date= schema.DateProperty()
    ending_date= schema.DateProperty()
    mapping_type= schema.StringProperty()
    status= schema.StringProperty()
    def __str__( self ):
        return "Mapping( timestamp={0.timestamp}, effective_date={0.effective_date}, ending_date={0.ending_date}, mapping_type={0.mapping_type}, status={0.status})".format( self )
