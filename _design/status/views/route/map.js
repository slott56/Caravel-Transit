/* Route Status documents */
function(doc){
    if(doc.doc_type=='Route') {
        emit( doc._id, doc )
        }
    }