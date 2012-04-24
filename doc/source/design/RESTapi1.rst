RESTful API for Feed and Mapping
=====================================

Feed
------

Here are some couch db view definitions

..  literalinclude:: ../../../_design/feed/views/all/map.js
    :language: javascript

..  literalinclude:: ../../../_design/feed/views/new/map.js
    :language: javascript

..  literalinclude:: ../../../_design/feed/views/old/map.js
    :language: javascript


:samp:`/hrtransit`

    Base API URL -- a CouchDB query.

    ::

        {"db_name":"hrtransit",
        "doc_count":238,
        "doc_del_count":1,
        "update_seq":111741,
        "purge_seq":0,
        "compact_running":false,
        "disk_size":4010076,
        "instance_start_time":"1330602149238300",
        "disk_format_version":5,
        "committed_update_seq":111741}

Request::

    http://localhost:5984/couchdbkit_test/_design/feed/_view/all

Response::

    {"total_rows":1,"offset":0,"rows":[
        {"id":"9e6fabd08f2f2947fcb3e2119835155e",
        "key":"2012-04-23T10:52:01Z",
        "value":{
            "_id":"9e6fabd08f2f2947fcb3e2119835155e",
            "_rev":"3-e50b4e1919cac28f4e88b39307252904",
            "status":"processed",
            "doc_type":"Feed",
            "timestamp":"2012-04-23T10:52:01Z",
            "_attachments":{
                "feed":{
                    "content_type":"text/csv",
                    "revpos":2,
                    "digest":"md5-OhOQgpanYvhNAqfr99lL9A==",
                    "length":14816,
                    "stub":true}}}}
    ]}


Request::

    http://localhost:5984/couchdbkit_test/_design/feed/_view/new

Similar to above, except the status value is only "new".

Request::

    http://localhost:5984/couchdbkit_test/_design/feed/_view/old

Similar to above, except the status value is only "processed".

Mappings
----------

Here are some couch db view definitions

..  literalinclude:: ../../../_design/mapping/views/all/map.js
    :language: javascript

..  literalinclude:: ../../../_design/mapping/views/new/map.js
    :language: javascript

..  literalinclude:: ../../../_design/mapping/views/route/map.js
    :language: javascript

..  literalinclude:: ../../../_design/mapping/views/stop/map.js
    :language: javascript

..  literalinclude:: ../../../_design/mapping/views/vehicle/map.js
    :language: javascript

Request::

    http://localhost:5984/couchdbkit_test/_design/mapping/_view/all

See below for typical document.

Request::

    http://localhost:5984/couchdbkit_test/_design/mapping/_view/new

See below for typical document.

Request::

    http://localhost:5984/couchdbkit_test/_design/mapping/_view/route

Response::

    {"total_rows":1,"offset":0,"rows":[
        {"id":"08dbda2681dad90836b46c63cef56bc3",
        "key":["2012-04-22","2200-01-01"],
        "value":{
            "_id":"08dbda2681dad90836b46c63cef56bc3",
            "_rev":"4-e5b7771bb5c18eded36790beee24c554",
            "status":"valid",
            "doc_type":"Mapping",
            "mapping_type":"route",
            "timestamp":"2012-03-09T10:33:06Z",
            "ending_date":"2200-01-01",
            "effective_date":"2012-04-22",
            "_attachments":{
                "content":{
                    "content_type":"text/csv",
                    "revpos":2,
                    "digest":"md5-R52W6xqZ8zYNZDRUo+5b2A==",
                    "length":641,
                    "stub":true}}}}
    ]}

Request::

    http://localhost:5984/couchdbkit_test/_design/mapping/_view/stop

See above for typical document.

Request::

    http://localhost:5984/couchdbkit_test/_design/mapping/_view/vehicle

See above for typical document.
