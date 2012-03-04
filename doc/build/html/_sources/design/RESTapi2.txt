..  _design.transit_resource:

RESTful API for Transit Resources
======================================

The central use case expands into a few closely-related scenarios.

1.  User picks route and stop from a menu.

    For example, they are at a stop and can read the signage to figure out where
    they are.  Or, they is getting ready to go outside to wait
    for a bus.

2.  User is relying on smartphone GPS to pick nearest route and stop.

3.  User has a destination in mind and needs to know closest stop
    relevant to a route that gets to the desired destination.  This means
    that alterantive stops, routes, transfers and run times all need
    to be calculated.  This is rather complex.

Data Model
-------------

Stops are identified by a name and GPS coordinates.

A stop is associated with a route via two intermediate relationships:
stop-time and trip.

A stop is associated a stop_time.  A stop_time is associated with a trip.

The trip is a particular pass along a route.  It's constrained by the
kinds of service (usually day-of-week).

See :ref:`design.transit` for details.

Note that the trip and stop-time information is essential for navigating
the data structure, but not interesting to a person trying to catch
the bus.


Route Access
-----------------------

Some candidate RESTful requests for route information.

Given a date, the subset of allowed trips can be located.
From the subset of allowed trips in the future only, the distinct routes
can be determined as well as the distinct stops.

:samp:`/route/`

    The route list.  All 70.

:samp:`/route/{id}/`

    All stops along the route, each stop decorated with direction and service.
    The time-of-day details for a given trip are not provided; they are associated
    with a specific stop.

:samp:`/route/{id}/{dir}/`

    All stops in a particular direction along the route.  The direction is
    more-or-less inoound or outbound, and is actually a foreign key to a direction
    table.

:samp:`/route/{id}/?date={date}`

    All stops along the route filtered by services available on the given date.
    Day of week is generally sufficient, but there are calendar overrides,
    so full date is required.

:samp:`/route/{id}/?date={date}&time={time}`

    All stops along the route, filtered by services available on the given date
    on or after the given time.  If these are ordered by distance (along the route's
    direction) it should provide a tidy summary of the route.

Stop Access
------------

Some candidate RESTful requests for stop information.

:samp:`/stop/`

    All stops.  3210 of 'em.

:samp:`/stop/{id}/`

    A specific stop.

:samp:`/stop/{id}/?date={date}`

    All stop times for this stop constrained by services on the specific date.

:samp:`/stop/{id}/?date={date}&time={time}`

    All stop times at this stop, filtered by services available on the given date
    on or after the given time

Position Search
---------------

Given a GPS coordinates (and an optional date), the closest stop can be located irrespective
of bus schedule.

:samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}`

    This can find the nearest stops to this coordinate.

:samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&dir={dir}`

    This can find the nearest stops for all routes heading in this direction.

:samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}`

    This finds the nearest stops with a service that is active on the given date.

:samp:`/stop/?latlng={nn.nnnnnn,mm.mmmmmm}&time={time}`

    This finds the nearest stops with a service that is active on the given date
    and on or after the given time.


:samp:`/route/{id}/?latlng={nn.nnnnnn,mm.mmmmmm}`

    This can find the nearest stops on the given route to this coordinate.

:samp:`/route/{id}/{dir}/?latlng={nn.nnnnnn,mm.mmmmmm}`

    This can find the nearest stops on the given route and direction to this coordinate.

:samp:`/route/{id}/{dir}/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}`

    This can find the nearest stops on the given route and direction to this coordinate
    active on the given date.

:samp:`/route/{id}/{dir}/?latlng={nn.nnnnnn,mm.mmmmmm}&date={date}&time={time}`

    This can find the nearest stops on the given route and direction to this coordinate
    active on the given date and on or after the given time.
