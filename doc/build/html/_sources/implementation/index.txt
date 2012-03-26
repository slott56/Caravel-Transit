================
Implementation
================

Hosts
===========

There two hosts.

Source
-------

The source host runs the HRT-Log-Tail application (or similar) to tail the SpySocket.log.
This is Java because the source host expects this.

Analyzer
----------

The Analyzer host runs the Caravel application to analyze the mappings, feeds,
and transit data and compute the required status.


Python Stack
=================

The essential features of the implementation include the following:

-   CouchDB.  http://couchdb.apache.org.

    For hosting, see http://www.iriscouch.com/ and https://cloudant.com/

-   Python 2.7.  http://www.python.org

    -   couchdbkit.  http://couchdbkit.org/.  This has Django compatibility.

    -   fsmonitor.  https://github.com/shaurz/fsmonitor

    -   pywin32.  http://sourceforge.net/projects/pywin32/


There are several alternative couch implementations.

-   couchdb-Python 0.8.  http://packages.python.org/CouchDB/index.html
    Small and simple.

There are several alternative FSMonitor implementations.

-   watchdog.
    http://packages.python.org/watchdog/
    It does more and has a more complex installation
    and dependencies.

-   For Win32 **only**.
    http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html

-   For Linux2 **only**.
    http://pyinotify.sourceforge.net/

For background and more details, see

    http://wiki.apache.org/couchdb/Getting_started_with_Python

    http://blog.philippklaus.de/2011/08/watching-directories-for-changes-using-python\_-\_an-overview/


Application Structure
=======================

This section contains Sphinx "automodule" documentation from the various
components.

There is a multi-stage data flow of three separate pieces of
information.

-   Mappings.  The ET parts of the ETL process are done manually.
    The :mod:`caravel.LogCapture.couch_push` application performs a
    load.

-   The Feed.  An initial "capture" workflow does ETL of the Spysocket.log
    report feed.  The :mod:`caravel.LogCapture.log_capture` and
    :mod:`caravel.LogCapture.monitor_capture` applications provide
    two alternative implementations.  There are others.

-   Transit System.  The ETL extracts this from Google Transit,
    Transforms it into useful documents and loads it.

-   Status Reports.  This is a more complex workflow.
    The :mod:`caravel.StatusBuilder.change_notification` application
    handles this.

    1.  Once the feed is captured, then a second ETL applies
        the mappings to create intermediate report objects.
        These aren't generally persisted.

    2.  The reports are accumulated into Status documents.

    #.  One position reports are available, more complex transit system
        analysis can be done.



..  toctree::
    :maxdepth: 2

    database
    domain
    etl
    analysis
    web
