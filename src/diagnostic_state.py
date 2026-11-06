"""Result provenance and deterministic input signatures; saved records are owned by the separate account store."""
from datetime import datetime, timezone
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


def stamp_result(result, signature, criteria_signature, documents_signature):
    return dict(result, input_signature=signature, criteria_signature=criteria_signature,
                documents_signature=documents_signature,
                generated_at=datetime.now(timezone.utc).isoformat())


def is_stale(result, current_input, criteria_signature, documents_signature):
    return (result.get('input_signature') != current_input
            or result.get('criteria_signature') != criteria_signature
            or result.get('documents_signature') != documents_signature)
