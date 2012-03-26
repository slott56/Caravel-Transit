Real-Time Feed
==========================

The  log capture application is simply left running.  Forever.  It can be
stopped or restarted as needed for system maintenance.  It uses a private
cache file to record the size of the log so that it captures only the
new data.

There are two configurations.

-   All-in-One.

-   Separate Tail from Format-and-Push.

In the `All-In-One Log Capture`_ configuration, a single application (in Python or Java)
tails the log, formats it into CSV notation and the pushes it into
the couch database.

In the Separate hosts configuration, there are two applications, each
on separate hosts.  The `Tail Only Log Extract`_ command tails the log,
and moves the extract to a separate host.  The `Monitor Capture`_ application formats
the extract into CSV and pushes it to the couch database.

All-In-One Log Capture
-----------------------

The application is started from the command line
::

    python2.7 -m caravel.LogCapture.log_capture ../HRT-Mock/simulated.log

The positional argument (:file:`../HRT-Mock/simulated.log`) names the log file
to tail.

The Java implementation is similar.
::

    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.Capture
    ../HRT-Mock/simulated.log

Tail Only Log Extract
----------------------

The Tail-only configuration requires a tail process on one host.
The format and puch processing runs on a separate host, using the `Monitor Capture`_
application.

The application is started from the command line
::

    python2.7 -m caravel.LogCapture.log_capture -t Tail_Only ../HRT-Mock/simulated.log

The positional argument (:file:`../HRT-Mock/simulated.log`) names the log file
to tail.

The Java implementation is similar.
::

    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.Capture -t Tail_Only
    ../HRT-Mock/simulated.log

The extracts are copied to a separate host where a separate application processes
them for upload.

Monitor Capture
------------------

This is used to complete the processing started by the `Tail Only Log Extract`_.

This application monitors a directory for the extract file.  When the file is
created, this application immediately loads it to the Couch database.

The application is started from the command line
::

    python2.7 -m caravel.LogCapture.monitor_capture ../HRT-Mock

The positional argument (:file:`../HRT-Mock`) names the directory to examine
for the extract file.

There is no Java version of this.
