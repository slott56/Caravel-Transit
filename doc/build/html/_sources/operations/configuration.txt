Configuration
=====================

The Python configuration is in a Python-syntax module.

The default name is ``settings.py``.  The name can be controlled with the
:envvar:`CARAVEL_SETTINGS` environment variable.

.. literalinclude:: ../../../caravel/settings.py
   :language: python
   :linenos:

There an alternate version of Log Capture, written in Java.

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
