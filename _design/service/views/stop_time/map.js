/* Service Route Definition Documents Organized by arrival times at a stop */
function(doc){
    if(doc.doc_type=='Route_Definition') {
        for(svc in doc.trips) {
            for(trip in doc.trips[svc]) {
                for( i in doc.trips[svc][trip].stops ) {
                    emit( doc.trips[svc][trip].stops[i].arrival_time, doc )
                }
            }
        }
    }
}