"""Automated tests for the qualification engine, dedupe and outreach gating,
checked against data/expected_results.json (generated alongside the
synthetic dataset — see generate_synthetic_data.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.core.validate import load_leads, validate_and_normalise
from src.core.dedupe import detect_duplicates
from src.core.qualification import score_lead, classify_pipeline
from src.outreach.generator import generate_outreach

DATA_DIR = ROOT / "data"


def _load():
    raw = load_leads(str(DATA_DIR / "leads.json"))
    leads, issues = validate_and_normalise(raw)
    return leads, issues


def _expected():
    return json.loads((DATA_DIR / "expected_results.json").read_text())


def test_dataset_has_fifty_leads():
    leads, _ = _load()
    assert len(leads) == 50


def test_duplicate_detection_matches_expected_pairs():
    leads, _ = _load()
    duplicates = detect_duplicates(leads)
    expected = _expected()["duplicate_pairs"]
    for dup_id, primary_id in expected.items():
        assert duplicates.get(dup_id) == primary_id, f"{dup_id} should map to {primary_id}, got {duplicates.get(dup_id)}"
    assert len(duplicates) == len(expected)


def test_do_not_contact_leads_are_excluded():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    for lead_id in _expected()["expected_do_not_contact"]:
        score = score_lead(by_id[lead_id])
        assert score.excluded_from_outreach
        assert score.exclusion_reason
        bundle = generate_outreach(by_id[lead_id], score)
        assert bundle is None, f"{lead_id} must not get outreach drafts"


def test_duplicates_are_excluded_from_outreach():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    duplicates = detect_duplicates(leads)
    for dup_id, primary_id in duplicates.items():
        score = score_lead(by_id[dup_id], is_duplicate=True, duplicate_of=primary_id)
        assert score.excluded_from_outreach
        bundle = generate_outreach(by_id[dup_id], score)
        assert bundle is None


def test_not_a_decision_maker_flagged_with_right_next_action():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    for lead_id in _expected()["expected_not_decision_maker"]:
        lead = by_id[lead_id]
        assert lead.decision_maker_status == "Not a decision-maker"
        score = score_lead(lead)
        if not score.excluded_from_outreach and not score.needs_human_review:
            assert "budget holder" in score.recommended_next_action.lower()


def test_needs_review_flags_present():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    for lead_id in _expected()["expected_needs_review_at_least"]:
        score = score_lead(by_id[lead_id])
        assert score.needs_human_review, f"{lead_id} expected needs_human_review=True"


def test_unclear_pipeline_leads_classified_unclear():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    for lead_id in _expected()["expected_unclear_pipeline"]:
        assert classify_pipeline(by_id[lead_id]) == "Unclear"


def test_scoring_is_deterministic_and_reproducible():
    leads, _ = _load()
    lead = leads[0]
    s1 = score_lead(lead)
    s2 = score_lead(lead)
    assert s1.overall_score == s2.overall_score
    assert s1.pipeline == s2.pipeline
    assert s1.recommended_next_action == s2.recommended_next_action


def test_score_bounds_always_0_to_100():
    leads, _ = _load()
    for lead in leads:
        score = score_lead(lead)
        assert 0 <= score.overall_score <= 100


def test_missing_critical_fields_flagged_not_fabricated():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    lead = by_id["LEAD-008"]  # no named contact, only a general inbox
    assert "Missing required field: contact_name" in sum(
        [validate_and_normalise([lead])[1].get(lead.lead_id, [])], []
    )


def test_outreach_never_claims_unknown_personalisation():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    lead = by_id["LEAD-036"]  # almost nothing known
    score = score_lead(lead)
    bundle = generate_outreach(lead, score)
    assert bundle is not None
    assert "RESEARCH NEEDED" in bundle.initial_email


def test_high_scoring_decision_maker_leads_get_prioritise_action():
    leads, _ = _load()
    by_id = {l.lead_id: l for l in leads}
    lead = by_id["LEAD-001"]  # strong ICP match, decision-maker, confirmed budget
    score = score_lead(lead)
    assert score.overall_score >= 70
    assert not score.needs_human_review
    assert "prioritise" in score.recommended_next_action.lower()
