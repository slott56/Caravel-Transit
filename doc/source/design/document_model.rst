..  include:: <isoamsa.txt>

..  _design.document:

CouchDB Document Model
========================

See :ref:`design.transit` for the relational model.

We have a collection of hierarchical documents that are closely intertwined.
All of these are needed for different kinds of requests and processing.
Unlike a normalized relational models, there is no single *canonical* document structure.

We have at least two different document taxonomies for transit data.

-   By Geography -- route, direction and stop.

-   By Time -- weekday service class and time of day.

Additionally, we have position report documents, which can be
grouped around a vehicle id to track progress down a specific route.

Concerns
---------------------

Note that the standard relational model isn't an ideal fit for this
data.  There are several issues.

-   The route is a graph with nodes and edges corresponding to stops
    and driving segments.  Because nodes and edges are duals, only one is
    sufficient for a relational model.  Stops, for example, are easy
    to discern from the data.  Segments, however, are where slowdowns
    occur and where vehicle position reports are found.  It's difficult
    to choose one representation for a relational model.  It's also
    difficult to attempt to use both and keep them synchronized.

-   The historical data can be normalized, but it's of little value
    to do this.  A hierarchical collection of data by time period and
    trip might be
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
    See :ref:`design.distance` for more information on
    rapid distance approximations using an Equirectangular Approximation.

Relations
---------------------

The relational model contains four essential relationships.

-   ``[Class]<1-1..m>[Trip]``.  A Class of Service qualifies a number of Trips.

-   ``[Route]<1-1..m>[Trip]``.  A Route has  a number of Trips.

-   ``[Trip]<1-1..m>[Stop Time]``.  A single Trip contains a number of scheduled Stop Times.

-   ``[Stop]<1-1..m>[Stop Time]``.  A number scheduled Stop Times are planned for a given Stop.

What's important here is that Route and Stop definitions are heavily reused
by Trip and Class of Service.

A trivial hierarchy of ``[Class]->[Route]->[Trip]->[Stop Time]->[Stop]`` isn't
appropriate because of the repetition of Stop information.

Separate hierarchies based simply on the relational data may not be appropriate, either.
A Trip could be seen as a member of either of two hierarchies.

-   Service Class |map| [Trip, ...]

-   Route |map| [Trip, ...]

Similarly, A Stop Time could be seen as a member of either of two hierarchies:

-   Trip |map| [Stop Time, ...]

-   Stop |map| [Stop Time, ...]


Design Considerations
------------------------

While these queries can be handled with view that uses linked documents,
it would be advantageous to
pick an "optimal" document structure and reduce the complexity of views.

See :ref:`design.flow` for the processing steps.

See :ref:`design.transit_resource` for additional transit system queries.

See http://guide.couchdb.org/draft/why.html

Candidate Document Structures
-------------------------------

A Trip-based document seems to contain all but the Route
and Stop details.

    Trip |map| ( [Class,...], Route, Direction, [ Stop |map| [Stop Time, ...], ... ] )

A Class, separately, has calendar and calendar date information.

This is supported by a number of views.

(Route, Trip Direction) |map| [ Stop, ... ]

    This is a simple summary of a routes.

    Each route has a pair of directions. and a number of trips.
    Each direction has a sequence of stop references.
    This is a union of stops from all trips.

    This must be coupled with a simple mapping of stop details.

    Also, it must be coupled with Trip and Service Class information.

(Route, Trip Direction, Service Class) |map| [ [Trip, (Stop Time, Stop), ...], ... ]

    This ennumerates all route, direction and service combination.
    Each combination has a number of trips.  Each trip has a sequence
    of stop-times.

    This must be coupled with a simple mapping of Stop and Route details.

    This can be filtered to get route by date, weekly service id,
    or even time-of-day.

Multi-Tree Structure
---------------------

One document hierarchy is this:

    Class |map| [ Trip |map| [ Stop Time, ... ], ... ]

Another this this:

    Route |map| [ Trip |map| [ Stop Time, ... ], ... ]

Stop details are simply kept separately via references from a Stop Time.