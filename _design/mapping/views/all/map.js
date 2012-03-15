/* Mapping documents */
function(doc){
    if(doc.doc_type=='Mapping') {
        var key = doc.mapping_type + "/" + doc.effective_date;
        emit( key, doc )
        }
    }