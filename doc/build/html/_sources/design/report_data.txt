..  _design.position:

Position Data Acquisition
===========================

See http://www.transitchicago.com/developers/bustracker.aspx
for other implementations.

Background
-----------------

The underlying software is the Trapeze ITS integated vehicle fleet management
and communication systems for advanced public transit operations.

From Trapeze application, we need to do a tail of the GPS log.  This is
a very clever way to extract nearly real-time
location data without disrupting any aspect of Trapeze operations.

This tail can then be loaded into a Caravel database.

Legacy Implementations
------------------------

The first implementation did a file copy from the tail to an FTP server.
This provided a great deal of useful information.

::

    ftp://216.54.15.3/Anrd/

-   :file:`hrtrtf.txt` is the data.  There are at least three different
    formats for this file.

-   :file:`vid.csv` is a map of route ids to vehicle ids

The next two releases reformatted this extract into CSV and attempted to resolve
some of the foreign keys.

This suffers from three race conditions.  One of them cannot be fixed.

-   Tailing the log file will often create a partial last record
    as the tail is not synchronized with Trapeze.  Currently,
    this is 300 records, but the rate of growth of the log file
    (in records per minute) has not been measurted, so it's difficult
    to know if this is the roght size or not.

-   Polling means that the consumer can easily miss an entire upload
    simply by having the producer run a little more quickly than
    the consumer.

-   Copying the transformed log file to the FTP server means that
    FTP clients can see partial files.  While unlikely, it can't be
    prevented.

Preferred Implementation
--------------------------

There are three separate issues in capturing the Trapeze data.

1.  Proper interval for tailing the log.

2.  Providing mappings from Trapeze vehicle, route, stop and direction
    to GTFS route, stop and direction.

3.  Pushing the position report tail to a couchdb server as soon as it's available
    to avoid polling and synchronization issues.

**Tail Size**.
The proper tail size is estimated by computing the size of the
log hourly during several days.  From this, the average size per minute
can be computed along with a standard deviation that allows judging
how much data must be sampled to have reasonable confidence that all
data is available.

**Mappings**.
The mappings must be extracted from Trapeze and pushed to the Caravel couchdb.
The Trapeze data reflects actual operating conditions of the system and
are essential for matching the position reports against GTFS information.

The mappings are created and pushed as follows.

1.  Manually query the relevant Trapeze tables.

2.  Remove unneeded extra columns.

#.  Format as CSV.

#.  Package and push.

The "package and push" will supplement the mapping with an "Effective Date" -- the
date at which these mappings should be used.  Ideally, this date is in the future.

Each mapping file is pushed to the Caravel couchdb using two HTTP requests.

1.  An HTTP POST is used to create the mapping document.

2.  An HTTP PUT is used to upload the actual CSV file as an attachment to the
    mapping document.

The mapping document is encoded in `JSON <http://www.json.org/>`_ notation::

    {
        "timestamp": "yyyy-mm-ddThh:mm:ssZ",
        "effective_date": "yyyy-mm-dd",
        "mapping_type": "vehicle"
        "doc_type": "Mapping"
    }

In JSON, the ``{}``, ``:``, ``,`` and ``"`` punctuation is mandatory; whitespace
is optional.

:timestamp:
    The current date and time.
    The format is :samp:`{date}T{time}Z` and should be in GMT, not local time.
    The ``T`` is required.  The ``Z`` indicates GMT.
    Date is :samp:`{yyyy}-{mm}-{dd}`.
    Time is :samp:`hh:mm:ss`.

    See ISO 8601 and http://www.ietf.org/rfc/rfc3339.txt.

    This should simply be the operating system file timestamp.  If the file
    is updated and pushed a second time, then the timetamp will positively
    identify which is the latest and greatest.

:effective_date:
    The date on which this becomes effective.
    Date is :samp:`{yyyy}-{mm}-{dd}`.

    Once a mapping reaches the effective date, there's no point in changing
    the file, since it's being used elsewhere in the system.

:mapping_type:
    The type of mapping file being provided.
    This must be one of the following strings.

    -   ``"vehicle"`` to provide vehicle ID mappings from Trapeze codes to proper numbers.
    -   ``"route"`` to provide route ID mappings from Trapeze to GTFS.
    -   ``"stop"`` to provide stop ID mappings from Trapeze to GTFS.

:doc_type:
    Must be ``"Mapping"`` or the document cannot be found.

Using a program like `curl <http://curl.haxx.se/>`_, the mapping document
can be created using the following HTTP POST request.

