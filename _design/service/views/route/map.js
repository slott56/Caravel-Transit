/* Service Route Definition Documents */
function(doc){
    if(doc.doc_type=='Route_Definition') {
        emit( doc.route_id, doc )
        }
    }