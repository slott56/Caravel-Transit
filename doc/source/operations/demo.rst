Demonstration
==============

To run a demo, open five terminal windows.

Window 1.

Run::

    couchdb

Window 2.

Run::

    cd /path/to/Caravel
    python2.7 -m caravel.admin

This will push the necessary DB view definitions into the database.


Run::

    python2.7 -m caravel.StatusBuilder.change_notification

This starts the status builder application.

Window 3.

Run::

    python2.7 -m caravel.LogCapture.monitor_capture /path/to/HRT-Log-Capture

This will monitor a working directory for log tails.
This assumes that a tail-only process will be running,
and this process will do reformat and push processes.

Window 4.

Run::

    cd /path/to/Caravel
    python2.7 -m caravel.LogCapture.log_capture /path/to/HRT-Mock/simulated.log

This will tail some log.

Or.  To use the Java version.

Run::

    cd /path/to/HRT-Log-Capture
    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.Capture /path/to/HRT-Mock/simulated.log

Window 5.

The mappings are uploaded with this::

    cd /path/to/Caravel
    export PYTHONPATH=caravel
    python2.7 -m caravel.LogCapture.couch_push -m vehicle -e yyyy-mm-dd /path/to/HRT-Mock/vehicle.csv
    python2.7 -m caravel.LogCapture.couch_push -m route -e yyyy-mm-dd /path/to/HRT-Mock/route.csv
    python2.7 -m caravel.LogCapture.couch_push -m stop -e yyyy-mm-dd /path/to/HRT-Mock/stop.csv

The Transit System Definition is uploaded with this::

    python2.7 -m caravel.something.

..  todo:: Finish this.

A simulated real-time feed starts with this::

    cd /path/to/HRT-Mock
    python2.7 mock_log.py >simulated.log