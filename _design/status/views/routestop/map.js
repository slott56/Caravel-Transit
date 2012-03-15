/* RouteStop Status documents */
function(doc){
    if(doc.doc_type=='RouteStop') {
        emit( doc._id, doc )
        }
    }