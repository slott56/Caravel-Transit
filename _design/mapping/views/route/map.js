/* Mapping documents which are valid and mapping type route.*/
function(doc){
    var valid = 'status' in doc && doc.status == 'valid';
    if(doc.doc_type=='Mapping' && valid && doc.mapping_type == 'route' ) {
        emit( [doc.effective_date,doc.ending_date], doc )
        }
    }