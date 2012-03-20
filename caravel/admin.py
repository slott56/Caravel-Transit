#!/usr/bin/env python2.7
"""Caravel CouchDB Admin Functions.

This will create databases, create applications.

It will also do things like clean the feed database.
"""
from __future__ import print_function
from couchdbkit.designer import push
from caravel.conf import settings
import pprint
from collections import defaultdict

def define_views( db ):
    """Purely administrative.  Done once (or so) to set the views.

    Similar to the way that couchapp works.

    https://github.com/couchapp/couchapp/tree/
    """
    push('_design/feed', db)
    push('_design/mapping', db)
    push('_design/status', db)

def check_views( db ):
    expected = [ '_design/feed', '_design/mapping', '_design/status' ]
    for id in expected:
        pprint.pprint( db[id] )

    for doc in db.all_docs():
        id= doc['id']
        if id.startswith('_design') and id not in expected:
            print( "Unexpected", id )

    if 'foo' in db:
        print( db['foo'] )

def integrity_check( db ):
    """Looking for objects with missing or unknown doc_type attributes."""
    models = [ 'Mapping', 'Feed', 'Route', 'RouteStop', 'Stop', 'Vehicle' ]
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