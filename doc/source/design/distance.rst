Distance Calculations
=======================

Proper calculation from http://williams.best.vwh.net/avform.htm#Dist

The great circle distance *d* between two points with coordinates {lat1,lon1} and {lat2,lon2} is given by:

::

    d=acos(sin(lat1)*sin(lat2)+cos(lat1)*cos(lat2)*cos(lon1-lon2))

..  math::

    d = \arccos \bigl[ \sin(la_1) \sin(la_2)+\cos(la_1) \cos(la_2) \cos(lo_1-lo_2) \bigr]

A mathematically equivalent formula, which is less subject to rounding error for short distances is:

::

    d=2*asin(sqrt((sin((lat1-lat2)/2))^2 +
                 cos(lat1)*cos(lat2)*(sin((lon1-lon2)/2))^2))

..  math::

    a &= \bigl[\sin(\frac{la_1-la_2}{2})\bigr]^2 + \cos{la_1}\cos{la_2}\bigl[\sin(\frac{lo_1-lo_2}{2})\bigr]^2 \\
    c &= 2 \arcsin { \sqrt{ a }  }

The angle, *c*, is in radians.  It needs to be converted to degrees and then distance.
For nautical miles it's :math:`c\times(60\times 180\div \pi)`, about 3,437.746.

From http://www.movable-type.co.uk/scripts/latlong.html

..  math::

    a &= \bigl[\sin(\frac{la_1-la_2}{2})\bigr]^2 + \cos{la_1}\cos{la_2}\bigl[\sin(\frac{lo_1-lo_2}{2})\bigr]^2 \\
    c &= 2 \arctan { \frac{\sqrt{a}}{\sqrt{1-a}} }

The angle, *c*, is in radians.  It can be converted to distance by multiplying by
the earth's mean radius;  6,378.1 kilometers, 3,961.3 miles and
3,440.07 Nautical miles (nm).

The Equirectangular Approximation is the following.

..  math::

    x &= (lo_2-lo_1) \times \cos( \frac{la_1+la_2}{2} ) \\
    y &= la_2 - la_1 \\
    c &= \sqrt{ x^2 + y^2 }

The angle, *c*, is in radians.

DGPS is only theoretically accurate to 5m (16.4 ft.);
this is 0.0027 nm (0.0031 mile).  Therefore, we only really
need an accuracy of about 1/380.

Two lat/lon points are coincident if :math:`d \leq 0.003`.