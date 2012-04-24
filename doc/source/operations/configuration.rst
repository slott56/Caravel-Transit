..  _ops.config:

Configuration
=====================

There are two log capture implementations.  They're functionally identical.
Each will monitor the spyspocket.log, capture the activity in the previous
minute and push the data to a database.

-   `Python Log Capture`_.  The :mod:`caravel.LogCapture` application is configured with a
    :file:`settings.py` file, described below.

-   `Java Log Capture`_.  There an alternate version of Log Capture, written in Java.
    This uses a :file:`hrtail.properties`, described below.

    See https://github.com/CfABrigadeHamptonRoads/HRT-Log-Capture

Python Log Capture
--------------------

The Python configuration is in a Python-syntax module.

The default name is ``settings.py``.  The name can be controlled with the
:envvar:`CARAVEL_SETTINGS` environment variable.

.. literalinclude:: ../../../caravel/settings.py
   :language: python
   :linenos:

:db_url:
    The URL for the database.  For testing, you can run a server
    and use http://localhost:5984/couchdbkit_test.

    For production, use http://hrt.iriscouch.com:5984/feed"

:logtail_status_filename:
    The filename used to record status.  This persistent status
    file makes it trivial to stop and restart log capture
    without missing or duplicating any data.

:logtail_size_limit:
    The largest tail that will be produced.  This is based on the
    rate of log growth.  The default will limit the log to
    one hour of data.  As a practical matter, vehicle position reports
    that are an hour old are probably irrelevant.

:capture_extract_filename:
    The name for the raw capture file.

:capture_csv_filename:
    The name for the CSV format capture file.

:change_notification_daily_task_time:
    A tuple with hour, minute and second on which to perform
    daily cleanup tasks like database compression.  The default
    is :samp:`(3, 0, 0)`, which does compression at 3:00 AM.

Java Log Capture
-------------------

The Java version uses a :file:`hrtail.properties`.

::

    #hrtail Properties

    #Couch Push
    #Test Database
    couchpush.db_url=http://localhost:5984/couchdbkit_test
    #Production Database
    #couchpush.db_url=http://hrt.iriscouch.com:5984/feed

    #Log Tail
    logtail.tail_status_filename=logtail.history
    logtail.file_size_limit=1m

    # Reformat

    # Capture
    capture.extract_filename=hrtrtf.txt
    capture.csv_filename=hrtrtf.csv
