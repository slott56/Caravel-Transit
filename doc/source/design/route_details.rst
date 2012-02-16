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

Given a sequence of days, :math:`w_0, w_1, w_2, \ldots, w_n`, we have a matrix
of arrival times on each day for the given position, :math:`p`.  Generally,
this sequence of days will all have the same day-of-week.

..  math::

    T_p = \begin{vmatrix}
    T_{p,w_0,0} & T_{p,w_0,1} & T_{p,w_0,2} & \ldots & T_{p,w_0,s} \\
    T_{p,w_1,0} & T_{p,w_1,1} & T_{p,w_1,2} & \ldots & T_{p,w_1,s} \\
    T_{p,w_2,0} & T_{p,w_2,1} & T_{p,w_2,2} & \ldots & T_{p,w_2,s} \\
    \ldots \\
    T_{p,w_n,0} & T_{p,w_n,1} & T_{p,w_n,2} & \ldots & T_{p,w_n,s} \\
    \end{vmatrix}

We can compute a mean (and other descriptive statistics) down the colum to get a
set of average arrival times throughout a given day.

Each distinct arrival sequence number, :math:`s`, will have an average arrival,
:math:`\mu_{p,s}`, as
well as a standard deviation, :math:`\sigma_{p,s}`.

..  math::

    \mu_{p,s} = \mu_n\{T_{p,w_n,s}\} = \frac{\sum_n{T_{p,w_n,s}}}{\lvert T_{p,w_n,s} \rvert}

..  math::

    \sigma_{p,s} = \sigma_n\{T_{p,w_n,s}\}

Pragmatically, data may be missing or inconsistent.  The matrix will have
gaps that must be handled gracefully.  The column of data must be filtered
to assure that all of the values are within a "reasonable" time window
of each other.

Barring changes in the route, the sequence of values will reflect a consistent
ordering.  A kind of "look-ahead" algorithm should allow aligning each element
in the vector row with elements in other rows.

Finding Routes
-----------------

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
