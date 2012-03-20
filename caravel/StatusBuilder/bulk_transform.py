#!/usr/bin/env python2.7
"""Caravel processing of raw feed and mapping into route, stop and vehicle status
reports.

This is a one-time manual operation that can be driven via cron.

1.  Handle new mappings.  Validate.  Update Cache.  Cleanup.
    See :mod:`caravel.feed.mapping_load`.

2.  Handle new feeds.  Validate.  Apply Mappings.  Cleanup.
    See :mod:`caravel.feed.feed_load`.

3.  Build status.  See :mod:`caravel.status.status_load`.

"""
from __future__ import print_function
from caravel.feed.models import *
from caravel.status.models import *
from caravel.conf import settings
import datetime
import caravel.feed.feed_load as feed
import caravel.feed.mapping_load as mapping
import caravel.status.status_load as status


def build_status():
    # Mappings cache in the application server.
    mappings = {}

    # Remove all damaged feed documents; these cannot be processed.
    counts = feed.remove_damaged( settings.db, settings.db.view( "feed/new" ) )
    print( "Cleanup", dict(counts) )

    # If the change notification is a mapping...
    # Or.  Do all new mappings.
    counts= mapping.refresh_mapping_cache(mappings, Mapping.view('mapping/new', descending=True))
    print( "Mapping", dict(counts) )

    # If the change notification is a feed...
    counts= status.old_status_removal(settings.db)
    print( "Status Removal", dict(counts) )

    start= datetime.datetime.now()
    counts= feed.transform_new( mappings, feed.new_feed_iter(), status.track_arrival, status.track_location )
    end= datetime.datetime.now()
    print( "Transform {0} reports in {1}".format( dict(counts), end-start ) )

    # Not every time we receive a feed; only once per day.
    counts= feed.remove_old( settings.db )
    print( "Feed Removal", dict(counts) )

if __name__ == "__main__":
    Mapping.set_db(settings.db)
    Feed.set_db(settings.db)
    Route.set_db(settings.db)
    RouteStop.set_db(settings.db)
    Vehicle.set_db(settings.db)
    Stop.set_db(settings.db)

    build_status()