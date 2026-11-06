#!/usr/bin/env python3
"""
End-to-end workflow orchestrator — this IS the automation being demoed.

Steps (per the project brief):
  1. Import raw leads (CSV/JSON)
  2. Validate and normalise
  3. Detect duplicates
  4. Classify into government-funded / private-sector pipelines
  5. Score against configurable ICP/eligibility rules
  6. Generate outreach drafts (skipped for excluded/duplicate leads)
  7. Simulate CRM updates (contacts, companies, deals, tasks, activity log)
  8. Write processed outputs + a run summary (measured time + time-saved
     estimate, clearly separated)

Run: python3 run_workflow.py [--leads data/leads.csv] [--reset-crm]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from src.core.validate import load_leads, validate_and_normalise
from src.core.dedupe import detect_duplicates
from src.core.qualification import score_lead
from src.core.rules_config import MANUAL_MINUTES_PER_LEAD
from src.outreach.generator import generate_outreach
from src.crm.simulator import LocalCRMSimulator

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CRM_STATE_PATH = DATA_DIR / "crm_state.json"


def run(leads_path: str, reset_crm: bool = False) -> dict:
    t0 = time.perf_counter()

    raw_leads = load_leads(leads_path)
    leads, validation_issues = validate_and_normalise(raw_leads)

    duplicates = detect_duplicates(leads)

    crm = LocalCRMSimulator(str(CRM_STATE_PATH))
    if reset_crm:
        crm.reset()

    processed = []
    outreach_drafts = {}

    for lead in leads:
        dup_of = duplicates.get(lead.lead_id)
        score = score_lead(lead, is_duplicate=lead.lead_id in duplicates, duplicate_of=dup_of)

        lead_dict = lead.to_dict()
        lead_dict["validation_issues"] = validation_issues.get(lead.lead_id, [])

        # --- CRM simulation ---
        crm.upsert_company(lead_dict)
        crm.upsert_contact(lead_dict)
        crm.upsert_deal(lead_dict, score.to_dict())

        if score.is_duplicate:
            crm.flag_duplicate(lead.lead_id, score.duplicate_of)
            crm.log_activity(lead.lead_id, "Duplicate detected",
                              f"Matched to {score.duplicate_of}; excluded from outreach")
        elif score.excluded_from_outreach:
            crm.log_activity(lead.lead_id, "Excluded", score.exclusion_reason or "Excluded from outreach")
        else:
            crm.log_activity(lead.lead_id, "Scored",
                              f"{score.pipeline}, {score.overall_score}/100 — {score.recommended_next_action}")

        bundle = generate_outreach(lead, score)
        if bundle is not None:
            outreach_drafts[lead.lead_id] = bundle.to_dict()
            crm.log_activity(lead.lead_id, "Outreach drafted", "Initial email + 2 follow-ups + briefing generated")
            if score.overall_score >= 70 and not score.needs_human_review:
                crm.create_task(lead.lead_id, f"Review & approve outreach for {lead.organisation_name}", due_in_days=2)
            elif score.needs_human_review:
                crm.create_task(lead.lead_id, f"Research/qualify {lead.organisation_name} before outreach", due_in_days=3)

        processed.append({**lead_dict, "score": score.to_dict()})

    crm.finish_run()

    elapsed_seconds = time.perf_counter() - t0

    summary = build_summary(processed, outreach_drafts, elapsed_seconds, crm.get_state())

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "processed_leads.json").write_text(json.dumps(processed, indent=2))
    (DATA_DIR / "outreach_drafts.json").write_text(json.dumps(outreach_drafts, indent=2))
    (DATA_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2))

    return summary


def build_summary(processed: list[dict], outreach_drafts: dict, elapsed_seconds: float, crm_state: dict) -> dict:
    total = len(processed)
    duplicates = [p for p in processed if p["score"]["is_duplicate"]]
    excluded = [p for p in processed if p["score"]["excluded_from_outreach"] and not p["score"]["is_duplicate"]]
    needs_review = [p for p in processed if p["score"]["needs_human_review"]]
    pipeline_counts: dict[str, int] = {}
    for p in processed:
        pipeline_counts[p["score"]["pipeline"]] = pipeline_counts.get(p["score"]["pipeline"], 0) + 1

    high_priority = [
        p for p in processed
        if p["score"]["overall_score"] >= 70 and not p["score"]["excluded_from_outreach"]
    ]

    billable_leads = total - len(duplicates)  # leads actually worked, excluding pure dupes
    manual_minutes_per_lead_total = sum(MANUAL_MINUTES_PER_LEAD.values())
    estimated_manual_minutes = billable_leads * manual_minutes_per_lead_total

    return {
        "measured": {
            "total_leads_imported": total,
            "unique_leads": total - len(duplicates),
            "duplicates_detected": len(duplicates),
            "leads_excluded_from_outreach": len(excluded),
            "leads_needing_human_review": len(needs_review),
            "pipeline_breakdown": pipeline_counts,
            "high_priority_leads": len(high_priority),
            "outreach_drafts_generated": len(outreach_drafts),
            "crm_tasks_created": len(crm_state.get("tasks", [])),
            "crm_activities_logged": len(crm_state.get("activities", [])),
            "software_processing_time_seconds": round(elapsed_seconds, 3),
        },
        "estimated_not_measured": {
            "assumption_basis": "Editable manual-effort assumptions in src/core/rules_config.py MANUAL_MINUTES_PER_LEAD",
            "manual_minutes_per_lead_assumed": manual_minutes_per_lead_total,
            "minutes_breakdown": MANUAL_MINUTES_PER_LEAD,
            "leads_this_applies_to": billable_leads,
            "estimated_manual_minutes_total": estimated_manual_minutes,
            "estimated_manual_hours_total": round(estimated_manual_minutes / 60, 1),
            "disclaimer": (
                "This is an editable assumption about manual effort, not a measured "
                "result, and makes no claim about conversion-rate or revenue impact."
            ),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Niyo B2B lead-automation workflow")
    parser.add_argument("--leads", default=str(DATA_DIR / "leads.csv"))
    parser.add_argument("--reset-crm", action="store_true")
    args = parser.parse_args()

    result = run(args.leads, reset_crm=args.reset_crm)
    print(json.dumps(result, indent=2))
