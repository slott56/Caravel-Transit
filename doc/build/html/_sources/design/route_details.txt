..  _design.routes:

Route Discovery
================

The routes can be discovered from historical location report data.
Each Dwell and Arrival report contains Route, Direction, Stop and Time
information.

Each report is effectively a triple, :math:`\langle v, p, t \rangle`, with
vehicle, *v*, the
position, *p*,
and the time, *t*.  The position breaks down into a triple, also,
:math:`p = \langle r, d, s \rangle`; this is route, *r*, direction, *d* and stop, *s*.
We can say :math:`p.r` to reference just the route id within a position.
We'll often summarize the position as a RDS or R/D/S triple.

The time has a number of attributes: :math:`t.d` is the date;
:math:`t.w` is the day of the week; :math:`t.t` is time of day.

The universe of data, is set of reports, :math:`R`.

..  math::

    R = \{ \langle v_0, p_0, t_0 \rangle, \langle v_1, p_1, t_1 \rangle, \dotsc \}

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
It's simpler to treat each of the seven weekdays as distinct.

We have a
collection of
sequential stop times, :math:`0 \leq y < s`, on each day, :math:`0 \leq y < d`, for the given position, :math:`p`.

..  math::

    T_{p,y=0} &= \langle T_{p,0,0}, T_{p,1,0}, \dotsc, T_{p,s-1,0} \rangle \\
    T_{p,y=1} &= \langle T_{p,0,1}, T_{p,1,1}, \dotsc, T_{p,s-1,1} \rangle \\
    T_{p,y=2} &= \langle T_{p,0,2}, T_{p,1,2}, \dotsc, T_{p,s-1,2} \rangle \\
    \dotsb \\
    T_{p,y=d-1} &= \langle T_{p,0,d-1}, T_{p,1,d-1}, \dotsc, T_{p,s-1,d-1} \rangle


We can compute a mean (and other descriptive statistics) "down the colum" to get a
set of average arrival times throughout a given day.  These are the :math:`T_{p,x,w_n}`
values for a given stop, :math:`p`, and sequential visit, :math:`0 \leq x < s`.

If the data was complete and consistent, this would be relatively easy to
work this.  Pragmatically, there may be gaps (and duplicates) in each vector.  We'll
address that below in the `Clustering`_ section.

We have to count only the valid data; we'll use :math:`\lvert T_{p,x,y} \rvert` as
the "valid count".  Ideally, all :math:`d` values down the column are valid, but pragmatically,
there may be duplications or omissions.

Each distinct arrival sequence number, :math:`x`, will have an average arrival,
:math:`\mu_{p,x}`, as
well as a standard deviation, :math:`\sigma_{p,x}`.

..  math::

    \mu_{p,x} = \mu\{T_{p,x,y} \vert 0 \leq y < d\} = \frac{\sum_y{T_{p,x,y}}}{\lvert T_{p,x,y} \rvert}

..  math::

    \sigma_{p,x} = \sigma\{T_{p,x,y} \vert 0 \leq y < d\} = \sqrt{\frac{1}{\lvert T_{p,x,y} \rvert-1}\sum_d{(T_{p,x,y}-\mu_{p,x})^2}}

The average arrival time, :math:`\mu_{p,x}`, isn't sufficient.  The standard
deviation, :math:`\sigma_{p,x}` is required to put a sensible confidence interval
around the arrival time.

Assuming that the arrival times follow a normal distribution, the following
should be true.

-   60% of arrivals will be within :math:`\mu_{p,x} \pm \sigma_{p,x}`
-   95% of arrivals will be within :math:`\mu_{p,x} \pm 2\times\sigma_{p,x}`
-   99% of arrivals will be within :math:`\mu_{p,x} \pm 3\times\sigma_{p,x}`

Clustering
-------------

Pragmatically, data may be missing or inconsistent.  The matrix will have
gaps that must be handled gracefully.  The column of data must be adjusted
to assure that all of the time values are within a "reasonable" time window
of each other.

..  note:: Reasonable

    A large statistical sample will allow a formal definition of "reasonable".

There may be missing data in the collection of times.  What we actually
have is the following kind of matrix of stop times with :math:`\varnothing`
missing data.


