User's Guide
======================

There are three parts to gathering and processing transit
system data to create the current vehicle status.

1.  Log Capture.  The Log Capture application has two key feature sets.
    Note that the log has internal codes for route, stop and vehicle.
    A set of mappings must *also* be captured to interpret these codes.

    -   It gathers the real-time position reports
        once each minute and pushes them to the CouchDB.

    -   It is used to manually push mappings to the CouchDB.

2.  Status Builder.  This watches the CouchDB for change notification
    and transforms the raw feed into Route, Stop and Vehicle information.

3.  Route Capture.  This captures GTF data from Google.

..  toctree::
    :maxdepth: 2

    log_capture
    status_build
    route_capture