::

    curl -X POST http://hrt.iriscouch.com:5984/mappings/
    -H "Content-Type: application/json"
    -d '{"timestamp":"2012-03-02T21:16:00Z", "effective_date":"2012-03-05",
    "mapping_type":"vehicle", "doc_type":"Mapping"}'

..  note:: Long Lines

    curl commands are one long (!) line, shown on multiple lines
    for readability in this document.

This can also done using any HTTP library in any programming language.

The response to document creation looks like this::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

This provides the status, the assigned document ID and a revision.  The ``id`` and ``rev`` are used
to attach the CSV document

The actual mapping file content is attached to the document using the following
HTTP PUT request.

The ``id`` and ``rev`` from the initial response becomes part of the URL.
The ``/content/`` in the URL is required; it's the name of the attachment.

::

    curl -X PUT http://hrt.iriscouch.com:5984/mappings/09833a88a1cbb06f64c555d0245f1af3/content/?rev=1-7750ef2dbce77303f957de17c754852a
    -H "Content-Type: text/csv"
    --data-ascii @the_mapping_file.csv

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"2-748151ff136b0001671fb0fa14eb886d"}

This provides the status, the assigned document ID and the new revision of the document.

**Position Report Feed**.
The real-time feed must be extracted from Trapeze and pushed to the Caravel couchdb.

The feed is created and pushed as follows.

1.  Tail the Trapeze log.  The tail size is currently 300 lines, but
    may need to be changed.

2.  Format into CSV.

#.  Package and push.

The "package and push" will include a status, document type and a timestamp.

Each feed extract is pushed to the Caravel couchdb using two HTTP requests.

1.  An HTTP POST is used to create the position report document.

2.  An HTTP PUT is used to upload the actual CSV file as an attachment to the
    position report document.

The position report feed document is encoded in `JSON <http://www.json.org/>`_ notation::

    {
        "timestamp": "yyyy-mm-ddThh:mm:ssZ",
        "status": "new"
        "doc_type": "Feed"
    }

:timestamp:
    The current date and time.
    The format is :samp:`{date}T{time}Z` and should be in GMT, not local time.
    Date is :samp:`{yyyy}-{mm}-{dd}`.
    Time is :samp:`hh:mm:ss`.

    See ISO 8601 and http://www.ietf.org/rfc/rfc3339.txt.

    This should simply be the operating system file timestamp.

:status:
    The status of the feed file being provided.  Must be ``"new"`` or
    the document will not be used.

:doc_type:
    Must be ``"Feed"`` or the document cannot be found.

Using a program like `curl <http://curl.haxx.se/>`, the feed document
can be created using the following HTTP POST request.

::

    curl -X POST http://hrt.iriscouch.com:5984/feed/
    -H "Content-Type: application/json"
    -d '{"timestamp":"2012-03-02T21:16:00Z", "status":"new", "doc_type":"Feed"}'

This can also done using any HTTP library in any programming language.

The response to document creation looks like this::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"1-7750ef2dbce77303f957de17c754852a"}

This provides the status, the assigned document ID and a revision.  The ``id`` and ``rev`` are used
to attach the CSV feed document

The actual feed file content is attached to the document using the following
HTTP PUT request.

The ``id`` and ``rev`` from the initial response becomes part of the URL.
The ``/feed/`` in the URL is required; it's the name of the attachment.

::

    curl -X PUT http://hrt.iriscouch.com:5984/feed/09833a88a1cbb06f64c555d0245f1af3/feed/?rev=1-7750ef2dbce77303f957de17c754852a
    -H "Content-Type: text/csv"
    --data-ascii @the_loca_feed_extract.csv

The response is::

    {"ok":true,"id":"09833a88a1cbb06f64c555d0245f1af3","rev":"2-748151ff136b0001671fb0fa14eb886d"}

This provides the status, the assigned document ID and the new revision of the document.

**Audit**.
The ID's can be used to get the documents to confirm proper upload.

For example::

    curl http://hrt.iriscouch.com:5984/feed/09833a88a1cbb06f64c555d0245f1af3/

This will respond with the specific document.

::

    {
    "_id":"09833a88a1cbb06f64c555d024be284c",
    "_rev":"2-450cfb068dfedf21046d11b5bed1d84f",
    "status":"new",
    "doc_type":"Feed",
    "timestamp":"2012-03-03T19:46:02Z",
    "_attachments":{
        "feed":{
            "content_type":"text/csv",
            "revpos":2,
            "digest":"md5-amWYNwFqSf4ICT04fsWeNw==","
            length":14758,
            "stub":true
            }
        }
    }

