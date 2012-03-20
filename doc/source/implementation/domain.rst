============================
Domain Model Implementation
============================

This section contains Sphinx "automodule" documentation from the various
components.

There is a multi-stage data flow.

-   `Extract`_ is the extraction and push via log tailing.
    It also includes a manual push of mappings.

-   `Transform-Load`_ applies the mappings to capture current
    transit system status.

-   `Transit System`_ is the capture of transit system route and stop
    definitions from GTF.

This is also used to support both `Analysis and Profiling`_ and `Applications`_.

Extract
=======================

These are the Python implementations.
A seaprate project has a Java implementation.

couch_push
-----------------

..  automodule:: caravel.LogCapture.couch_push

log_capture
-----------------

..  automodule:: caravel.LogCapture.log_capture

Transform-Load
=======================

Report
-----------------

..  automodule:: caravel.report

Administrative Functions
--------------------------

..  automodule:: caravel.admin

..  automodule:: caravel.conf

Feed
------

..  automodule:: caravel.feed.models
..  automodule:: caravel.feed.mapping_load
..  automodule:: caravel.feed.feed_load

Status
--------

..  automodule:: caravel.status.models
..  automodule:: caravel.status.status_load

Status Builder
-----------------

This is the status builder which relies on CouchDB change notification.
It includes mapping validation, feed validation
as well as feed transform and load to create transit system
status.

..  automodule:: caravel.StatusBuilder.change_notification

Status Builder Manual
------------------------

This is a one-time builk status builder that simply queries the database
for all mappings and all feeds.

..  automodule:: caravel.StatusBuilder.bulk_transform

Transit System
=========================

..  automodule:: caravel.transit_system

Analysis and Profiling
=========================

These are analysis and profiling modules and applications.

Statistics
------------

..  automodule:: caravel.statistics

Arrival Statistics
--------------------

..  automodule:: caravel.arrival_stats

Transit System Statistics
---------------------------

..  automodule:: caravel.transit_stats

Applications
=====================

These are top-level applications to produce useful results.

Arrival At Stop
----------------

..  automodule:: caravel.arrival_at_stop


Stop Discovery
----------------

..  automodule:: caravel.stop_discovery
