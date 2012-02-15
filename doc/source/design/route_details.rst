Route Discovery
================

Without a route map, details can still be acquired.

Each Dwell and Arrival report contains Route, Direction, Stop and Time
information.

Each report is effectively a pair :math:`\langle p, t \rangle`.  This is the
position, :math:`p = \langle r, d, s \rangle`,  (route, *r*, direction, *d*, stop, *s*)
and the time, *t*.

The time has a number of attributes: :math:`t.d` is the date;
:math:`t.w` is the day of the week; :math:`t.t` is time of day.

The universe of data, is set of reports, :math:`R`.

..  math::

    R = \{ \langle p_0, t_0 \rangle, \langle p_1, t_1 \rangle, \ldots \}

For each position, :math:`p`, we have a subset of reports for that position

..  math::

    R_p = \{ t_n \vert \langle p_n, t_n \rangle \in R \land p_n = p \}

We can partition the data into one-day slices.
For each day, :math:`d`, from the domain of available dates, :math:`d \in \{ t_n.d \vert t_n \in R_p\}`.

..  math::

    R_{p,d} = \langle t_n.t \vert  t_n \in R_p \land t_n.d = d \rangle

Note that :math:`R_{p,d}` is a vector of times only.  A specific arrival time
during the day is :math:`R_{p,d,k}`.  It's simply a number of seconds past
some epochal time, like midnight.

Each day of the week should have a similar ordered sequence of arrival timestamps.
There's no *a priori* reason to separate the schedule into weekday and weekend.
It's simpler to treat each of the seven days as distinct.

Given a sequence of days, :math:`w_0, w_1, w_2, \ldots, w_n`, we have a matrix
of arrival times on each day for the given position, :math:`p`.  Generally,
this sequence of days will all have the same day-of-week.

..  math::

    R_p = \begin{vmatrix}
    R_{p,w_0,0} & R_{p,w_0,1} & R_{p,w_0,2} & \ldots & R_{p,w_0,m} \\
    R_{p,w_1,0} & R_{p,w_1,1} & R_{p,w_1,2} & \ldots & R_{p,w_1,m} \\
    R_{p,w_2,0} & R_{p,w_2,1} & R_{p,w_2,2} & \ldots & R_{p,w_2,m} \\
    \ldots \\
    R_{p,w_n,0} & R_{p,w_n,1} & R_{p,w_n,2} & \ldots & R_{p,w_n,m} \\
    \end{vmatrix}

We can compute a mean (and other descriptive statistics) down the colum to get a
set of average arrival times throughout a given day.

Each distinct time of day, :math:`k`, will have an average arrival,
:math:`\mu_{p,k}`, as
well as a standard deviation, :math:`\sigma_{p,k}`.

..  math::

    \mu_{p,k} = \mu_n\{R_{p,w_n,k}\}

..  math::

    \sigma_{p,k} = \sigma_n\{R_{p,w_n,k}\}

Pragmatically, data may be missing or inconsistent.  The matrix will have
gaps that must be handled gracefully.  The column of data must be filtered
to assure that all of the values are within a "reasonable" time window
of each other.

Barring changes in the route, the sequence of values will reflect a consistent
ordering.  A kind of "look-ahead" algorithm should allow aligning each element
in the vector row with elements in other rows.