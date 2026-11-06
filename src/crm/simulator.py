"""Local, HubSpot-shaped CRM simulation — no real HubSpot access, ever.

Every write here is explicitly a *simulated* action. Nothing in this module
talks to the internet or claims to have updated a real HubSpot account.
State persists to a local JSON file so the dashboard can read it back.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from .interface import CRMInterface

DEFAULT_STATE = {
    "companies": {},   # organisation_name -> company record
    "contacts": {},    # lead_id -> contact record
    "deals": {},       # lead_id -> deal record (pipeline + stage)
    "tasks": [],        # list of task dicts
    "activities": [],   # list of activity log dicts
    "duplicates": {},    # duplicate_lead_id -> primary_lead_id
    "last_run": None,
}

DEAL_STAGES_BY_SCORE = [
    (70, "Qualified — ready for outreach"),
    (40, "Nurture"),
    (0, "Low priority / monitor"),
]


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


class LocalCRMSimulator(CRMInterface):
    def __init__(self, state_path: str):
        self.state_path = Path(state_path)
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())
        else:
            self.state = json.loads(json.dumps(DEFAULT_STATE))

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def reset(self) -> None:
        self.state = json.loads(json.dumps(DEFAULT_STATE))
        self._save()

    def upsert_company(self, lead: dict) -> dict:
        name = lead.get("organisation_name") or f"Unknown ({lead['lead_id']})"
        record = self.state["companies"].get(name, {"created_at": _now()})
        record.update({
            "name": name,
            "organisation_type": lead.get("organisation_type"),
            "sector": lead.get("sector"),
            "organisation_size": lead.get("organisation_size"),
            "website": lead.get("website"),
            "location": lead.get("location"),
            "updated_at": _now(),
        })
        self.state["companies"][name] = record
        return record

    def upsert_contact(self, lead: dict) -> dict:
        record = self.state["contacts"].get(lead["lead_id"], {"created_at": _now()})
        record.update({
            "lead_id": lead["lead_id"],
            "name": lead.get("contact_name"),
            "job_title": lead.get("contact_job_title"),
            "email": lead.get("contact_email"),
            "organisation_name": lead.get("organisation_name"),
            "decision_maker_status": lead.get("decision_maker_status"),
            "consent_status": lead.get("consent_status"),
            "updated_at": _now(),
        })
        self.state["contacts"][lead["lead_id"]] = record
        return record

    def upsert_deal(self, lead: dict, score: dict) -> dict:
        stage = next(s for threshold, s in DEAL_STAGES_BY_SCORE if score["overall_score"] >= threshold)
        if score.get("excluded_from_outreach"):
            stage = "Excluded — " + (score.get("exclusion_reason") or "excluded")
        record = self.state["deals"].get(lead["lead_id"], {"created_at": _now()})
        record.update({
            "lead_id": lead["lead_id"],
            "organisation_name": lead.get("organisation_name"),
            "pipeline": score.get("pipeline"),
            "stage": stage,
            "score": score.get("overall_score"),
            "needs_human_review": score.get("needs_human_review"),
            "recommended_next_action": score.get("recommended_next_action"),
            "updated_at": _now(),
        })
        self.state["deals"][lead["lead_id"]] = record
        return record

    def create_task(self, lead_id: str, title: str, due_in_days: int) -> dict:
        task = {
            "task_id": f"TASK-{len(self.state['tasks']) + 1:04d}",
            "lead_id": lead_id,
            "title": title,
            "due_date": (datetime.utcnow() + timedelta(days=due_in_days)).date().isoformat(),
            "status": "Open",
            "created_at": _now(),
        }
        self.state["tasks"].append(task)
        return task

    def log_activity(self, lead_id: str, activity_type: str, detail: str) -> dict:
        activity = {
            "lead_id": lead_id,
            "activity_type": activity_type,
            "detail": detail,
            "timestamp": _now(),
        }
        self.state["activities"].append(activity)
        return activity

    def flag_duplicate(self, lead_id: str, primary_lead_id: str) -> dict:
        self.state["duplicates"][lead_id] = primary_lead_id
        return {"lead_id": lead_id, "primary_lead_id": primary_lead_id}

    def get_state(self) -> dict:
        return self.state

    def finish_run(self) -> None:
        self.state["last_run"] = _now()
        self._save()
