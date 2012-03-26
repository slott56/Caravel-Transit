============================
Domain Model Implementation
============================

The problem domain includes objects of the following broad subject areas.

-   `Feed`_ includes the real-time Spysocket.log data
    and the  mappings between the real-time feed and GTF transit system.

-   `Report`_ are the real-time position reports.

-   `Transit System`_ contains the GTF transit system description.

-   `Status`_ contains the final reports on vehicles, routes and stops.

Feed
====

The raw data includes mappings and position feeds.

Feed Models
------------

..  automodule:: caravel.feed.models

Mapping Load
--------------

..  automodule:: caravel.feed.mapping_load

Feed Load
-----------

..  automodule:: caravel.feed.feed_load

Report
========

An intermediate position report can be built from the raw
position feed.

..  automodule:: caravel.report


Transit System
=========================

The current transit system description.

..  automodule:: caravel.transit_system

Status
======

The final, useful status reports.

Status Models
----------------

..  automodule:: caravel.status.models

Status Load
--------------

..  automodule:: caravel.status.status_load