..  math::

    T_p = \begin{vmatrix}
    T_{p,0,0} & T_{p,1,0} & \varnothing & \dots & T_{p,s-1,0} \\
    \varnothing & T_{p,1,1} & T_{p,2,1} & \dots & T_{p,s-1,1} \\
    T_{p,0,2} & \varnothing & T_{p,2,2} & \dots & T_{p,s-1,2} \\
    \dotsb \\
    T_{p,0,d-1} & T_{p,1,d-1} & T_{p,2,d-1} & \dots & T_{p,s-1,d-1} \\
    \end{vmatrix}

The sequence of stops is shown horizontally from :math:`0 \leq x < s`.
The various days, :math:`0 \leq y < d`, are shown vertically.

There may also be duplicates.  These are trivial to detect and exclude, so we won't
discuss them further.

This can be handled by an algorithm which clusters the arrival times.
This algorithm will allow for missing reports of arrival times.

The goal is to minimize the deviations in the clusters of arrival times.

Stated another way, any other clustering of times will
yield a larger deviation value.  If we have two clusters, :math:`C_7 = \{ \text{6:59}, \text{7:00} \}`
and :math:`C_8 = \{ \text{8:05}, \text{8:07} \}`,
and a time, :math:`T = \text{7:02}`.   It's clear that :math:`\sigma (C_7 \cup T) < \sigma (C_8 \cup T)`.
Therefore, the new time belongs with :math:`C_7`.

We can formalize this goal to state that each deviation is the minimum of all
alternative assignements of time to cluster.

..  math::

    \forall T_{p,x,y} \bigl( T_{p,x,y} \in C_i \land \sigma C_i = min \{ \sigma (C_j \cup T_{p,x,y}) \vert j \neq i \} \bigr)

Interestingly, it's trivial to acheive this by simply claiming that each cluster
has only one arrival time.  This leads to another constraint on the clusters.

The additional goal is to minimize the number of clusters, consistent with a "reasonable"
arrival time window.  If we combine times to  reduce the number of clusters,
we'd have arrival times that
deviate too far from the planned schedule.

We can formalize this goal as a minimal number of clusters; or alternatively, an
upper limit on the deviation allowed within a cluster.  Over some :math:`\epsilon`,
the cluster must be divided.

..  math::

    \forall C_i \bigl( \sigma C_i < \epsilon \bigr)

We can separate times to reduce the
deviation (and increase the number of clusters).  This allows us to make somewhat
more sensistive analyses of actual arrival times, different from the planned
schedule.  For instance, railroad crossing delays, tunnel delays and bridge
opening delays may happen at a predictable time of day.  This may mean that
a stop which is "normally" at 2:00 PM may deviate consistently to 2:05 PM on
certain days.  In a single cluster, this has a large deviation.  In separate
clusters, this has a much smaller deviation, and may be more useful for predicting
arrival times.

**Clustering Algorithm**.

**[Initialization]**.  Start with a sequence
of visits to a stop, :math:`p`, to seed the clusters.
Since the choice doesn't matter, we'll
use the first sequence, :math:`T_{p,w_0} = \langle T_{p,0,w_0}, T_{p,1,w_0}, T_{p,2,w_0}, \dotsc, T_{p,s-1,w_0} \rangle`
as a candidate definition of the sequence of times.

This creates an initial sequence of stop top clusters.
Each cluster is a single time.

..  math::

    C \gets \langle  C_0, C_1, C_2, \dotsc, C_{s-1} \rangle

Where

..  math::

    C_0 &= \{ T_{p,0,w_0} \} \\
    C_1 &= \{ T_{p,1,w_0} \} \\
    C_2 &= \{ T_{p,2,w_0} \} \\
    \dotsb \\
    C_{s-1} &= \{ T_{p,s-1,w_0} \}

Given this initial definition,
each subsequent day of data can be matched to the candidate list of clusters.

**[Iterate through Days]**.
For each day's data, match each time with the accumulated cluster of times,
and update the clusters.

