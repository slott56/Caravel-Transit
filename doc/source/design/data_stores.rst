Data Store Hierarchy
=======================

There are three tiers of storage.

1.  Since Last Stop on this route.  These are location reports
    that reflect a vehicle's progress since the last stop.
    With some care, this can be extrapolated to an arrival time
    at all subsequent stops on the route.

2.  Today's History.  These are arrival and dwell reports for
    today. These create a localized trend that conforms to or deviates from the
    historical average arrival times for a given route/direction/stop.

3.  Long-Term History.  The overall history of route/direction/stop arrival
    times effectively describes the actual routes and schedules.

Note that the standard relational model isn't an ideal fit for this
data.  There are several issues.

-   The route is a graph with nodes and edges corresponding to stops
    and driving segments.  Because nodes and edges are duals, only one is
    sufficient for a relational model.  Stops, for example, are easy
    to discern from the data.  Segments, however, are where slowdowns
    occur and where vehicle location reports are found.  It's difficult
    to choose one representation for the relational model.  It's also
    difficult to attempt to use both and keep them synchronized.

-   The historical data can be normalized, but it's of little value
    to do this.  A hierarchical collection might be considerably
    more efficient than normalizing the route/direction/stop hierarchy

-   The bulk of the access is
    to gather the short-term historical records associated with a
    a given route/direction/stop; this forms a short vector of times.
    This is transient data that forms a kind of FIFO.
    Fairly complex database queries are required to insert, delete and
    query a FIFO structure.
    A simple web service which avoids database overheads makes more sense.

-   Geospatial queries.  Locating stops and vehicles based on Lat/Lon
    is irksome because there's no simple database indexing scheme
    that permits rapid distance calculations.

    However.  See :ref:`design.distance` for more information on
    rapid distance approximations using an Equirectangular Approximation.

Last-Stop FIFO
------------------

Each Route/Direction FIFO contains the last stop's Dwell or Arrival report followed by
any Location reports for the same vehicle.

The CRUD transactions work like this.

**Create**.

-   Location reports are appended to a FIFO.

-   Arrival and Dwell reports clear the FIFO prior to insert.

**Update**.  Does not happen.

**Retrieve**.  Given a request for a route/direction, the short term
data is available to discover immediate location.  Daily data and Historical
data is required to compute an expected arrival time.

**Delete**.  Happens when an Arrival or Dwell report is inserted.

Today
-------

Each Route/Direction/Stop contains the Dwell and Arrival data accumulated today.

This has two parts.

-   A status with simple variance and confidence factor.

-   A sequence of reports.  Each Insert
    updates the status with a time variance and a confidence window.

The arrival times throughout the day will fit into one of two patterns.

-   Statistically significant departure from historical averages.
    This may indicate a route change or a significant systemic delay
    (e.g. construction or accident.)   This increases the confidence
    in any variance.

-   Confirmation of historical averages.  This decreases the confidence
    in any variance.

History
---------

Each Route/Direction/Stop contains all Dwell and Arrival data.

This is simply accumulated to discover route details.

See :ref:`design.routes`.
