Mappings Upload
==================

There are three species of mappings:

-   Vehicle

-   Route

-   Stop

The mappings are prepared through a multi-step process.

1.  Query the data.

2.  Create a CSV-format file with the appropriate column titles.

    The file formats have mandatory column names as shown below.

    ======= =============================
    Type    Column Names
    ======= =============================
    vehicle "vid","bus"
    route   "rid","Route"
    stop    "sid","Stop"
    ======= =============================

    Yes, the upper-case/lower-case rules are inconsistent.

3.  Push the file with an appropriate effective date.

The :mod:`caravel.LogCapture.couch_push` program is used to push each
mapping.

::

    python2.7 -m caravel.LogCapture.couch_push --mapping_type type --effective_date date [--verbose] source.csv


There is a Java version of this, also.

::

    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.CouchPush -m type -e date source.csv

Examples

::

    python2.7 -m caravel.LogCapture.couch_push -m route -e 2012-03-12 route.csv
    python2.7 -m caravel.LogCapture.couch_push -m stop -e 2012-03-12 stop.csv
    python2.7 -m caravel.LogCapture.couch_push -m vehicle -e 2012-03-12 vehicle.csv
