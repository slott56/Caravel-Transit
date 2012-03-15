/* Feed documents with a status of new */
function(doc){
    if(doc.doc_type=='Feed' && doc.status=="new") {
        emit(doc.timestamp, doc)
        }
    }