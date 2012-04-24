#!/usr/bin/env python2.7
"""Caravel ETL of real-time-feed with mappings
from source encodings to GTFS keys.

1.  Get any new mapping.

#.  Validate the mapping.

    -   Check the timestamp and delete duplicates (same type,
        same effective date, same or older timestamp).
    -   Check the type.
    -   Check the attachment size and structure.

#.  Put in a proper effective date range.

#.  Cache the current mapping chosen from the set of valid mappings.
    It's helpful to keep this in memory to save time.


Attachment Handling
====================

..  autoclass:: Invalid_Mapping
..  autoclass:: CSV_Attachment
..  autoclass:: Vehicle_Attachment
..  autoclass:: Route_Attachment
..  autoclass:: Stop_Attachment

..  autofunction:: mapping_attachment

Mapping Processing
====================

..  autofunction:: validate
..  autofunction:: validate_new
..  autofunction:: assemble_timeline
..  autofunction:: fetch_current
..  autofunction:: refresh_mapping_cache
"""
from __future__ import print_function
from caravel.feed.models import *
import csv
import datetime
from collections import defaultdict
from couchdbkit.exceptions import ResourceNotFound

class Invalid_Mapping( Exception ):
    """An exception raised as part of mapping validation."""
    pass

class CSV_Attachment( object ):
    """The attached file for a mapping.  The file should be a .CSV notation
    file with two specific column names.
    """
    source_name= ""
    gtf_name= ""
    def __init__( self, document ):
        """Construct a Mapping_Attachement for a given document.
        This will fetch the attached document and open it for access.
        """
        self.doc= document
        attachment= self.doc.fetch_attachment( name="content", stream=True )
        self.reader= csv.DictReader( attachment )
        self.map= {}
    def is_valid( self ):
        """Validate the attachment.  This is generally a check of the headers
        to the sure that the class-level :var:`source_name` column
        and :var:`gtf_name` column are present.
        """
        if set( (self.source_name, self.gtf_name) ) <= set(self.reader.fieldnames):
            pass
        else:
            #print( " expected", set( (self.source_name, self.gtf_name) ) )
            #print( " found   ", set(self.reader.fieldnames) )
            raise Invalid_Mapping("bad columns: {0} not in {1}".format(
                (self.source_name, self.gtf_name), self.reader.fieldnames) )
        return True
    def load( self ):
        """Load the attachment, returning a mapping with the "source_name" column
        as the key and the gtf_name column as the value.
        """
        if not self.map:
            self.map = dict(
                (row[self.source_name], row[self.gtf_name]) for row in self.reader )
        return self.map

class Vehicle_Attachment( CSV_Attachment ):
    """A :class:`CSV_Attachment` for the vehicle mapping."""
    source_name= 'vid'
    gtf_name= 'bus'

class Route_Attachment( CSV_Attachment ):
    """A :class:`CSV_Attachment` for the route mapping."""
    source_name='rid'
    gtf_name= 'Route'

class Stop_Attachment( CSV_Attachment ):
    """A :class:`CSV_Attachment` for the stop id mapping."""
    source_name='sid'
    gtf_name= 'Stop'

def mapping_attachment(mapping):
    """Instantiate the proper CSV_Attachment subclass
    for this mapping.
    """
    handlers= {
    'vehicle': Vehicle_Attachment,
    'route': Route_Attachment,
    'stop': Stop_Attachment,
    }
    return handlers[mapping.mapping_type](mapping)

def validate( mapping ):
    """Validate a given mapping object.  This will locate
    an appropriate attachment handler and then invoke the attachment
    handler's :meth:`CSV_Attachment.validate` method.

    This is the first step when processing a new mapping.

    If anything goes wrong an exception is raised.
    Otherwise this returns the mapping.
    """
    try:
        attachment_handler= mapping_attachment(mapping)
        if not attachment_handler.is_valid():
            raise Invalid_Mapping("invalid_attachment")
    except KeyError:
        raise Invalid_Mapping("unknown type: {0.mapping_type}".format(mapping))
    existing= set( k.effective_date for k in Mapping.view( 'mapping/'+mapping.mapping_type ) )
    #print( '===', repr(mapping.effective_date), existing )
    if mapping.effective_date in existing:
        raise Invalid_Mapping("duplicate type and effective date")
    return mapping

