=============
Use Cases
=============

There are -- actually -- two actors.

-   The rider

-   The historian

Rider Use Cases
=================

The rider really only has one use case.

    As an HRT rider, I want to know when will the next bus get here
    so I can decide how to spend my time or whether I want to use
    an alternate form of transportation.

By "here", I mean a given stop on a given route for a bus heading
in a particular direction.  Ideally, this is based on GPS from a phone
which correlates with bus stops.

Due to GPS errors, it may be ambiguous which stop a person is waiting at.
It's rarely clear which route is desired.  In the case of very wide streets,
it may be possible to decide which  side of the steet and which route is
expected.

By "next bus", I mean the earliest to arrive bus which is on this route,
in the desired direction.

Historian Use Cases
===================

The historian has two use cases.

-   Accumulate mutli-week history to discern routes and stops from the
    available data.

-   Accumulate daily history to discern slowdowns along the various routes.

History is simplified to vehicle, position, time data.  The
position decomposes into route, direction and stop.  Other information
like vehicle odometer readings can be gracefully discarded.

For long-term history, the arrival and dwell reports are used.
Other location reports are ignored.

The short-term history includes the arrival and dwell reports from earlier
in the day.  These provide some localized trending information compared with long-term
averages.  These are organized by position (route, direction and stop).

The short-term history also includes the last few minutes of location reports.
Ideally, it's just location reports since the last stop.  However, this
can be complex to filter.  A window of the last 30 minutes of reports
may be sufficient.