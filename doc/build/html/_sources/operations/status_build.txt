..  _ops.sb:

Status Builder
================

The status build application (:mod:`caravel.StatusBuilder`)
listens for update notifications in
the CouchDB.  It responds two two kinds of notifications.

1.  Mappings.  This is a change to one of the mappings that provides
    GTFS values for the feed.  These are prepared and pushed
    manually.  See :ref:`ops.map`.

2.  Feeds.  This is the one-minute tail of the position log.
    These are prepared and pushed by the log capture
    application.  See :ref:`ops.rtc`.

The  status build application is simply left running.  Forever.  It can be
stopped or restarted as needed for system maintenance.  It uses a private
cache file to record the last change sequence number in the database.

::

    python2.7 -m caravel.StatusBuilder.change_notification

Since this works entirely inside the database, it doesn't need any
additional configuration beyond the settings file described in :ref:`ops.config`.
