#!/usr/bin/env python2.7
"""Caravel processing of raw feed and mapping into route, stop and vehicle status
reports.

This relies on Couchdb Change Notification via long polling.

1.  Handle new mappings.  Validate.  Update Cache.  Cleanup.
    See :mod:`caravel.feed.mapping_load`.

2.  Handle new feeds.  Validate.  Apply Mappings.  Cleanup.
    See :mod:`caravel.feed.feed_load`.

3.  Build status.  See :mod:`caravel.status.status_load`.

Synopsis
==========

::

    python -m caravel.StatusBuilder.change_notification

Description
===============

This will start a long-polling request for changes in the given
couchDB.  This yields  a sequence of change documents.

For documents which are mappings, this triggers the mapping
validation, and cache update.  This is defined by
the :mod:`caravel.feed` package, specifically :mod:`caravel.feed.mapping_load`.

For documents which are feeds, this triggers feed validation, and status
updates.  The initial steps of feed processing are defined by
the :mod:`caravel.feed` package, specifically :mod:`caravel.feed.feed_load`.

The status updates are part of the :mod:`caravel.status` package,
specifically :mod:`caravel.status.status_load`.

The cleanup cycles are triggered asynchronously based on
watching the clock during ordinary processing cycles (i.e.,
intermittently after feed processing is completed.)

Alternatives include
-   cron in a separate process,
-   heartbeat from couchdb.


Recursion Detection
=====================

Once we start processing a feed or mapping, we'll get renotified of the
changes we're making to that mapping.

To prevent infinite recursion, we keep a small FIFO of documents that we
ignore when the appear a second time.  After all, this process does
numerous updates, so it gets notified of the updates it made.

Configuration
==================

This relies on :mod:`caravel.conf` to provide the settings
with the database connection.

Components
===============
..  autoclass:: LimitedFIFO
..  autofunction:: mapping_notification
..  autofunction:: feed_notification
..  autofunction:: periodic_tasks
..  autofunction:: long_poll_callback
"""
from __future__ import print_function
import logging
import sys

from caravel.feed.models import *
from caravel.status.models import *
from caravel.conf import settings
import datetime
import sys
import caravel.feed.feed_load as feed
import caravel.feed.mapping_load as mapping
import caravel.status.status_load as status
from couchdbkit.consumer.sync import SyncConsumer
from collections import namedtuple
import json

LRU = namedtuple( "LRU", ["id", "seq"] )

class LimitedFIFO( list ):
    """A list of a fixed size.  This creates a kind of first-in-first-out
    FIFO where new items are appended until the size is reached.  Then
    old items are removed.
    """
    def __init__( self, limit=60 ):
        """Creates a LimitedFIFO with a defined size.

        :param limit: the upper limit on the FIFO size, default=60.
        """
        self._limit= limit
    def append( self, object ):
        """Least-Recently-Used update.  This is a FIFO with the last 60 mapping
        or feed files that were processed.

        The idea is to prevent CoucbDB update notifications from echoing
        through the system. If we've processed it once, we won't process it
        again.
        """
        super( LimitedFIFO, self ).append( object )
        if len(self) > self._limit:
            self.pop( 0 )

logger= logging.getLogger( "change_notification" )

# Global Least-Recently-Used FIFO of documents in process
lru_fifo = LimitedFIFO()

# Global Mappings cache in the application server.
mappings = {}

def mapping_notification( new_mapping ):
    """The change notification is a complete mapping with an attachment."""
    global mappings

    mapping_cache= mapping.refresh_mapping_cache(mappings, [new_mapping] )
    logger.info( "Mapping {0!r}".format( dict(mapping_cache) ) )

def feed_notification( new_feed ):
    """The change notification is a feed with an attachment."""
    global mappings

    start= datetime.datetime.now()
    counts= feed.transform_new( mappings, [new_feed], status.track_arrival, status.track_location )
    end= datetime.datetime.now()
    logger.info( "Transform {0!r} reports in {1}".format( dict(counts), end-start ) )

