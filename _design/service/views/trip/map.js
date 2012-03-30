/* Service Route Definition Documents Organized by Trip_ID */
function(doc){
    if(doc.doc_type=='Route_Definition') {
        for(t in doc.trips ) {
            emit( doc.trips[t].trip_id, doc )
            }
        }
    }