..  _design.transit:

General Transit Feed Data
=====================================

See http://googletf.gohrt.com/google_transit.zip

See http://www.gtfs-data-exchange.com/agency/hampton-roads-transit-hrt/

See https://developers.google.com/transit/gtfs/reference

Per the GTFS standard, this contains the following files:

-   agency.txt
-   calendar.txt
-   calendar_dates.txt
-   fare_attributes.txt
-   fare_rules.txt
-   routes.txt
-   stop_times.txt
-   stops.txt
-   trips.txt


Agency
--------

::

    agency_name,agency_url,agency_timezone
    Hampton Roads Transit (HRT),http://www.gohrt.com/,America/New_York

Calendar
----------

Standard Service.

::

    service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
    WE,1,1,1,1,1,0,0,20120122,20121229
    SA,0,0,0,0,0,1,0,20120122,20121229
    SU,0,0,0,0,0,0,1,20120122,20121229
    MR,1,1,1,1,0,0,0,20120122,20121229
    FR,0,0,0,0,1,0,0,20120122,20121229

Calendar Dates
---------------

Holidays that provide some kind of exception to standard service.

::

    service_id,date,exception_type
    MR,20120102,2
    WE,20120102,2
    SA,20120102,1
    MR,20120116,2
    WE,20120116,2
    SA,20120116,1
    MR,20120528,2
    WE,20120528,2
    SA,20120528,1
    MR,20120704,2
    WE,20120704,2
    SA,20120704,1
    MR,20120903,2
    WE,20120903,2
    SA,20120903,1
    MR,20121122,2
    WE,20121122,2
    SU,20121122,1
    FR,20121123,2
    WE,20121123,2
    SA,20121123,1
    MR,20121225,2
    WE,20121225,2
    SU,20121225,1

Fare Attributes
-----------------

The domain of fares which apply to the various routes.

::

    fare_id,price,currency_type,payment_method,transfers
    1,1.50,USD,0,2
    2,1.00,USD,0,0
    3,1.50,USD,1,0
    6,3.00,USD,0,0

Fare Rules
-----------

The specific fare-route assignments.

::

    fare_id,route_id
    1,001
    1,002

69 lines of mapping from Fare to Route.

Trips
--------

This is the mapping from route to multiple trips along that route
during a day.  The route has generic stops.  The trip has specific
stop times.

::

    route_id,service_id,trip_id,direction_id,block_id
    090,WE,1,0,090 -  1
    090,WE,2,0,090 -  1

7,907 lines.

Routes
--------

The names of the routes.

::

    route_id,route_short_name,route_long_name,route_desc,route_type,route_url
    001,1,GRANBY ST, Downtown Norfolk Pembroke East ,3,http://www.gohrt.com/routes/route-1.pdf
    002,2,HAMPTON BLVD, Naval Station Norfolk/Hampton Boulevard ,3,http://www.gohrt.com/routes/route-2.pdf

70 lines of route names.

Stops
--------

The names of the stops assigned to the various routes.

::

    stop_id,stop_name,stop_lat,stop_lon
    0001,CHARLOTTE & MONTICELLO,36.85192,-76.28732
    0003,SAINT PAULS & CHARLOTTE,36.85155,-76.28542
    0006,SAINT PAULS & PLUME,36.84645,-76.28593

3,210 lines of stops.

Stop Times
------------

The stop time for each trip around a route.

::

    trip_id,arrival_time,departure_time,stop_id,stop_sequence,timepoint
    1,7:15:00,7:15:00,F001,1,1
    1,7:30:00,7:30:00,F002,2,1
    1,7:35:00,7:35:00,F003,3,1

303,115 lines of stop times.

The timepoint is a 0/1 flag of some kind.

GTFS Data Model
----------------

The GTFS is a normalied, relational model.  This can, however, be restructured into
hierarchical "document" model that's more useful.  First, we'll
look at the normalized view.

We can ignore Agency, Fare Attributes and Fare Rules for the purposes of
determining bus arrival times.

The `Calendar`_ defines a class of service (WE, SA, SU, MR, FR) and the
days on which that class of service is offered.

The `Calendar Dates`_ provides for two kinds of exceptions, coded ``1`` and ``2``.
A value of 1 indicates that service has been added for the specified date.
A value of 2 indicates that service has been removed for the specified date.

For a given class of service, the `Trips`_ defines the routes that apply.  Each
route may have several trips during the day.

Each route has a number of `Stops`_.

Each trip through a route has a number of `Stop Times`_.

A YUML (http://www.yuml.me) specification::

    [Class]<1-1..m>[Trip]
    [Trip]<1..m-1>[Route]
    [Trip]<1-1..m>[Stop Time]
    [Stop]<1-1..m>[Stop Time]

..  figure:: 600cd99.png

    Logical View of GFTS Data.

Hierarchical Document Model
----------------------------

We have a collection of hierarchies that are closely intertwined.  All of these
are needed for different kinds of requests and processing.  Unlike a normalized
view, there is no canonical document structure.

Note that we have two different taxonomies:

-   By Geography -- route, direction and stop.

-   By Time -- weekday service class and time of day.

[Route [Direction [Stop]]].

    This is a sequence of routes. Each route has a pair of directions.
    Each direction has a sequence of stop references.
    This is a union of stops from all trips.
    This must be coupled with a simple mapping of stop details.

    This is a summary of each route.

[Route [Direction [(Service, Stop-Time, Stop)]]]

    This is a sequence of routes. Each route has a pair of directions.
    Each direction has a sequence of stop-time and stop references.
    This includes all trips.
    This must be coupled with a simple mapping of stop details.

    This can be filtered to get route by date, weekly service id,
    or even time-of-day.

[Stop [Route [Direction [(Service, Stop-Time)]]]]

    This is a dictionary of stops, providing service, stop-time and route
    data for that stop.  Generally a stop belongs to one route,
    but the times belong to a particular direction of the trip.

[Service [Route [Direction [(Stop-Time, Stop)]]]]

    Given a service, this is all active routes and all stops on that