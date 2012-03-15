/* Feed documents irrespective of status */
function(doc){
    if(doc.doc_type=='Feed') {
        emit(doc.timestamp, doc)
        }
    }