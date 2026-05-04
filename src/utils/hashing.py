from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel


def stable_model_hash(model: BaseModel) -> str:
    payload = model.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
