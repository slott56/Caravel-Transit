#!/usr/bin/env python2.7
"""The Caravel Configuration Package.

This echoes Django's lazy configuration.  It will -- when requested --
create the database connection.

..  autoclass:: Settings

:path:
    Location of the settings file.   The environment
    variable :envvar:`CARAVEL_SETTINGS` is used to locate
    the appropriate module.

:settings:
    The :class:`Settings` object, ready for use.

Defaults
========

    db_url= 'http://localhost:5984/hrtransit/'
    capture_extract_filename= 'hrtrtf.txt'
    capture_csv_filename= 'hrtrtf.csv'
    logtail_status_filename= 'logtail.history'
    logtail_size_limit= 1*1000*1000
    change_notification_daily_task_time = ( 3, 0, 0 ) # 3:00 AM

"""
import urlparse
from couchdbkit import Server
import os

class Settings( object ):
    """A lazy class to establish the database connection as well as other
    settings.

    This class offers two special attributes, ``db`` and ``connection``
    which are only created only when specifically requested.

    All other settings are loaded the first time a setting is needed.
    """
    def __init__( self, path="settings.py", **defaults ):
        self.__dict__.update( defaults )
        self._path= path
        self._settings= None
    def __getattr__( self, name ):
        if not self._settings:
            self._load()
        if name == 'db' or name == 'connection':
            if 'db' not in self._settings:
                p = urlparse.urlparse(self._settings['db_url'])
                database_uri= "{0.scheme}://{0.netloc}".format( p )
                database_name= p.path

                connection = Server(database_uri)
                db = connection.get_or_create_db(database_name)

                self._settings['connection']= connection
                self._settings['db']= db
        return self._settings[name]

    def _load( self ):
        self._settings= {}
        execfile( self._path, self._settings )

    def __setattr__( self, name, value ):
        if name.startswith('_'):
            # Internal names
            self.__dict__[name]= value
            return
        if name == 'db' or name == 'connection':
            # Late Binding Names
            raise KeyError( "Set db_url to control db and connection." )
        # All other names
        self._settings[name]= value

path= os.environ.get('CARAVEL_SETTINGS', 'caravel/settings.py')
settings = Settings(path,
    db_url= "http://localhost:5984/hrtransit/",
    capture_extract_filename= 'hrtrtf.txt',
    capture_csv_filename= 'hrtrtf.csv',
    logtail_status_filename= "logtail.history",
    logtail_size_limit= 1*1000*1000,
    change_notification_daily_task_time = ( 3, 0, 0 ),
    )


if __name__ == "__main__":
    print( settings.db )