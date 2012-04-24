================
Implementation
================

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
