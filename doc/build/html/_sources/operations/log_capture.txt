..  _ops.rtc:

Real-Time Capture
==========================

The  log capture application is simply left running.  Forever.  It can be
stopped or restarted as needed for system maintenance.  It uses a private
cache file to record the size of the log so that it captures only the
new data.

There are two configurations of the log capture.

-   `All-In-One Log Capture`_.  A single application (in Python or Java)
    does three things.  The application
    (1) tails the log, (2) formats it into CSV notation and then (3) pushes it into
    the couch database.

-   `Tail Only Log Extract`_.  Two separate applications are used.

    1.  This does step (1), tail the spysocket log and copy the file to a separate host.

    2.  Monitor a destination directory, and does things:
        (2) formats the extract into CSV notation and then (3) pushes it into
        the couch database.

While the all-in-one is simpler, it involves a slightly more complex installation
that may involve unacceptable modifications to production servers.

The tail-only requires two separate hosts.  The capture host has very, very
simplex software.  The monitor host, however, is requires te complete
installation.


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

This requires a configuration file described in :ref:`ops.config`.

Tail Only Log Extract
----------------------

The Tail-only configuration requires two hosts.

-   The `tail process`_ runs on one host.

-   The `format and push process`_ runs on a separate host.

Tail Process
~~~~~~~~~~~~~~

The Python implementation of the tail process uses the :mod:`caravel.LogCapture` application.
This is started from the command line
::

    python2.7 -m caravel.LogCapture.log_capture -t Tail_Only ../HRT-Mock/simulated.log

The positional argument (:file:`../HRT-Mock/simulated.log`) names the log file
to tail.

The Java implementation of the tail processes uses the Java ``org.hrva.capture.Capture``
application.  This is started from the command line
::

    java -cp LogCapture/dist/LogCapture.jar org.hrva.capture.Capture -t Tail_Only
    ../HRT-Mock/simulated.log

The extracts are copied to a separate host where a separate application processes
them for upload.

This requires a configuration file described in :ref:`ops.config`.

Format and Push Process
~~~~~~~~~~~~~~~~~~~~~~~~~

This is used to complete the processing started by the `Tail Process`_.

This application monitors a directory for the extract file.  Each time the
extract file is created, this application immediately does two things.

1.  It reformats the file into CSV.

2.  It pushes the file to the Couch database.

The application is started from the command line
::

    python2.7 -m caravel.LogCapture.monitor_capture ../HRT-Mock

The positional argument (:file:`../HRT-Mock`) names the directory to examine
for the extract file.

There is no Java version of this.

This requires the Python :file:`settings.py` file described in :ref:`ops.config`.
