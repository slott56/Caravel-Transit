============================
Database Implementation
============================


See http://couchdb.apache.org/

See http://packages.python.org/CouchDB/index.html

http://www.couchbase.com/couchbase-server/overview

For some design notes, see :ref:`design.document`.

The CouchDB Mapping to Python objects leads to a data model using
the 11 field types defined here: http://packages.python.org/CouchDB/mapping.html#field-types.

For testing purposes, there are two candidate strategies.

-   Mock.  This is more appropriate for a relational database with a complex,
    difficult to initialize schema.

-   Temporary Database built during ``setUp`` and deleted during ``tearDown``.
    This is preferred, since CouchDB is so simple to work with.

Feed and Mappings
--------------------

The acquisition side of the database is the real-time feed plus the mappings
from source to GTF.

Feed

Mapping

Transit System
----------------

The Transit System is described by GTF data.

TBD

Status
-------

The status part of the system is built from analysis of the Feed and Mappings.

Vehicle

Route

Report
