..  _design.transit_resource:

RESTful API for Transit Service Definitions
=============================================

The central use case expands into a few closely-related scenarios.

1.  User picks route and stop from a menu.

    For example, they are at a stop and can read the signage to figure out where
    they are.  Or, they is getting ready to go outside to wait
    for a bus.

2.  User is relying on smartphone GPS to pick nearest route and stop.
    This is a bit more complex, since it requires a geospatial query.

3.  User has a destination in mind and needs to know closest stop
    relevant to a route that gets to the desired destination.  This means
    that alterantive stops, routes, transfers and run times all need
    to be calculated.  This is quite complex.  This is best
    handed off to Google.

Data Model
-------------

Stops are identified by an ID as well as GPS coordinates.

A stop is associated with a route via two intermediate relationships:
stop-time and trip.

A stop is associated a stop_time.  A stop_time is associated with a trip.

The trip is a particular pass along a route.  It's constrained by the
kinds of service (usually day-of-week).

See :ref:`design.transit` for details.

Note that the trip and stop-time information is essential for navigating
the data structure, but not interesting to a person trying to catch
the bus.


Services
-----------------------
Here are some couch db view and list definitions.

..  literalinclude:: ../../../_design/service/views/bydate/map.js
    :language: javascript

..  literalinclude:: ../../../_design/service/views/route/map.js
    :language: javascript

..  literalinclude:: ../../../_design/service/views/stop/map.js
    :language: javascript

..  literalinclude:: ../../../_design/service/views/stop_time/map.js
    :language: javascript

..  literalinclude:: ../../../_design/service/views/trip/map.js
    :language: javascript
