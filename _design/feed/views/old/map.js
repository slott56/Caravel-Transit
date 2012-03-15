/* Feed documents with a status of everything other than new */
function(doc){
    if(doc.doc_type=='Feed' && doc.status!="new") {
        emit(doc.timestamp, doc)
        }
    }