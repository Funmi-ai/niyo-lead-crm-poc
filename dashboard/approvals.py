"""Tiny local store for outreach approval/rejection decisions and edited
draft text, so the partnership manager's review choices persist across
dashboard reruns. Synthetic-data demo only — not a real approvals audit log."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

APPROVALS_PATH = Path(__file__).parent.parent / "data" / "approvals.json"


def load_approvals() -> dict:
    if APPROVALS_PATH.exists():
        return json.loads(APPROVALS_PATH.read_text())
    return {}


def save_approval(lead_id: str, status: str, edited_fields: dict | None = None) -> None:
    approvals = load_approvals()
    entry = approvals.get(lead_id, {})
    entry["status"] = status
    entry["decided_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    if edited_fields:
        entry.setdefault("edited_fields", {}).update(edited_fields)
    approvals[lead_id] = entry
    APPROVALS_PATH.parent.mkdir(exist_ok=True)
    APPROVALS_PATH.write_text(json.dumps(approvals, indent=2))


def reset_approvals() -> None:
    if APPROVALS_PATH.exists():
        APPROVALS_PATH.unlink()
