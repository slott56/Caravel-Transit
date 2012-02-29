Data Acquisition
====================

See http://www.transitchicago.com/developers/bustracker.aspx

Source information: ftp://216.54.15.3/Anrd/

Two Files: :file:`hrtrtf.txt` is the data. :file:`vid.csv` is a map of route ids to vehicle ids

Need Routes and Segments to see where bus is.

Vehicle Information
------------------------

Vehicle Id information in :file:`vid.csv` has the following format::

    {'RID': '2218', 'VehID': '2018'}

RID is the route ID.  VehID is the Vehicle ID.

Vehicle Report V1
-----------------------

There are three types of records::

    07:04:42 02/15  V.1.2233  H.0.0  MT_LOCATION    Lat/Lon:370620935/-763413842 [Valid]  Adher:-1 [Valid]  Odom:2668 [Valid]  DGPS:On  FOM:2

    07:04:42 02/15  V.1.3515  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:37  Dwell:22  Rte:65  Dir:2  TP:352  Stop:69  Svc:1  Blk:203  Lat/Lon:370425333/-764286136 [Valid]  Adher:-1 [Valid]  Odom:1712 [Valid]  DGPS:On  FOM:2

    07:04:42 02/15  V.1.2236  H.0.0  MT_TIMEPOINTCROSSING   Time:07:04:36  Arrival  Rte:4  Dir:2  TP:329  Stop:45  Svc:1  Blk:221  Lat/Lon:370315618/-763461352 [Valid]  Adher:2 [Valid]  Odom:1924 [Valid]  DGPS:On  FOM:2

Field by Field

0.  Time in ``"%H:%M:%S"`` format
1.  Date in ``"%m/%d"`` format
2.  Vehicle ID in ``"V\.1\.(\d+)"`` format
3.  ``H.0.0``
4.  Either ``"MT_LOCATION"`` or ``"MT_TIMEPOINTCROSSING"``

For MT_LOCATION

5.  Location in ``"Lat/Lon:%d/%d"`` format.
6.  '[Invalid]': 4, '[Valid]': 269
7.  ``"Adher:%d"``
8.  '[Invalid]': 64, '[Valid]': 209
9.  ``"Odom:%d"``
10. '[Invalid]': 6, '[Valid]': 267
11. 'DGPS:Off': 8, 'DGPS:On': 265
12. ``"FOM:%d"``.  Optional.

For MT_TIMEPOINTCROSSING some additional fields are present.

5.  Actual Time in ``""Time:%H:%M:%S"`` format
6.  "Dwell:%d" or "Arrival"
7.  ``Rte:65`` - Does not match routes.txt
8.  ``Dir:2`` - Direction 1 or 2; trips.txt uses 0 or 1
9.  ``TP:352``
10. ``Stop:69``
11. ``Svc:1`` or ``Svc:4``
12. ``Blk:203``
13. Location in ``"Lat/Lon:%d/%d"`` format.
14. '[Valid]': 27
15. ``"Adher:%d"``
16. '[Valid]': 27
17.  ``"Odom:%d"``
18. '[Valid]': 27
19. 'DGPS:Off': 1, 'DGPS:On': 26
20. ``"FOM:%d"``.  Optional.

Vehicle Report V2
------------------------

There are two types of records::

    Time,Date,RID,Lat/Lon,Location Valid/Invalid,Adherence,Adherence Valid/Invalid[,Route,Direction,StopID]

    07:00:38,02/28,3247,368147270/-762487811,V,-1,V

    07:00:41,02/28,2109,368099480/-763510804,V,-1,V,28,1,30

The header, however, is unusable in the given form.