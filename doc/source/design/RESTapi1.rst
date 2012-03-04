RESTful API for Reports
=========================

Here are some couch db view and list definitions.

::

    {
        "_id": "_design/app",
        "language": "javascript",
        "views": {
            "all": {
                "map": "function(doc) {\n  if(doc.positions.length > 0) {\n    emit(doc._id, doc.positions);\n  }\n}"
            },
            "latest": {
                "map": "function(doc) {\n  if(doc.positions.length > 0) {\n    emit(doc._id, doc.positions[doc.positions.length-1]);\n  }\n}"
            }
        },
        "lists": {
            "positions": "function(head, req) { var row; start({ \"headers\": { \"Content-Type\": \"application/json\" } }); var output = '['; while(row = getRow()) { if(req.query.route_id) { if(row.key != req.query.route_id) { continue; } else { output += '{\"route_id\": \"' + row.key + '\", \"positions\":' + JSON.stringify(row.value) + '},'; } } else { output += '{\"route_id\": \"' + row.key + '\", \"positions\":' + JSON.stringify(row.value) + '},'; } } output += '{}]'; send(output); }"
        }
    }

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

:samp:`/hrtransit/_design/app/_list/positions/all`

    List all positions reports (current max is last 5 positions) for all routes.

    ::

        [{"route_id": "2052",
        "positions":[
        {"time":"15:26:39",
        "date":"02/29",
        "lat/lon":"370137445/-763652336",
        "loc_valid":"I",
        "adherence":"0",
        "adh_valid":"I",
        "route":"",
        "description":"","stopid":""},

        etc.

        ]}
        ]

:samp:`/hrtransit/_design/app/_list/positions/all?route_id=2106`

    List all positions (current max is last 5 positions) for a specific route.

    See above for sample JSON.

:samp:`/hrtransit/_design/app/_list/positions/latest`

    List latest position reports for all routes.

    See above for sample JSON.

:samp:`/hrtransit/_design/app/_list/positions/latest?route_id=2106`

    List latest position for a specific route

    See above for sample JSON.