To see the attachment, use this::

    curl http://hrt.iriscouch.com:5984/feed/09833a88a1cbb06f64c555d0245f1af3/feed/

That will confirm the feed file which was pushed.

Similar queries can be used for the mappings::

    curl http://hrt.iriscouch.com:5984/mapping/09833a88a1cbb06f64c555d0245f1af3/
    curl http://hrt.iriscouch.com:5984/mapping/09833a88a1cbb06f64c555d0245f1af3/content/

Data Model
------------------------

There have been three legacy data models.

Vehicle Information
~~~~~~~~~~~~~~~~~~~~~~~

Vehicle Id information in :file:`vid.csv` has the following format::

    {'RID': '2218', 'VehID': '2018'}

RID is the route ID.  VehID is the Vehicle ID.

Vehicle Report V1
~~~~~~~~~~~~~~~~~~~~

There are three types of records::

    07:04:42 02/15  V.1.2233  H.0.0  MT_LOCATION    Lat/Lon:370620935/-763413842 [Valid]  Adher:-1 [Valid]  Odom:2668 [Valid]  DGPS:On  FOM:2

    07:04:42 02/15  V.1.3515  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:37  Dwell:22  Rte:65  Dir:2  TP:352  Stop:69  Svc:1  Blk:203  Lat/Lon:370425333/-764286136 [Valid]  Adher:-1 [Valid]  Odom:1712 [Valid]  DGPS:On  FOM:2

    07:04:42 02/15  V.1.2236  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:36  Arrival  Rte:4  Dir:2  TP:329  Stop:45  Svc:1  Blk:221  Lat/Lon:370315618/-763461352 [Valid]  Adher:2 [Valid]  Odom:1924 [Valid]  DGPS:On  FOM:2

Field by Field

0.  Time in ``"%H:%M:%S"`` format
1.  Date in ``"%m/%d"`` format
2.  Vehicle ID in ``"V\.1\.(\d+)"`` format
3.  ``H.0.0``
4.  Either ``"MT_LOCATION"`` or ``"MT_TIMEPOINTCROSSING"``

For MT_LOCATION

5.  Location in ``"Lat/Lon:%d/%d"`` format.
6.  '[Invalid]': 4, '[Valid]': 269
7.  ``"Adher:%d"``
8.  '[Invalid]': 64, '[Valid]': 209
9.  ``"Odom:%d"``
10. '[Invalid]': 6, '[Valid]': 267
11. 'DGPS:Off': 8, 'DGPS:On': 265
12. ``"FOM:%d"``.  Optional.

For MT_TIMEPOINTCROSSING some additional fields are present.

5.  Actual Time in ``""Time:%H:%M:%S"`` format
6.  "Dwell:%d" or "Arrival"
7.  ``Rte:65`` - Does not match routes.txt
8.  ``Dir:2`` - Direction 1 or 2; trips.txt uses 0 or 1
9.  ``TP:352``
10. ``Stop:69``
11. ``Svc:1`` or ``Svc:4``
12. ``Blk:203``
13. Location in ``"Lat/Lon:%d/%d"`` format.
14. '[Valid]': 27
15. ``"Adher:%d"``
16. '[Valid]': 27
17.  ``"Odom:%d"``
18. '[Valid]': 27
19. 'DGPS:Off': 1, 'DGPS:On': 26
20. ``"FOM:%d"``.  Optional.

Vehicle Report V2
~~~~~~~~~~~~~~~~~~~~~

There are two types of records::

    Time,Date,RID,Lat/Lon,Location Valid/Invalid,Adherence,Adherence Valid/Invalid[,Route,Direction,StopID]

    07:00:38,02/28,3247,368147270/-762487811,V,-1,V
    07:00:41,02/28,2109,368099480/-763510804,V,-1,V,28,1,30

The header, however, is unusual.

The RID value appears to be an internal route id.  It does not
match the route ID in the :ref:`design.transit` data.

Vehicle Report V3
~~~~~~~~~~~~~~~~~~~~~

There are two types of records::

    Time,Date,Vehicle,Lat/Lon,Location Valid/Invalid,Adherence,Adherence Valid/Invalid[,Route,Direction,StopID]

    07:00:38,02/28,3247,368147270/-762487811,V,-1,V
    07:00:41,02/28,2109,368099480/-763510804,V,-1,V,28,1,30
