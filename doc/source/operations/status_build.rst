Status Build
================

The status build operation listens for update notifications in
the CouchDB.  It responds two two kinds o notifications.

1.  Mappings.  This is a change to one of the mappings that provides
    GTF values for the feed.

2.  Feeds.  This is a one-minute tail of the position log.