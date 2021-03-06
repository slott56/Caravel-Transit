#!/usr/bin/env python2.7
"""Test Caravel FTP_acquire module.
"""
from __future__ import print_function
import unittest
import logging
import sys
import datetime
import os
import time
from contextlib import closing
import caravel.LogCapture.ftp_acquire

class MockFTP( object ):
    dirlist= ""
    history= []
    def __init__( self, **kwargs ):
        self.kwargs= kwargs
        self.closed= False
    def close( self ):
        self.closed= True
    def dir( self, command, writer ):
        self.history.append( command )
        for line in self.dirlist.splitlines():
            writer( line )
    def retrbinary( self, command, writer ):
        self.history.append( command )
        writer( "New Binary\n" )
    def retrlines( self, command, writer ):
        self.history.append( command )
        writer( "New Lines" )
        writer( "Of Data" )

class MockHTTP( object ):
    data= "New Lines Of Data"
    history= []
    def __init__( self ):
        self.closed= False
    def open( self, *args ):
        MockHTTP.history.append( args )
        return self
    def close( self ):
        self.closed= True
    def read( self ):
        return self.data
    def __iter__( self ):
        return iter( self.data.splitlines() )

class Temp_File_Cleanup( unittest.TestCase ):
    today= datetime.datetime.now()
    yesterday= today-datetime.timedelta( days=1 )
    template_directory= """\
{0}                 3975 vid.csv
{0}                43107 hrtrtf.txt
"""
    def tearDown( self ):
        try:
            os.remove( 'test/vid.csv' )
        except OSError as e:
            self.assertEqual( 2, e.errno )
        if self.name:
            try:
                os.remove( self.name )
            except OSError as e:
                self.assertEqual( 2, e.errno )

class Test_No_VID( Temp_File_Cleanup ):
    def setUp( self ):
        class NewVIDFTP( MockFTP ):
            dirlist= self.template_directory.format( self.today.strftime( "%m-%d-%y %I:%M%p") )
            history= []
        self.ftp_class= NewVIDFTP
        try:
            os.remove( 'test/vid.csv' )
        except OSError as e:
            self.assertEqual( 2, e.errno )
        self.name= None
    def runTest( self ):
        self.name= caravel.LogCapture.ftp_acquire.get_report_files( self.ftp_class, target_dir='test' )
        self.assertTrue( os.path.exists( 'test/vid.csv' ) )
        self.assertEqual( ['Anrd', 'RETR Anrd/vid.csv', 'RETR Anrd/hrtrtf.txt'], self.ftp_class.history )
        with open('test/vid.csv','rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "New Binary\n", new_data )
        with open(self.name,'rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "New Lines\nOf Data\n", new_data )

class Test_New_VID( Temp_File_Cleanup ):
    def setUp( self ):
        class NewVIDFTP( MockFTP ):
            dirlist= self.template_directory.format( self.today.strftime( "%m-%d-%y %I:%M%p") )
            history= []
        self.ftp_class= NewVIDFTP
        try:
            os.remove( 'test/vid.csv' )
        except OSError as e:
            self.assertEqual( 2, e.errno )
        with open('test/vid.csv','w') as vid:
            vid.write( "original\n" )
        old = time.mktime( self.yesterday.utctimetuple() )
        os.utime( 'test/vid.csv', (old, old) )
        self.name= None
    def runTest( self ):
        self.name= caravel.LogCapture.ftp_acquire.get_report_files( self.ftp_class, target_dir='test' )
        self.assertTrue( os.path.exists( 'test/vid.csv' ) )
        with open('test/vid.csv','rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "New Binary\n", new_data )
        with open(self.name,'rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "New Lines\nOf Data\n", new_data )
        self.assertEqual( ['Anrd', 'RETR Anrd/vid.csv', 'RETR Anrd/hrtrtf.txt'], self.ftp_class.history )

class Test_Old_VID( Temp_File_Cleanup ):
    def setUp( self ):
        class OldVIDFTP( MockFTP ):
            dirlist= self.template_directory.format( self.yesterday.strftime( "%m-%d-%y %I:%M%p") )
            history= []
        self.ftp_class= OldVIDFTP
        try:
            os.remove( 'test/vid.csv' )
        except OSError as e:
            self.assertEqual( 2, e.errno )
        with open('test/vid.csv','w') as vid:
            vid.write( "original\n" )
        new = time.mktime( self.today.timetuple() )
        os.utime( 'test/vid.csv', (new, new) )
        self.name= None
    def runTest( self ):
        self.name= caravel.LogCapture.ftp_acquire.get_report_files( self.ftp_class, target_dir='test' )
        self.assertTrue( os.path.exists( 'test/vid.csv' ) )
        with open('test/vid.csv','rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "original\n", new_data )
        with open(self.name,'rb') as new_file:
            new_data= new_file.read()
        self.assertEqual( "New Lines\nOf Data\n", new_data )
        self.assertEqual( ['Anrd', 'RETR Anrd/hrtrtf.txt'], self.ftp_class.history )

class Test_Reader( unittest.TestCase ):
    def setUp( self ):
        self.http_class= MockHTTP
        self.http_class.data= "Several\nLines\nOf\nData\n"
    def runTest( self ):
        with closing( caravel.LogCapture.ftp_acquire.report_reader( self.http_class() ) ) as source:
            src_iter= iter( source )
            self.assertEqual( "Several", next(src_iter) )
            self.assertEqual( "Lines", next(src_iter) )
            self.assertEqual( "Of", next(src_iter) )
            self.assertEqual( "Data", next(src_iter) )

if __name__ == "__main__":
    logging.basicConfig( stream=sys.stderr, level=logging.WARN )
    unittest.main()