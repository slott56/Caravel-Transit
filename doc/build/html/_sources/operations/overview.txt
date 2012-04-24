Operational Overview
=======================

There are three separate pieces of information which are integrated to
provide a complete, accessible view of the transit system status.

1.  The real-time GPS position reports.  This is a tail from the spysocket.log.
    It is captured each minbute and pushed to a database.

2.  The Google Transit System (GTS) files.  These describe stops, routes,
    trips, and stop times.  These change slowly.

3.  Mappings from the real-time position reports to the GTS routes,
    stops and vehicles.  These change frequently, but aren't real-time
    data sources.

The objective is to integrate this data into a single database so that
various applications can extract it and use it.

Because of the variety of origins, there are several capture processes.

1.  The :mod:`caravel.LogCapture` application.  See :ref:`ops.rtc`.
    This monitors the spysocket log for size changes.
    It captures only the changed data and pushes it to the database.
    There are two versions of this.

    -   Java.

    -   Python.

2.  Mappings Upload.  See :ref:`ops.map`.  This must be done manually,
    based on transit system schedule and route changes.  The
    :mod:`caravel.LogCapture` application is used for mapping upload.

2.  The :mod:`caravel.StatusBuilder` application.  See :ref:`ops.sb`.
    This monitors the database for changes.
    When a change occurs (i.e., a tail from the log is pushed) it will
    check for mapping changes, check for GTS changes, and update the database
    to describe all the new vehicle, route and trip status.