Log and Mapping Capture
==========================

The general `Log Capture Configuration`_ applies to both use cases.

The `Mappings Push`_ use case pushes the relevant mapping files.

The `Log Capture`_ use case does the tail-reformat-push of the feed file.

Log Capture Configuration
----------------------------

There are two version of Log Capture.  A Python version, included
in Caravel, and a Java version.

See https://github.com/CfABrigadeHamptonRoads/HRT-Log-Capture

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

The Python log capture uses a JSON-format file, :file:`hrtail_conf.py`

::

    #hrtail_conf

    #Couch Push
    #Test Database
    couchpush = { "db_url": "http://localhost:5984/couchdbkit_test" }
    #Production Database
    #couchpush = { "db_url": "http://hrt.iriscouch.com:5984/feed" }

    #Log Tail
    logtail = { "tail_status_filename": "logtail.history",
        "file_size_limit": 1000000 }

    # Reformat

    # Capture
    capture = { "extract_filename": "hrtrtf.txt",
        "csv_filename": "hrtrtf.csv" }

Mappings Push
----------------

A mapping is created through a three-step process.

1.  Extract the relevant Internal key and GTFS value.

2.  Create a CSV file in one of three formats:
    "vehicle", "route" or "stop".

3.  Push the CSV file using the CouchPush application.
    You'll provide the type of mapping and the effective date for the
    mapping.  On the given day (at midnight) the mapping takes effect.

The file formats have mandatory column names as shown below.

..  csv-table:: Column Names

    "vehicle","""vid"",""bus"""
    "route","""rid"",""Route"""
    "stop","""sid"",""Stop"""

Yes, they're inconsistent with respect to capitalization.

The application is started from the command line
::

    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.CouchPush -m route -e 2012-03-12 route.csv
    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.CouchPush -m stop -e 2012-03-12 stop.csv
    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.CouchPush -m vehicle -e 2012-03-12 vehicle.csv

The positional argument (:file:`../HRT-Mock/simulated.log`) names the log file
to tail.

The application is started from the command line
::

    python2.7 -m caravel.LogCapture.couch_push -m route -e 2012-03-12 route.csv
    python2.7 -m caravel.LogCapture.couch_push -m stop -e 2012-03-12 stop.csv
    python2.7 -m caravel.LogCapture.couch_push -m vehicle -e 2012-03-12 vehicle.csv


Log Capture
---------------

The  log capture operation is simply left running.  Forever.  It can be
stopped or restarted as needed for system maintenance.  It uses a private
cache file to record the size of the log so that it captures only the
new data.

Also, it has an upper limit on the amount of data that will
be captured. Real-time position reports rapidly become stale.
Only position reports from the last hour matter; older reports can be
safely ignored.

The application is started from the command line
::

    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.Capture
    ../HRT-Mock/simulated.log

The positional argument (:file:`../HRT-Mock/simulated.log`) names the log file
to tail.

The application is started from the command line
::

    python2.7 -m caravel.LogCapture.log_capture ../HRT-Mock/simulated.log
