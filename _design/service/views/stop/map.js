/* Service Stop Definition Documents */
function(doc){
    if(doc.doc_type=='Stop_Definition') {
        emit( doc.stop_id, doc )
        }
    }