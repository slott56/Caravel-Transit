..  _design.stopfinder:

Stop Finding
===================

Given a position Report (generally, an Arrival or Dwell), what stop does this
report reflect?

The :ref:`design.transit`  has stops with GPS coordinates.

The real-time reports have GPS coordinates.

There's a theoretical accuracy (without WAAS or DGPD) of 5m (about 16').

The location of the bus with respect to the planned stop, and the
time of day compared to the planned stop time have inherent errors
The driver may not stop at the same position.  Traffic interferes with the
schedule.

Further, time and position are in incompatible units.  It's a simple
three-dimensional mapping problem.  If the vehicles traveled at a constant
velocity, then it would be easy.  Since the vehicles stop and start, there
are no compatible units, nor any easy way to create compatible units.

Therefore the search involves a two-tier examination of possible stops.

1.  Locate nearest GPS coordinates, arranged in distance from the report.
    Locating distance from all 3210 stops seems excessive, but it's a
    simple brute-force approach.

    We have the report latitude and report longtude (:math:`R.la` and :math:`R.lo`).
    We also have a set of stops, :math:`S = \{ s_0, s_1, \dotsc, s_{n-1} \}`, each of which has
    latitude and logitude attributes (:math:`S_i.la` and :math:`S_i.lo`).

    We have a distance function, :math:`\Delta(la_1, lo_1, la_2, lo_2) \to d`.
    See :ref:`design.distance` for alternatives.

    ..  math::

        D = \{ \langle \Delta(R.la,R.lo,s_i.la,s_i.lo), s_i \rangle \vert s_i \in S \}

    We can order :math:`D` from closest to farthest.

2.  For each coordinate, find the stop times.

    We have a report time, :math:`R.t`.  We also have a set of times for a
    given stop,
    :math:`(s_i).T = \{ t_0, t_1, \dotsc, t_{m-1} \}`.

    ..  math::

        C = \{ \langle \lvert t-R.t \rvert, s_i, t \rangle \vert t \in (s_i).T \land s_i \in D \}

    We can order :math:`C` from closest in space and time to farthest.

    We have some choices for the time comparison.  We can use simple absolute value of the planned
    time, assuming the vehicle arrival times are normally distributed.  Or, we can
    assume that vehicles are more likely to be late.  This means that a few early
    arrival matches are sensible, but the more typical case is a late arrival.

We also need to put upper limits on the distance and time intervals.  There's no
reason to sort all 3210 distances when -- really -- less than a dozen will be
close enough to be relevant.

Consider some cases.

1.  A vehicle reports a location 200' from Stop 1 and 210' from stop 2.
    The difference is less than the 16' error inherent in GPS data.
    If these are on the same route, then time must be used to distinguish
    which stop is relevant.
    If these are on different routes, then vehicle history may help to
    distinguish which stop is relevant.

2.  A vehicle at Stop 3 at 2:05.  This could be the 2:03 running two minutes
    late.  Or it could be the 2:07 running two minutes early.  Only
    vehicle history can distinguish these two cases.  For the person at the
    next stop, however, the distinction is academic.  The stops are a known
    drive time apart; current time at the stop (2:05) plus drive time to the next
    stop is the relevant prediction.

3.  A vehicle reports in at 2:05.  It's 210' from Stop 1, and 1 minute late.
    It's 200' from Stop 2 and two minutes early.  By the clock it should be considered
    to be late for Stop 1.  By the GPS is should considered early for Stop 2.

Route Statistics
---------------------

Each defined trip visits a number of stops along a route.

The following procedure can follow each route and compute time and
distance between stops along that route.  Computing data along
a route creates a meaningful subset of all
time and distance deltas throughout the network of approximately 3200 stops.

::

    time_delta = defaultdict(int)
    distance_delta= defaultdict(int)
    for t in conn.trips:
        trip= conn.trips[t]
        stops= conn.trip_times[trip.trip_id]
        for i in range(1,len(stops)):
            # time and distance from previous stop
            d_t= stops[i].arrival_time -stops[i-1].arrival_time
            p_i= conn.stops[stops[i].stop_id].stop_lat, conn.stops[stops[i].stop_id].stop_lat
            p_i1= conn.stops[stops[i-1].stop_id].stop_lat, conn.stops[stops[i-1].stop_id].stop_lat
            d_d= dist_approx( p_i, p_i1 )
            if d_t != 0: time_delta[ d_t ] += 1
            d_bin= 16*int(d_d*5280//16)
            if d_bin != 0: distance_delta[d_bin] += 1

The times are all integer multiples of 60, so the frequency table is rather small.
Also.  There are zero-time differences between arrivals on adjacent stops.
There are zero-distance differences between adjacent stops, also.
It's not clear what this means.

The distance function provides values in miles.  We collapse these into 16'-wide
bins based on the accuracy of GPS coordinates.

We find the following.

..  csv-table::

    measure,mean,standard deviation
    time (sec),96.2,92.4
    distance (ft),1061,1947

We would expect 68% of the stops to be less than 188.6 seconds apart.
95% of the stops are less than 281.0 seconds apart.  These are approximately
3 and 5 minutes.

Similarly, 68% of the stops are less than 3008 feet apart;
95% of the stops are less than 4955 feet apart.

Lookup Statistics
---------------------

The important metric, however, is average distance between a reported
Arrival and the planned Stop.  This metric tells us how large a circle
around each Report (and each Stop) to use when determining vehicle
arrival at a stop.

Using 295 Arrival/Dwell reports, we computed a list of candidate stops.
These were limited to stops within 5280 feet.  Five of the reports could not
be matched to a stop within one mile.

In some cases the closest stop in distance was also the closest scheduled in time.

In the rest of the cases, a subsequent candidate stop -- possibly further in distance -- was closer in
time to the report.  In some cases, the stop has multiple scheduled times, so later
alterantives have the same distance, but a better time fit.

The distance between the first report and the closest-in-time scheduled stop is
tabulated below.

..  csv-table::

    closer step, avg. distance, std. distance, count
    0,   373,   575, 111
    1,  1183,  1167,  57
    2,  1045,   700,  28
    3,  1822,  1138,  18
    4,  1620,  1284,  23
    5,  1051,   538,  27
    6,   694,   134,   5
    7,   982,   948,   5
    8,  1541,   651,   3
    9,   832,   N/A,   1

Row zero are those reports where scheduled stop with the closest distance was also the closest time,
the average distance was 373 feet with a standard deviation 575 feet.  The raw distances
are densely packed to about 560 feet where they become sparse. This is less than one standard
deviation above the mean.

Row one summarizes those reports where the second stop was closer in time; the difference
was an average of 1183 feet.  Also, the data are densly packed up to about 496 feet,
then the data become sparse.  The average is large because
of outliers where the nearest stop in time was over 1,061 feet away.

Each subsequent row shows subsequent stops which were closer in time than
the closest stop.  For row 2, the minimum was a stop 96 feet away, but closer in
time.

For row 3, the minimum was 288 feet to a stop closer in time.  For the other 17 examples
the stop closer to the scheduled time was over 800 feet from the closest stop.

Rows 0, 1, 2 and 3 are nicely exponential in frequency distribution.  This suggests
that rows 4 to 9 include a number of false positives where stops a great distance
away were being compared incorrectly.
For rows 4 to 9, the minimum (with two exceptions) was over 500 feet to
locate a stop with closer scheduled time.

Based on the route analysis, stops are an average of 1,000 feet apart.

Based on Arrival report analysis, the distance of about 500 feet -- half way
to the next stop -- is a sensible upper bound for a matching stop.
