..  _design.routes:

Route Discovery
================

Without a route map, the route can still be discovered.

Each Dwell and Arrival report contains Route, Direction, Stop and Time
information.

Each report is effectively a trip :math:`\langle v, p, t \rangle`.  This is the
vehicle, *v*, the
position, :math:`p = \langle r, d, s \rangle`,  (route, *r*, direction, *d*, stop, *s*)
and the time, *t*.

The time has a number of attributes: :math:`t.d` is the date;
:math:`t.w` is the day of the week; :math:`t.t` is time of day.

The universe of data, is set of reports, :math:`R`.

..  math::

    R = \{ \langle v_0, p_0, t_0 \rangle, \langle v_1, p_1, t_1 \rangle, \ldots \}

Finding Scheduled Stops
---------------------------

For each position, :math:`p`, we have a subset of the universe of reports, :math:`R`, for that position

..  math::

    T_p = \{ t_n \vert \langle v_n, p_n, t_n \rangle \in R \land p_n = p \}

This position data does not include vehicle information, since we're only
trying to locate stops along a route and the schedule.

We can partition the position data, :math:`T_p`, into one-day slices.
For each day, :math:`d`, from the domain of available dates,
:math:`d \in \{ t_n.d \vert t_n \in T_p\}`, we have this:

..  math::

    T_{p,d} = \langle t_n.t \vert  t_n \in T_p \land t_n.d = d \rangle

Note that :math:`T_{p,d}` is a vector of stop times at this position.
Each index value is an arrival counter.  A vehicle will arrive a position
several times during the day.

A specific arrival time
during the day is :math:`T_{p,d,k}`.  The value is simply a number of seconds past
some epochal time, like midnight.

There are :math:`s = \lvert T_{p,d} \rvert` scheduled times because
a vehicle stops at position :math:`p` a total of :math:`s` times on a given day, :math:`d`.

Each day of the week should have a similar ordered sequence of arrival timestamps.
There's no *a priori* reason to separate the schedule into weekday and weekend.
It's simpler to treat each of the seven days as distinct.

Given a sequence of days, :math:`w_0, w_1, w_2, \ldots, w_6`, we have a matrix
of sequential visits on each day for the given position, :math:`p`.  This sequence
of days simply follows the day-of-week.

Also, there may be missing data in this set.

..  math::

    T_p = \begin{vmatrix}
    T_{p,0,w_0} & T_{p,1,w_0} & \varnothing & \ldots & T_{p,s,w_0} \\
    T_{p,0,w_1} & T_{p,1,w_1} & T_{p,2,w_1} & \ldots & T_{p,s,w_1} \\
    T_{p,0,w_2} & \varnothing & T_{p,2,w_2} & \ldots & T_{p,s,w_2} \\
    \ldots \\
    T_{p,0,w_6} & T_{p,1,w_6} & T_{p,2,w_6} & \ldots & T_{p,s,w_6} \\
    \end{vmatrix}

We can compute a mean (and other descriptive statistics) "down the colum" to get a
set of average arrival times throughout a given day.  These are the :math:`T_{p,s,w_n}`
values for a given stop, :math:`p`, and sequential visit, :math:`s`.

Each distinct arrival sequence number, :math:`s`, will have an average arrival,
:math:`\mu_{p,s}`, as
well as a standard deviation, :math:`\sigma_{p,s}`.

..  math::

    \mu_{p,s} = \mu_n\{T_{p,s,w_n}\} = \frac{\sum_n{T_{p,s,w_n}}}{\lvert T_{p,s,w_n} \rvert}

..  math::

    \sigma_{p,s} = \sigma_n\{T_{p,s,w_n}\} = \sqrt{\frac{1}{\lvert T_{p,s,w_n} \rvert-1}\sum_n{(T_{p,s,w_n}-\mu_{p,s})^2}}

Clustering
-------------

Pragmatically, data may be missing or inconsistent.  The matrix will have
gaps that must be handled gracefully.  The column of data must be filtered
to assure that all of the values are within a "reasonable" time window
of each other.

This can be handled by an algorithm which takes the first sequence
of visits, :math:`w_0`, :math:`T_{p,w_0} = \langle T_{p,0,w_0}, T_{p,1,w_0}, T_{p,2,w_0}, \ldots, T_{p,s,w_0} \rangle`
as a candidate definition of the sequence of times for a stop, :math:`p`.

We start with a sequence of stops with singleton groups times.

..  math::

    C &= \langle  C_0, C_1, C_2, \ldots, C_s \rangle \\
    C_0 &= \{ T_{p,0,w_0} \} \\
    C_1 &= \{ T_{p,1,w_0} \} \\
    C_2 &= \{ T_{p,2,w_0} \} \\
    \ldots \\
    C_s &= \{ T_{p,s,w_0} \}

Given this initial definition,
each subsequent day of data can be matched through a simple clustering algorithm.

The next day's data is :math:`T_{p,w_1} = \langle T_{p,0,w_1}, T_{p,1,w_1}, T_{p,2,w_1}, \ldots, T_{p,s,w_1} \rangle`.
The brute force algorithm simply matches each new :math:`T_{p,x,w_1}`
against the established groups of clustered stop times to compute all possible deviation values.

..  math::

    \sigma(C_0 \cup \{ T_{p,x,w_1} \}), \sigma(C_1 \cup \{ T_{p,x,w_1} \}), \ldots, \sigma(C_s \cup \{ T_{p,x,w_1} \})

The minimum :math:`\sigma(C_i \cup \{ T_{p,x,w_1} \})` value shows which stop the new time belongs to.

