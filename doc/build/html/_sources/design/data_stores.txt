..  include:: <isoamsa.txt>

..  _design.flow:

Data Flow and Processing
=========================

There are several processing steps.  This leads to a number of data stores
reflecting the persistent results of the various processing steps.

1.  Acquire Feed.  See :ref:`design.position`.
    This is parsed and (in effect) put into a processing queue.

2.  Find Stop.  Arrival reports have a route, stop and direction.

    Location reports require a geospatial query to locate a
    non-schedule stop.  See :ref:`design.stopfinder`.  There are two results possible.

    -   No good correlation with a known location.  These are "reject"
        locations that can be logged for further analysis and research on
        GPS errors or vehicle deviations from routes and schedules.

    -   A good correlation with a known, but non-scheduled stop.
        This use useful data that is persisted for publication.

3.  Time to Next Stop Calculation.  The time and stop information from a good location
    provides an estimate of the time to next stop.  The time since the report,
    and the time of the request all figure into this calculation.  Seconds
    count.  This is the **Since Last Stop** type and is most recent information
    only.

4.  Time On This Trip Calculation.  This is the sequence of stops on this
    particular trip on this route on this day.  For short routes, it's only
    a few locations.  For longer routes, it may be more locations.  This can
    provide additional detail for time to next stop.

5.  Day Statistics.  This is the sequence of stops on this day.  For a given
    route and direction, this may indicate persistent delays.  It provides an
    overall "health of the system" value that (probably) can't be used
    to predict arrival times.

6.  Longer-Term Statistics.

This leads to several tiers of storage.

1.  The Feed "queue".  The log tails are lightly reformatted to CSV and pushed.
    The internal to GTF mappings must also be pushed.

    From this, the Location, Dwell and Arrival reports are extracted for processing.

2.  Stop Status FIFO.  These are Good Arrival reports; i.e., those that have a
    close Stop and Stop Time.  These are stored in a simple FIFO that
    show's a vehicle's last reported status.

3.  Route Status.  These are Good Arrival reports.
    These are placed in a structure that tracks the vehicle's progress
    along a route.

#.  Day Status.  These are a collection of trip status for a given day.

#.  Long-Term History.  The overall history of route/direction/stop arrival
    times effectively describes the actual routes and schedules.
    This is simply a collection of days.

Also, see :ref:`design.document` for database design considerations based
simply on the structure of the data, independent of the processing.

Stop Status FIFO
------------------

Each Route/Direction FIFO contains the last stop's Dwell or Arrival report followed by
any Location class position reports for the same vehicle.

There are two relevant views of this FIFO of stop times.

We can look at the history of a particular route.  This shows the sequence
of trips along the route.  Knowing the first stop on the route allows
breaking the sequence into trips.

    (Route, Direction) |map| (Stop, Stop Time)

We can look at the history of a particular stop on a route.

    (Route, Direction, Stop) |map| Stop Time

The stops along the route are part of the transit system information.
The sequence of stops and stop-times
are required to predict all future stops in this route/direction.

Route Status
--------------

Good Arrival reports are placed in a structure that tracks the vehicle's progress
along a trip (and the associated route).

    (Route, Direction) |map| [ (Stop, Stop Time), ... ]

Good Arrival reports (and their stop and stop time) are appended to
the trip's stop sequence.

This can be viewed as the following, also.

    (Route, Direction, Stop) |map| [ Stop Time, ... ]

The sequence of stops along the trip provide a slightly longer-term view of
delays for the vehicle that will likely arrive at the stop.

Today's Status
----------------

Each Route/Direction/Stop contains the Dwell and Arrival data accumulated today,
irrespective of trip.

This allows calculation of a simple variance and confidence factor between
scheduled and actual stop times.

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

This is simply accumulated to discover any long-term trends.

Also, the historical data can be used to discover routes.
See :ref:`design.routes`.
