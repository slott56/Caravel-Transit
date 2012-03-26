=============================
Extract Transform and Load
=============================

The ETL processing has several components.

-   `Administrative Functions`_ configure the Couch database.

-   `Configuration and Settings`_ slightly simplifies the
    various components by providing a consistent set of settings.

-   `Mapping Push`_ is a manual mush of the various mappings
    required to interpret the real-time feed.

-   `Log Tailing`_ contains two implementations of the basic log
    tailing application.

    -   Tail_Only does extract and then moves the file to another
        server for the rest of the transform-load process.
        The `Monitor Capture`_ handles this.

    -   Tail_Format_Push does extract, transform and load.

-   `Monitor Capture`_ is used with "Tail_Only" Log tailing.

Administrative Functions
============================

..  automodule:: caravel.admin

Configuration and Settings
===============================

..  automodule:: caravel.conf

Mapping Push
==============


..  automodule:: caravel.LogCapture.couch_push

Log Tailing
======================

There are several solutions to the feed capture problem.

The HRT-Log-Capture
project is another implementation of the log capture and couchDB push.

    https://github.com/CfABrigadeHamptonRoads/HRT-Log-Capture.

This application has two operating modes.

-   "Tail_Format_Push" capture handles everything.

-   "Tail_Only" merely captures the file and does nothing more.
    This requires

..  automodule:: caravel.LogCapture.log_capture

Monitor Capture
================

When the all-in-one "Tail_Format_Push" capture mode (see `Log Tailing`_) can't
be used, then a multi-step alternative must be used.

-   A Tail-Only log capture.  This simply "moves" the extract file to a
    drop-box directory on a separate server.

-   An application which monitors the  drop-box directory and does
    the reformat-push.

..  automodule:: caravel.LogCapture.monitor_capture

Status Building
=================

There are two versions of the status update application.

The standard implementation, `Status Builder`_ uses long polling to
capture each feed as it arrives in the CouchDB.  It is immediately
processed to create status updates.

An alternate implementation, `Status Builder Manual`_ can be run
against a database periodically.  This suffers from race conditions.

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
