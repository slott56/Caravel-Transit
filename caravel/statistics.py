"""Statistics tools for working with frequency counts.

..  autoclass:: FQTable
    :members:

"""
from __future__ import division
import math
from collections import defaultdict

class FQTable( defaultdict ):
    """Subclass of :class:`collections.defaultdict` that
    enforces an integer count similar to :class:`collections.Count`
    but also adds mean and standard deviation descriptive statistics.

    Note that the summary statistics are stateful; they're computed
    once and memoized.  They must be manually reset of the collection
    is changed.
    """
    def __init__( self ):
        super( FQTable, self ).__init__( int )
        self.reset()
    def reset( self ):
        """Reset the descriptive statistics."""
        self.m= None
        self.count= None
    def mean( self ):
        """Return the mean of this frequency table.

        :return: mean
        """
        if self.m: return self.m
        sum, count = 0, 0
        for k in self:
            sum += k*self[k]
            count += self[k]
        self.m= sum/count
        self.count= count
        return self.m
    def sd( self ):
        """Return the standard deviation of this frequency table.

        :return: standard deviation.  Returns None if there are fewer
            than 2 items.
        """
        if not self.m: self.m= self.mean()
        if self.count < 2: return None
        sum = 0
        for k in self:
            sum += (k-self.m)**2*self[k]
        return math.sqrt( sum/(self.count-1) )
