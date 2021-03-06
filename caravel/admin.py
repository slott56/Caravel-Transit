#!/usr/bin/env python2.7
"""Caravel CouchDB Admin Functions.

Run this as a main program to create the views.

::

    python2.7 -m caravel.admin

This will use the settings to get the database connection and
reset the view definitions.

This will create databases, create applications and check database
integrity.

..  autofunction:: define_views
..  autofunction:: check_views
..  autofunction:: integrity_check
"""
from __future__ import print_function
from couchdbkit.designer import push
from caravel.conf import settings
import pprint
from collections import defaultdict
import glob

apps = glob.glob("_design/*")

def define_views( db ):
    """Purely administrative.  Done once (or so) to set the views.

    Similar to the way that couchapp works.

    https://github.com/couchapp/couchapp/tree/
    """
    for app in apps:
        push( app, db )

def check_views( db ):
    for id in apps:
        pprint.pprint( db[id] )

    for doc in db.all_docs():
        id= doc['id']
        if id.startswith('_design') and id not in apps:
            print( "Unexpected", id )

    if 'foo' in db:
        print( db['foo'] )

def integrity_check( db ):
    """Looking for objects with missing or unknown doc_type attributes."""
    models = [ 'Mapping', 'Feed', 'Route', 'RouteStop', 'Stop', 'Vehicle',
              'Service', 'Route_Definition', 'Stop_Definition',
              ]
    counts = defaultdict(int)
    for doc in db.all_docs():
        id= doc['id']
        if id.startswith("_"): continue
        counts['objects'] += 1
        obj= db[id]
        if 'doc_type' not in obj:
            pprint.pprint( obj )
            counts['bad'] += 1
        elif obj['doc_type'] not in models:
            pprint.pprint( obj )
            counts['bad'] += 1
        else:
            pass # known model type.
            counts['good'] += 1
    pprint.pprint( dict(counts) )

if __name__ == "__main__":
    define_views( settings.db )
    check_views( settings.db )
    integrity_check( settings.db )
    settings.db.compact()