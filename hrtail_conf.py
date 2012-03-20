#hrtail_conf

#Couch Push
#Test Database
couchpush = { "db_url": "http://localhost:5984/couchdbkit_test" }
#Production Database
#couchpush = { "db_url": "http://hrt.iriscouch.com:5984/feed" }

#Log Tail
logtail = { "tail_status_filename": "logtail.history",
    "file_size_limit": 1000000 }

# Reformat

# Capture
capture = { "extract_filename": "hrtrtf.txt",
    "csv_filename": "hrtrtf.csv" }

