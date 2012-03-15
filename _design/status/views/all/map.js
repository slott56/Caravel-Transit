/* All Status documents */
function(doc){
    if(doc.doc_type=='Route' || doc.doc_type=='RouteStop' || doc.doc_type=='Vehicle') {
        var key = doc.date;
        emit( key, doc )
        }
    }