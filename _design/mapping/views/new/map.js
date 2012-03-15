/* Mapping documents with no status.*/
function(doc){
    var has_status = 'status' in doc && doc.status != null;
    if(doc.doc_type=='Mapping' && !has_status) {
        emit( doc.timestamp, doc )
        }
    }