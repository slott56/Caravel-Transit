/* Service Calendar/Schedule Documents */
function(doc){
    if(doc.doc_type=='Service') {
        emit( doc.date, doc )
        }
    }