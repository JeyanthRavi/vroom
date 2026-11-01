"""Staging-only local model registry; promotion is always a human action."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ALLOWED_STATUS = {"staging", "rejected", "archived"}


def register(path: Path, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Append a staging entry; this function cannot create production status."""

    status = entry.get("status", "staging")
    if status not in ALLOWED_STATUS:
        raise ValueError("automatic registry status must be staging, rejected, or archived")
    records: List[Dict[str, Any]] = []
    if path.exists():
        records = json.loads(path.read_text())
        if not isinstance(records, list):
            raise ValueError("model registry must be a JSON list")
    record = dict(entry)
    record["status"] = status
    records.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
    return records
