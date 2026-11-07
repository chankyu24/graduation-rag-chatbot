"""Result provenance and deterministic input signatures; saved records are owned by the separate account store."""
from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
from .utils import normalize


def input_signature(department, year, courses, activities, complete, evidence, official_requirements):
    payload = dict(department=normalize(department), year=int(year),
                   courses=sorted({normalize(c) for c in courses if normalize(c)}),
                   activities=activities, complete=complete, evidence=evidence,
                   official_requirements=official_requirements)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode('utf-8')).hexdigest()


def input_payload(department, year, courses, activities, complete, evidence, official_requirements):
    """Own a snapshot for later advice; never retain mutable widget references."""
    return deepcopy(dict(department=department, year=year, courses=list(courses),
                         activities=activities, complete=complete, evidence=evidence,
                         official_requirements=official_requirements))


def owner_scope(owner_id):
    return hashlib.sha256(str(owner_id).encode('utf-8')).hexdigest()


def stamp_result(result, signature, criteria_signature, documents_signature, *, inputs=None, owner_id=None):
    stamped=dict(result, input_signature=signature, criteria_signature=criteria_signature,
                 documents_signature=documents_signature,
                 generated_at=datetime.now(timezone.utc).isoformat())
    if inputs is not None: stamped['input_snapshot']=deepcopy(inputs)
    if owner_id is not None: stamped['owner_scope']=owner_scope(owner_id)
    return stamped


def is_stale(result, current_input, criteria_signature, documents_signature):
    return (result.get('input_signature') != current_input
            or result.get('criteria_signature') != criteria_signature
            or result.get('documents_signature') != documents_signature)


def consultation_context(result, department, year, current_input, criteria_signature, documents_signature, owner_id):
    """Prepare only the current account's selected diagnosis for conversation.

    Legacy results without owner_scope are allowed only because the caller loads
    them from its authenticated account's private profile store. They cannot
    provide input details that were never saved.
    """
    if not result or result.get('department')!=department or result.get('year')!=year:
        return None
    if result.get('owner_scope') and result['owner_scope']!=owner_scope(owner_id):
        return None
    context=deepcopy(result)
    context['_stale']=is_stale(result,current_input,criteria_signature,documents_signature)
    snapshot=context.get('input_snapshot')
    if snapshot:
        try:
            valid=(snapshot['department']==department and snapshot['year']==year and
                   input_signature(**snapshot)==result.get('input_signature'))
        except (KeyError,TypeError,ValueError): valid=False
        if not valid: context['_stale']=True
    context['_consultation_context']=True
    return context
