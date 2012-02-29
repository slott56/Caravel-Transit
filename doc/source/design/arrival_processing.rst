Arrival Detail Enrichment
==========================

Wait, what?

When an application locates an appropriate stop that matches a report,
there is an unlimited number of "enrichment" steps that could be performed
around that stop.

-   Add route and trip information.

-   Add next stop information.

-   All all next stops in this trip.

The issue is that there are four closely-related bits of processing.

1.  The core algorithm that uses a Report to locate a Stop.
    If a stop is found, enrich it.  Write to one file.
    if a stop cannot be found, Write to a separate file.

2.  The initial stop lookup.

3.  Any additional enrichments to that lookup.

4.  The file writes.

These are entangled because the file writes (to create proper CSV)
need to know about the enrichments, binding them together with respect
to attribute names.

The core algorithm, also, can "fail" at during lookup or enrichment.  Any problems mean
that the report is written to a reject file.  Only success in lookup and
subsequence enrichment leads to a report written to the "good" file.

To make it more challenging, enrichment could for a kind of **Chain of Command**,
where multiple enrichments can be used.

Ideally, each Enrichment is an independent object.  The write polls them
for column name information.  The core algorothm then passes the results
to them.