================
Architecture
================

See http://www.zachman.com/about-the-zachman-framework

-   What (data)

-   How (processing)

-   Where (network hosts)

-   When (schedule and operations)

-   Who and Why (Use Cases)

See http://en.wikipedia.org/wiki/4%2B1_Architectural_View_Model

-   Logical (data)

-   Process

-   Development (components)

-   Physical (schedule and operations)

-   Scenarios (Use Cases)

Data and Processing
======================

See :ref:`design` for background.

Schedule and Operations
==========================

See :ref:`ops` for details.

Network Hosts
===============

Caravel has a number of processes.  These can be split onto several hosts or all run
on a single host.

Capture, Format and Push
-------------------------

Some "source" host runs the LogCapture or HRT-Log-Tail application (or similar) to capture
the real-time data from SpySocket.log.

There are both Java and Python implementations to permit flexibility.

See :ref:`ops.rtc`.

The captured data must be reformatted and pushed to a couch database.

This can be done on a single host.

Or the capture can be on one host and the format-and-push can be on a separate host.

Mappings
-----------

Additionally, the mappings must also be captured.  This uses the same log capture
application, but it can be run on a desktop or on one of the servers that has the real-time
capture components installed.

See :ref:`ops.map`.

Builder
----------

The Builder host runs the Caravel application to analyze the mappings, feeds,
and transit data and build the required status updates.

This is -- generally -- a separate host which does only couchdb processing.

See :ref:`ops.sb`.


Components and Tech Stack
===========================

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

