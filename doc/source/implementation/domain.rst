============================
Domain Model Implementation
============================

This section contains Sphinx "automodule" documentation from the various
components.

There are several tiers: `Extract-Transform-Load`_ gathers data
and creates the `Current Status`_.  This is also used to support both
`Analysis and Profiling`_ and `Applications`_.

Extract-Transform-Load
=======================

There are several parts to the extract, transformation and load of
the vehicle reports and transit system data.

1.  Mappings.

2.  Real-Time Feed.

3.  Validation and Creation of usable Tansit Status

LogCapture
-----------------

..  automodule:: caravel.LogCapture.acquire
..  automodule:: caravel.LogCapture.capture
..  automodule:: caravel.LogCapture.couch_push

Feed
----------------

..  automodule:: caravel.feed

Report
-----------------

..  automodule:: caravel.report

Administrative Functions
--------------------------

..  automodule:: caravel.admin

..  automodule:: caravel.settings

Current Status
=================

Status Builder
-----------------

This actually include mapping validation, feed validation
as well as feed transform and load to create transit system
status.

..  automodule:: caravel.StatusBuilder.bulk_transform
..  automodule:: caravel.StatusBuilder.change_notification

Feed
------

..  automodule:: caravel.feed.models
..  automodule:: caravel.feed.mapping_load
..  automodule:: caravel.feed.feed_load

Status
--------

..  automodule:: caravel.status.models
..  automodule:: caravel.status.status_load

Transit System
-----------------

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
