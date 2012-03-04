============================
Database Implementation
============================


See http://couchdb.apache.org/

See http://packages.python.org/CouchDB/index.html

http://www.couchbase.com/couchbase-server/overview

See :ref:`design.document`

The CouchDB Mapping to Python objects leads to a data model using
the 11 field types defined here: http://packages.python.org/CouchDB/mapping.html#field-types.

For testing purposes, there are two candidate strategies.

-   Mock.

-   Temporary Database built during ``setUp`` and deleted during ``tearDown``.