def validate_new( mapping_iter ):
    """For all new mappings, validate the attached content and update
    the status to mark them as usable.

    Return a dictionary of sequences of the new mappings which are also valid.
    The keys are the mapping types.  The value is a sequence of valid
    mappings of that type.
    This return value signals that we must rework the timeline
    and reload the mappings that are in cache.
    """
    new_valid= defaultdict(list)
    for m in mapping_iter:
        #print( "validate", m )
        try:
            validate( m )
            if m.status != 'valid':
                # Rare situation: revalidating an existing mapping.
                m.status= 'valid'
                m.ending_date= None
                m.save()
            new_valid[m.mapping_type].append( m )
        except ResourceNotFound as e:
            # No attached document
            # Simply ignore these, they may get updated later.
            continue
        except Invalid_Mapping as e:
            m.status = e.message
            m.save()
            continue
    return new_valid

end_of_days= datetime.date( 2200, 1, 1 ) # the end of days.

def assemble_timeline( mapping_type ):
    """For all valid mappings, reassemble the timeline for each type.

    This is the sequence of valid mappings in order by their
    effective_date from most recent to oldest.

    The most recent applies until the end of time.
    Each previous mapping applies until the one more recently added.
    Generally, just the last two mappings need to be tweaked to have
    proper ending dates.  As a simplification, we reset all
    ending dates to assure consistent data.

    Returns the sequence of mappings of the given type.
    """
    #print( ">>> assemble_timeline", mapping_type )
    timeline= []
    the_iter= iter( Mapping.view('mapping/'+mapping_type, descending=True ) )
    # Latest mapping applies until the end of time.
    try:
        prev = next( the_iter )
    except StopIteration:
        # No mappings of this type.  A bit of a problem in the long run.
        return
    #print( '   ', repr(prev.ending_date), repr(end_of_days) )
    if prev.ending_date is None or prev.ending_date != end_of_days:
        prev.ending_date = end_of_days
        prev.save()
        #print( "    Update", prev )
    timeline.append( prev )
    # All Earlier mappings have an ending date of the previous effective date.
    for m in the_iter:
        if m.ending_date is None or m.ending_date != prev.effective_date:
            m.ending_date= prev.effective_date
            m.save()
            #print( "    Update", m )
        timeline.append( m )
        prev= m
    timeline.reverse()
    return timeline

def fetch_current( mapping_type, today ):
    """Locate the mapping of the given type which is active today.
    This requires that mappings are all validated and the timeline
    has been assembled correctly.
    """
    #print( ">>> fetch_current", mapping_type )
    for row in Mapping.view( "mapping/"+mapping_type ):
        if row.effective_date <= today < row.ending_date:
            return row

def refresh_mapping_cache( mapping_cache, new_mappings=None, today=None ):
    """Locate the current mappings so they can be cached and used.

    1.  Validate all new mappings.
        This uses :func:`validate_new`.

    2.  Among the valid maps, reason out the timeline and make
        sure the effective_dates and ending_dates all make sense.
        This uses :func:`assemble_timeline`.

    3.  Pick the mappings that apply today.
        This uses :func:`fetch_current`.

    4.  Compare with the mappings in the local mappings cache.
        If the current mapping is new, then parse the CSV mapping data.
        If the current mapping hasn't changed, then we're good.

    This must be run based on two events.

    -   Beginning of each day.

    -   Each time a mapping is pushed.

    It can be run before each feed is processed, but that's a bit more
    processing than is strictly necessary.

    :returns: dictionary with 'vehicle', 'route', 'stop' mappings.
    """
    if today is None:
        today = datetime.datetime.today().date()

    # May have side effect of database update.
    if new_mappings is not None:
        new= validate_new( new_mappings )

        # Not **always** necessary.  May have side effect of database update.
        for mapping_type in 'vehicle', 'route', 'stop':
            assemble_timeline(mapping_type)

    for mapping_type in 'vehicle', 'route', 'stop':
        try:
            current_id= mapping_cache[mapping_type].document._id
            current_rev= mapping_cache[mapping_type].document._rev
        except (KeyError, AttributeError) as e:
            current_id, current_rev= None, None
        potential= fetch_current( mapping_type, today )
        if potential is None:
            print( "No {0} for {1}".format(mapping_type, today) )
            continue
        if potential._id != current_id or potential._rev != current_rev:
            handler= mapping_attachment(potential)
            handler.load()
            mapping_cache[mapping_type]= handler
            print( "Change to {0} for {1}".format(potential, today) )
        else:
            print( "===", potential, current_id, current_rev )
            print( "Using {0} for {1}".format(mapping_cache[mapping_type], today) )
    return mapping_cache