Ideally, the stop numbers in the two vectors are the same, meaning that :math:`\sigma(C_x \cup \{ T_{p,x,w_1} \})`
has the minimal value.

There are two outcomes.

-   If the minimal devaition is reasonably small, :math:`\sigma(C_i \cup \{ T_{p,x,w_1} \}) < \epsilon`,
    this new time, :math:`T_{p,x,w_1}`,  is then appended to the :math:`i` cluster of times
    in the sequence of stops.

    ..  math::

        C^{\prime} = \langle C_0, C_1, \ldots, C_i \cup \{ T_{p,x,w_1} \}, \ldots, C_s \rangle

-   If the minimal devaition is not small enough, :math:`\sigma(C_i \cup \{ T_{p,x,w_1} \}) \geq \epsilon`,
    this new time is used to seed a new cluster.  It represents a gap in the previously
    clustered times.

    ..  math::

        C^{\prime} = \langle C_0, C_1, \ldots, \{ T_{p,x,w_1} \}, \ldots, C_s \rangle


Eventually, all times have been assigned to clusters by finding the minmimal deviation.

Barring dramatic changes in the route, the sequence of values may reflect a consistent
ordering.  This may lead to an optimization to check only **adjacent** stops.

Rather than simply compute all :math:`\bigl\{ \sigma (C_i \cup \{T_{p,x,w_n}\}) \vert C_i \in C \bigr\}`,
it's easier to compute using :math:`k` adjacent stops.

..  math::

    \bigl\{ \sigma (C_i \cup \{T_{p,x,w_n}\}) \vert C_i \in C \land x-k \leq i < x+k \bigr\}


Finding Route Repetition
------------------------------

A route is simply a sequence of stops for a particular vehicle.  Generally,
it repeats throughout the day.

A given vehicle, :math:`v`, participates in a set of stops

..  math::

    PT_v = \{ \langle p_n, t_n \rangle \vert \langle v_n, p_n, t_n \rangle \in R \land v_n = v \}

This can be analyzed as an ordered sequence of stops.

We can use a least time, :math:`t_n = \min T_v = \forall_{x \in T_v} t_n \leq x`,
as a filter for the first instance of a sequence of stops.

..  math::

    \lfloor P_v \rfloor = \langle p_n \vert \langle v_n, p_n, t_n \rangle \in PT_v \land t_n = \min T_v \rangle

The next repeat of this route will have the same vector, but the times will all be offset
from the previous time
by approximately the same amount, :math:`\delta r`.  We can define a filter function,
:math:`\rho( PT_v, \delta r )` that uses  :math:`\lfloor P_v \rfloor` and the offset to
locate the next repeat of the route.

..  math::

    \rho( PT_v, \delta r ) = \langle p_n \vert \langle v_n, p_n, t_n \rangle \in PT_v \land t^{\prime}_n = {\lfloor P_v \rfloor}_n \land t_n \approx t^{\prime}_n + \delta r \rangle

This generalizes nicely for any integer number of repeats of the route.

..  math::

    \rho( PT_v, k \delta r ) = \langle p_n \vert \langle v_n, p_n, t_n \rangle \in PT_v \land t^{\prime}_n = {\lfloor P_v \rfloor}_n \land t_n \approx t^{\prime}_n + k \delta r \rangle

Finding repeats of a route, however, isn't very valuable.

Some routes have times that vary throughout the day to reflect the
morning and evening rush.  It's easier (and more accurate) to ignore
repetition in the routes and treat the entire day's schedule as one
long sequence of stops.

Sample Data
----------------

Here's a typical sequence of data.  This listing has a number of
``route, direction, stop ('time dwell',...)`` instances.

::

    26 1  31 ('07:04:56 97', '14:04:28 104')
    26 1  45 ('07:20:15 None',)
    26 1 134 ('09:21:32 561',)
    26 1 140 ('09:31:27 10',)
    26 2  46 ('07:20:24 9',)
    26 2 221 ('11:13:57 None',)
    27 1 381 ('09:45:47 None',)
    27 1 458 ('10:46:38 11',)
    27 1 1188 ('19:53:29 None',)
    27 2 147 ('07:05:26 44',)
    27 2 333 ('09:21:18 442',)
    27 2 335 ('09:20:34 None', '09:20:34 None')
    27 2 481 ('11:12:17 56',)
    27 2 717 ('14:04:46 45',)

This shows three features.

-   Route 26, direction 1, stop 31 was visited twice.  This is a scheduled stop.
    Each day, the approximate sequence times will repeat.

-   Route 27, direction 2, stop 335 got duplicate reports.  This happens.

-   Route 26, direction 1, stop 45 (among many others) was missing.
    In this case,
    the various samples analyzed had time gaps.  Pragmatically, missing
    data must be tolerated.

Spike Solution
----------------

Here's a named tuple that's used to simulate Arrival-like reports.

..  literalinclude:: ../../../test/spike_stats.py
    :lines: 68

Here's a method to generate a set of data that reasonably matches the
raw data.

..  autofunction:: test.spike_stats.synth_data_iter

..  autofunction:: test.spike_stats.group_by_rte_dir_stop

..  autofunction:: test.spike_stats.cluster_times

..  autofunction:: test.spike_stats.build_route

Optimizations
--------------

The Spike solution needs a few improvements.

It uses a brute-force match when clustering stops.  This should be a search
of adjacent stops.

It has a fairly random set of thresholds for clustering.

The initial grouping by route/direction/stop should be used to create
an ordered dictionary so that all
subsequent steps can be simple generators without additional sorting or
dictionary construction.