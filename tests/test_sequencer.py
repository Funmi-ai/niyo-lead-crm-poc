"""Tests for the follow-up sequencing layer (src/outreach/sequencer.py)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.outreach.sequencer import SequenceStore


def _store(tmp_path) -> SequenceStore:
    return SequenceStore(str(tmp_path / "sequence_state.json"))


def test_enroll_is_ready_to_send_today(tmp_path):
    store = _store(tmp_path)
    record = store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    assert record["status"] == "Ready to send"
    assert record["current_step"] == "initial_email"
    assert record["next_due_on"] == store.today().isoformat()


def test_enroll_is_idempotent(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store.mark_sent("LEAD-001")
    before = store.get("LEAD-001")
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")  # should not reset progress
    after = store.get("LEAD-001")
    assert before == after


def test_due_today_includes_freshly_enrolled_lead(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    due = store.due_today()
    assert len(due) == 1
    assert due[0]["lead_id"] == "LEAD-001"


def test_mark_sent_advances_step_and_schedules_next(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store.mark_sent("LEAD-001")
    record = store.get("LEAD-001")
    assert record["current_step"] == "followup_1"
    assert record["status"] == "Waiting"
    assert record["next_due_on"] > store.today().isoformat()
    # not due yet — the cadence gap hasn't elapsed
    assert store.due_today() == []


def test_advancing_clock_surfaces_the_next_due_step(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store.mark_sent("LEAD-001")  # now waiting for followup_1, due in 4 days
    store.advance_clock(4)
    due = store.due_today()
    assert len(due) == 1
    assert due[0]["current_step"] == "followup_1"


def test_full_cadence_completes_after_final_step(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store.mark_sent("LEAD-001")  # -> followup_1
    store.advance_clock(10)
    store.mark_sent("LEAD-001")  # -> followup_2
    store.advance_clock(10)
    store.mark_sent("LEAD-001")  # -> sequence complete
    record = store.get("LEAD-001")
    assert record["status"] == "Sequence complete"
    assert record["current_step"] is None
    assert store.due_today() == []


def test_reply_stops_the_sequence(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store.log_reply("LEAD-001", "Replied")
    record = store.get("LEAD-001")
    assert record["status"] == "Stopped — Replied"
    assert record["reply_status"] == "Replied"
    assert store.due_today() == []


def test_unenroll_removes_the_lead(tmp_path):
    store = _store(tmp_path)
    store.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store.unenroll("LEAD-001")
    assert store.get("LEAD-001") is None
    assert not store.is_enrolled("LEAD-001")


def test_state_persists_across_instances(tmp_path):
    path = tmp_path / "sequence_state.json"
    store1 = SequenceStore(str(path))
    store1.enroll("LEAD-001", "Castlemere Logistics Ltd")
    store2 = SequenceStore(str(path))
    assert store2.is_enrolled("LEAD-001")
