"""Configuration Package."""
import urlparse
from couchdbkit import Server
import os

class Settings( object ):
    def __init__( self, path="settings.py" ):
        self._path= path
        self._settings= None
    def __getattr__( self, name ):
        if not self._settings:
            self._load()
        return self._settings[name]
    def _load( self ):
        self._settings= {}
        execfile( self._path, self._settings )

        p = urlparse.urlparse(self._settings['db_url'])
        database_uri= "{0.scheme}://{0.netloc}".format( p )
        database_name= p.path

        connection = Server(database_uri)
        db = connection.get_or_create_db(database_name)

        self._settings['connection']= connection
        self._settings['db']= db

path= os.environ.get('CARAVEL_SETTINGS', 'caravel/settings.py')
settings = Settings(path)

if __name__ == "__main__":
    print( settings.db )