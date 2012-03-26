Status Build
================

The status build application listens for update notifications in
the CouchDB.  It responds two two kinds o notifications.

1.  Mappings.  This is a change to one of the mappings that provides
    GTF values for the feed.

2.  Feeds.  This is a one-minute tail of the position log.

The  status build application is simply left running.  Forever.  It can be
stopped or restarted as needed for system maintenance.  It uses a private
cache file to record the last change sequence number in the database.

::

    python2.7 -m caravel.StatusBuilder.change_notification

Since this works entirely inside the database, it doesn't need any
additional configuration beyond the settings file described above.
