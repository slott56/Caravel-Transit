#!/usr/bin/env python2.7
"""Caravel Couch DB settings
"""
from couchdbkit import Server

database_uri= "http://localhost:5984/"
database_name= 'couchdbkit_test'

#    database_uri= "http://hrt.iriscouch.com:5984/"
#    database_name= 'feed'

connection = Server(database_uri)
db = connection.get_or_create_db(database_name)
