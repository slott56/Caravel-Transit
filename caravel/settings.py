#!/usr/bin/env python2.7
"""Caravel Couch DB settings.
"""

#Couch Push
#Test Database
db_url= "http://127.0.0.1:5984/couchdbkit_test"
#Production Database
#db_url= "http://hrt.iriscouch.com:5984/feed"

#Log Tail
logtail_status_filename= "logtail.history"
logtail_size_limit= 1*1000*1000

# Reformat

# Capture
capture_extract_filename= "hrtrtf.txt"
capture_csv_filename= "hrtrtf.csv"

# Change Notification
# (Hour, Minute, Second) of the day at which to do daily tasks
change_notification_daily_task_time = ( 3, 0, 0 )