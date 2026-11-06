"""Follow-up sequencing layer — this is the layer that makes outreach less
laborious, on top of classification/scoring.

Scoring + drafting (qualification.py / generator.py) answer "is this lead
worth contacting, and what should we say". This module answers the question
that actually eats the partnership manager's time day-to-day: "who needs a
follow-up *today*, and what do I say this time".

State is a small local JSON file (data/sequence_state.json) tracking, per
enrolled lead: which cadence step it's on, when it was last sent, when the
next step falls due, and whether it stopped (replied / rejected / done).

A lead enters the sequence only when its outreach is approved in the
dashboard — this stays entirely under the partnership manager's control,
same as outreach drafting. Nothing here sends anything; "mark as sent" is
a manual confirmation that the manager actually sent it (e.g. from their
own inbox or Apollo), not an automated send.

DEMO CLOCK: because a live demo can't wait real days to show a cadence
advancing, this module keeps its own virtual "today" (clock_date) that only
moves when the dashboard's "Advance day" control is used. Real timestamps
elsewhere (CRM activity log, etc.) are unaffected — this clock only drives
sequencing logic.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from ..core import rules_config as cfg

DEFAULT_STATE = {
    "clock_date": None,  # set to real today on first use
    "leads": {},  # lead_id -> sequence record
}

ACTIVE_STATUSES = {"Ready to send", "Waiting"}


class SequenceStore:
    def __init__(self, state_path: str):
        self.state_path = Path(state_path)
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())
        else:
            self.state = json.loads(json.dumps(DEFAULT_STATE))
        if not self.state.get("clock_date"):
            self.state["clock_date"] = date.today().isoformat()
            self._save()

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2))

    # --- clock ---------------------------------------------------------

    def today(self) -> date:
        return date.fromisoformat(self.state["clock_date"])

    def advance_clock(self, days: int = 1) -> date:
        new_date = self.today() + timedelta(days=days)
        self.state["clock_date"] = new_date.isoformat()
        self._save()
        return new_date

    def reset_clock(self) -> date:
        self.state["clock_date"] = date.today().isoformat()
        self._save()
        return self.today()

    # --- enrollment ------------------------------------------------------

    def is_enrolled(self, lead_id: str) -> bool:
        return lead_id in self.state["leads"]

    def enroll(self, lead_id: str, organisation_name: str) -> dict:
        """Enroll a lead in the cadence, ready to send step 0 today."""
        if lead_id in self.state["leads"]:
            return self.state["leads"][lead_id]
        record = {
            "lead_id": lead_id,
            "organisation_name": organisation_name,
            "step_index": 0,
            "current_step": cfg.CADENCE_STEPS[0],
            "status": "Ready to send",
            "enrolled_on": self.today().isoformat(),
            "last_sent_on": None,
            "next_due_on": self.today().isoformat(),
            "reply_status": None,
            "history": [],
        }
        self.state["leads"][lead_id] = record
        self._save()
        return record

    def unenroll(self, lead_id: str) -> None:
        self.state["leads"].pop(lead_id, None)
        self._save()

    # --- progressing the cadence -----------------------------------------

    def mark_sent(self, lead_id: str) -> dict:
        """Record that the current step was actually sent (by the manager,
        from their own inbox/Apollo), and schedule the next step."""
        record = self.state["leads"][lead_id]
        step = record["current_step"]
        today = self.today().isoformat()

        record["history"].append({"step": step, "sent_on": today})
        record["last_sent_on"] = today

        next_index = record["step_index"] + 1
        if next_index < len(cfg.CADENCE_STEPS):
            next_step = cfg.CADENCE_STEPS[next_index]
            gap = cfg.CADENCE_GAP_DAYS.get(next_step, 4)
            record["step_index"] = next_index
            record["current_step"] = next_step
            record["status"] = "Waiting"
            record["next_due_on"] = (self.today() + timedelta(days=gap)).isoformat()
        else:
            record["status"] = "Sequence complete"
            record["current_step"] = None
            record["next_due_on"] = None

        self._save()
        return record

    def log_reply(self, lead_id: str, outcome: str = "Replied") -> dict:
        """Stop the sequence because the lead replied (or should be stopped
        for another reason, e.g. 'Not interested')."""
        record = self.state["leads"][lead_id]
        record["status"] = f"Stopped — {outcome}"
        record["reply_status"] = outcome
        record["next_due_on"] = None
        self._save()
        return record

    # --- queries -----------------------------------------------------------

    def due_today(self) -> list[dict]:
        today = self.today()
        due = []
        for record in self.state["leads"].values():
            if record["status"] not in ACTIVE_STATUSES:
                continue
            if record["next_due_on"] and date.fromisoformat(record["next_due_on"]) <= today:
                due.append(record)
        return sorted(due, key=lambda r: r["next_due_on"])

    def all_records(self) -> list[dict]:
        return list(self.state["leads"].values())

    def get(self, lead_id: str) -> dict | None:
        return self.state["leads"].get(lead_id)