def periodic_tasks( hour=False, day=False ):
    """Tasks done once in a great while.

    ..  todo:: Must track these changes in our LRU to avoid echo issues.

    :param hour: If the monitor has run for an hour.
    :param day: If the monitor has run for a day.
    """
    global lru_fifo

    # Remove old status reports; not every time.  Once per day.
    docs= status.remove_old(settings.db)
    seq= settings.db.info()['update_seq']
    logger.info( "Status Removal {0!r}".format( docs ) )
    for d in docs:
        lru_fifo.append( LRU(d['id'], seq) )

    # Remove old feeds; not every time.  Once per day.
    docs= feed.remove_old(settings.db)
    seq= settings.db.info()['update_seq']
    logger.info( "Feed Removal {0!r}".format( docs ) )
    for d in docs:
        lru_fifo.append( LRU(d['id'], seq) )

    if day:
        # Compact database.
        settings.db.compact()

def long_poll_callback( changes ):
    """Callback function used by the long-poll Consumer.

    This will get the most recent changes.

    Since a new Feed (or Mapping) triggers a number of updates, those "echo"
    notifications will bounce right back here for a second visit.  The
    ID's will be in the LRU cache and will be ignored.
    """
    global last_seq
    global lru_fifo

    if 'last_seq' in changes:
        last_seq= changes['last_seq']
    for resp in changes['results']:
        logger.debug( resp )

        if resp['id'] in ( l.id for l in lru_fifo ):
            return # Recently processed; ignore it.

        try:
            doc= settings.db.get( resp['id'] )
        except ResourceNotFound:
            return # Recently deleted; ignore it.

        if 'doc_type' not in doc:
            return # Not something we recognize

        if doc['doc_type'] == 'Mapping':
            # Higher than 2? Attached content?
            seq, _, hash = doc['_rev'].partition('-')
            if int(seq) >= 2 and 'content' in doc['_attachments']:
                logger.debug( "{0} not in {1}".format( resp, lru_fifo ) )
                lru_fifo.append( LRU(resp['id'], resp['seq']) )
                mapping_notification( Mapping.wrap(doc) )
        elif doc['doc_type'] == 'Feed':
            # Higher than 2?  Attached feed?
            seq, _, hash = doc['_rev'].partition('-')
            if int(seq) >= 2 and 'feed' in doc['_attachments']:
                logger.debug( "{0} not in {1}".format( resp, lru_fifo ) )
                lru_fifo.append( LRU(resp['id'], resp['seq']) )
                feed_notification( Feed.wrap(doc) )
        else:
            pass # Other activity that we must ignore

# Global sequence number to persist in case we're stopped
last_seq = 0

def main():
    """Main CoucnDB consumer processing loop.

    Use a long poll query for database changes.
    Invoke the :func:`long_poll_callback` function for each change.

    Once each hour of elapsed run-time do :func:`periodic_tasks` with hour true.
    This does not happen at the the top of the hour, but instead happens
    after an hour has passed.

    Once each day do :func:`periodic_tasks` with day true.  This happens
    right around midnight.
    """
    global last_seq

    Mapping.set_db(settings.db)
    Feed.set_db(settings.db)
    Route.set_db(settings.db)
    RouteStop.set_db(settings.db)
    Vehicle.set_db(settings.db)
    Stop.set_db(settings.db)

    daily = hourly = datetime.datetime.now()

    h, m, s = settings.change_notification_daily_task_time
    daily_sched = h*60+m

    # Seed processing status with last known sequence number.
    try:
        with open("last_seq.json") as status_file:
            proc_state= json.load( status_file )
        last_seq= proc_state['last_seq']
    except (IOError, ValueError):
        proc_state= {}

    # todo:: Check Database for current sequence number.
    # If DB sequence number < last known, then DB was rebuilt.

    # Seed mappings with last known good mappings.
    mapping.refresh_mapping_cache(mappings)

    consumer= SyncConsumer(settings.db)
    while True:
        try:
            consumer.wait_once(cb=long_poll_callback, since=last_seq)

            now= datetime.datetime.now()
            logger.debug( "State time={0} last_seq={1}".format( now, last_seq ) )
            proc_state['last_seq']= last_seq
            proc_state['time']= now.strftime("%Y-%m-%dT%H:%M:%S%Z")
            with open("last_seq.json",'w') as status_file:
                json.dump( proc_state, status_file )

            if now.date() > daily.date():
                # Midnight passed, in a new day.
                now_minute = now.time().hour*60+now.time().minute
                if now_minute >= daily_sched:
                    daily= now
                    periodic_tasks( day=True )
            elif (now-hourly).seconds > 3600:
                # An hour has gone by.
                hourly= now
                periodic_tasks( hour=True )

        except (KeyboardInterrupt, SystemExit):
            logger.info( "Interrupted" )
            break

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.INFO )
    main()