The next day's data is :math:`T_{p,y} = \langle T_{p,0,y}, T_{p,1,y}, T_{p,2,y}, \dotsc, T_{p,s-1,y} \rangle`.

    **[Iterate through Stops]**.  Each day has multiple stops, which are individually
    merged into the candidate clusters.

        **[Compute Deviations]**.
        A brute force approach matches the new stop time, :math:`T_{p,x,y}`,
        against all candidate stop time clusters to compute deviation values.

        ..  math::

            D \gets \bigl\{ \sigma(C_i \cup \{ T_{p,x,y} \}) \vert C_i \in C \bigr\}

        **[Minimum**].  Get index of the minimum value.

        ..  math:: m \gets i \vert C_i = \min D

        The minimum :math:`\sigma(C_m \cup \{ T_{p,x,y} \})` value shows that the
        new time belongs to stop :math:`m`.

        Ideally, the sequence of stop numbers in each day's vectors are the same, meaning that :math:`\sigma(C_x \cup \{ T_{p,x,y} \})`
        has the minimal value. This isn't necessary; so it's possible that :math:`m \neq x`.


        **[Update Clusters]**.
        There are two outcomes from examination of the deviation values.

        -   If the minimal devaition is reasonably small, :math:`\sigma(C_m \cup \{ T_{p,x,y} \}) < \epsilon`,
            this new time, :math:`T_{p,x,y}`,  is then appended to the :math:`i` cluster of times
            in the sequence of stops.

            ..  math::

                C^{\prime} = \langle C_0, C_1, \dotsc, C_m \cup \{ T_{p,x,y} \}, \dotsc, C_{s-1} \rangle

        -   If the minimal deviation is not small enough, :math:`\sigma(C_m \cup \{ T_{p,x,y} \}) \geq \epsilon`,
            this new time is used to seed a new cluster.  It represents a gap in the previously
            clustered times.

            ..  math::

                C^{\prime} = \langle C_0, C_1, \dotsc, C_i, \{ T_{p,x,y} \}, C_{i+1}, \dotsc, C_{s-1} \rangle

            This maintains the sorted ordering, also.

            ..  math::

                \max(C_i) < T_{p,x,y} < \min(C_{i+1})

        In both cases, we have established that :math:`\sigma C_m = min \{ \sigma (C_j \cup T_{p,x,y}) \vert j \neq m \}`.
        The cluster creates a sequence of minimal deviations.  And the number of clusters in  :math:`C^{\prime}`
        is the minimal number of clusters that will assure that the deviations are all less than :math:`\epsilon`.

        This new collection of clusters is used for the next stop time.

        ..  math::

            C \gets C^{\prime}

    **[End of Stops in a Day]**.  All :math:`T_{p,y}` have been merged in :math:`C`.

**[End of Days]**.  All :math:`T_{p}` have been merged in :math:`C`.
All times of all days have been assigned to clusters by finding the minimal deviation.

Note that some clusters may have only one time.  This can happen with outlier times
that don't fit the "reasonably small" :math:`\epsilon`.  A post-processing
pass can be used to reassess any singletons and align them into a more appropriate
cluster.

We should be able to assert the following:

..  math::

    \forall T_{p,x,y} &\bigl( T_{p,x,y} \in C_i \land \sigma C_i = min \{ \sigma (C_j \cup T_{p,x,y}) \vert j \neq i \} \bigr)\\
    \forall C_i &\bigl( \sigma C_i < \epsilon \bigr)

All deviation assignments are minimized.  Any change to the allocation of an arrival time will
lead to a cluster with a larger deviation than the above assignment.  Also, the number of
clusters is minimized.  Any additional cluster most have a deviation larger than :math:`\epsilon`.

Barring dramatic changes in the route, the sequence of values may reflect a consistent
ordering.  This may lead to an optimization to check only **adjacent** stops.

Rather than simply compute all :math:`\bigl\{ \sigma (C_i \cup \{T_{p,x,y}\}) \vert C_i \in C \bigr\}`,
it's easier to compute using :math:`k` adjacent stops.

..  math::

    D \gets \bigl\{ \sigma (C_i \cup \{T_{p,x,y}\}) \vert C_i \in C \land x-k \leq i < x+k \bigr\}

Of course, this can be optimized so that the first value that passes the
:math:`\sigma(C_{x\pm k} \cup \{ T_{p,x,y} \}) < \epsilon` test stops the
processing.

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

..  autofunction:: test.spike_stats.main

Optimizations
--------------

The Spike solution needs a few improvements.

It uses a brute-force match when clustering stops.  This should be a search
of adjacent stops.

It has an arbitrary threshold for clustering.

It does not do a singleton-removal pass after clustering.

The initial grouping by route/direction/stop should be used to create
an ordered dictionary so that all
subsequent steps can be simple generators without additional sorting or
dictionary construction.