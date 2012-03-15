/* Mapping documents which are valid and mapping type stop.*/
function(doc){
    var valid = 'status' in doc && doc.status == 'valid';
    if(doc.doc_type=='Mapping' && valid && doc.mapping_type == 'stop' ) {
        emit( [doc.effective_date,doc.ending_date], doc )
        }
    }