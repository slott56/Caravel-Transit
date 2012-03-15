/* Stop History documents */
function(doc){
    if(doc.doc_type=='Stop') {
        emit( doc._id, doc )
        }
    }