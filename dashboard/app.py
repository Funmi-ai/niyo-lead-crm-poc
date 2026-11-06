"""Niyo B2B Partnership Sales Automation — demo dashboard (Streamlit).

Run with: streamlit run dashboard/app.py
All data is synthetic. No live HubSpot connection. No outbound sends.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from run_workflow import run as run_workflow  # noqa: E402
from generate_synthetic_data import main as regenerate_synthetic_data  # noqa: E402
from dashboard.approvals import load_approvals, save_approval, reset_approvals  # noqa: E402
from src.outreach.sequencer import SequenceStore  # noqa: E402

DATA_DIR = ROOT / "data"
SEQUENCE_STATE_PATH = DATA_DIR / "sequence_state.json"

CADENCE_STEP_LABELS = {
    "initial_email": "Initial email",
    "followup_1": "Follow-up 1",
    "followup_2": "Follow-up 2",
}

# --- Palette (validated default categorical/status palette, see dataviz skill) ---
PIPELINE_COLORS = {
    "Private-sector": "#2a78d6",      # categorical slot 1 (blue)
    "Government-funded": "#1baf7a",   # categorical slot 3 (aqua)
    "Unclear": "#eb6834",             # categorical slot 2 (orange)
}
STATUS_GOOD = "#0ca30c"
STATUS_WARNING = "#fab219"
STATUS_SERIOUS = "#ec835a"
STATUS_CRITICAL = "#d03b3b"

st.set_page_config(page_title="Niyo Partnership Automation — Demo", layout="wide")


# ---------------------------------------------------------------------------
# Data loading (no caching — dataset is small and must reflect the latest run)
# ---------------------------------------------------------------------------

def _read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def load_all():
    processed = _read_json(DATA_DIR / "processed_leads.json", [])
    drafts = _read_json(DATA_DIR / "outreach_drafts.json", {})
    summary = _read_json(DATA_DIR / "run_summary.json", None)
    crm_state = _read_json(DATA_DIR / "crm_state.json", {})
    return processed, drafts, summary, crm_state


def leads_to_dataframe(processed: list[dict]) -> pd.DataFrame:
    rows = []
    for p in processed:
        s = p["score"]
        rows.append({
            "lead_id": p["lead_id"],
            "organisation_name": p["organisation_name"],
            "organisation_type": p["organisation_type"],
            "sector": p["sector"],
            "contact_name": p["contact_name"],
            "contact_job_title": p["contact_job_title"],
            "pipeline": s["pipeline"],
            "score": s["overall_score"],
            "needs_review": s["needs_human_review"],
            "excluded": s["excluded_from_outreach"],
            "is_duplicate": s["is_duplicate"],
            "duplicate_of": s.get("duplicate_of") or "",
            "next_action": s["recommended_next_action"],
            "missing_information": ", ".join(s["missing_information"]),
            "decision_maker_status": p["decision_maker_status"],
            "budget_status": p["budget_status"],
            "consent_status": p["consent_status"],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sidebar — demo controls
# ---------------------------------------------------------------------------

st.sidebar.title("Demo controls")
st.sidebar.caption("Synthetic data only. No live HubSpot connection. No outbound sends.")

if st.sidebar.button("Import example data", width="stretch"):
    regenerate_synthetic_data()
    st.sidebar.success("50 example leads (re)generated into data/leads.csv + leads.json")

if st.sidebar.button("Run the automation", type="primary", width="stretch"):
    with st.spinner("Running import → validate → dedupe → classify → score → outreach → CRM sync..."):
        summary = run_workflow(str(DATA_DIR / "leads.csv"), reset_crm=False)
    st.sidebar.success(
        f"Done in {summary['measured']['software_processing_time_seconds']}s — "
        f"{summary['measured']['outreach_drafts_generated']} drafts generated"
    )

if st.sidebar.button("Reset demonstration", width="stretch"):
    for f in ["processed_leads.json", "outreach_drafts.json", "crm_state.json", "run_summary.json", "sequence_state.json"]:
        p = DATA_DIR / f
        if p.exists():
            p.unlink()
    reset_approvals()
    st.sidebar.success("Demo reset. Click 'Import example data' then 'Run the automation' to start again.")

st.sidebar.divider()
st.sidebar.caption("Export processed results")
processed_preload, drafts_preload, _, crm_state_preload = load_all()
if processed_preload:
    st.sidebar.download_button("Download processed leads (JSON)",
                                json.dumps(processed_preload, indent=2),
                                file_name="niyo_processed_leads.json", width="stretch")
    st.sidebar.download_button("Download outreach drafts (JSON)",
                                json.dumps(drafts_preload, indent=2),
                                file_name="niyo_outreach_drafts.json", width="stretch")
    st.sidebar.download_button("Download CRM state (JSON)",
                                json.dumps(crm_state_preload, indent=2),
                                file_name="niyo_crm_state.json", width="stretch")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

st.title("Niyo B2B Partnership Sales Automation — Proof of Concept")
st.caption(
    "Synthetic demo data · provisional ICP/scoring rules (see ASSUMPTIONS.md) · "
    "no live HubSpot connection · no automated sending"
)

processed, drafts, summary, crm_state = load_all()

if not processed or not summary:
    st.info("No run yet. Use the sidebar: **Import example data**, then **Run the automation**.")
    st.stop()

df = leads_to_dataframe(processed)
sequencer = SequenceStore(str(SEQUENCE_STATE_PATH))

tab_overview, tab_leads, tab_outreach, tab_followup, tab_crm = st.tabs(
    ["Overview", "Lead management", "Outreach workspace", "Follow-up queue", "CRM activity"]
)

# --- Overview ---------------------------------------------------------------
with tab_overview:
    measured = summary["measured"]
    estimated = summary["estimated_not_measured"]

    st.warning(
        "**Open questions, by design:** scoring rules are provisional (not yet confirmed by Niyo), "
        "duplicate detection is a heuristic, and there's no production data-security review yet. "
        "Full list in `ASSUMPTIONS.md` — flagged here rather than left for you to find.",
        icon="⚠️",
    )

    st.subheader("What the software actually did (measured)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leads imported", measured["total_leads_imported"])
    c2.metric("Duplicates detected", measured["duplicates_detected"])
    c3.metric("High-priority opportunities", measured["high_priority_leads"])
    c4.metric("Leads needing review", measured["leads_needing_human_review"])

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Outreach drafts generated", measured["outreach_drafts_generated"])
    c6.metric("CRM tasks created", measured["crm_tasks_created"])
    c7.metric("CRM activities logged", measured["crm_activities_logged"])
    c8.metric("Software processing time", f"{measured['software_processing_time_seconds']}s")

    st.divider()
    left, right = st.columns([1, 1])

    with left:
        st.markdown("**Pipeline breakdown**")
        pipeline_df = pd.DataFrame(
            [{"pipeline": k, "count": v} for k, v in measured["pipeline_breakdown"].items()]
        )
        chart = (
            alt.Chart(pipeline_df)
            .mark_bar(size=34, cornerRadiusEnd=4)
            .encode(
                y=alt.Y("pipeline:N", sort="-x", title=None),
                x=alt.X("count:Q", title="Leads"),
                color=alt.Color(
                    "pipeline:N",
                    scale=alt.Scale(domain=list(PIPELINE_COLORS.keys()), range=list(PIPELINE_COLORS.values())),
                    legend=None,
                ),
                tooltip=["pipeline", "count"],
            )
            .properties(height=160)
        )
        text = chart.mark_text(align="left", dx=4).encode(text="count:Q", color=alt.value("#52514e"))
        st.altair_chart(chart + text, width="stretch")

    with right:
        st.markdown("**⚠️ Estimated time saved — assumption, not a measured result**")
        st.metric("Estimated manual hours this batch would have taken",
                   f"{estimated['estimated_manual_hours_total']} hrs")
        st.caption(
            f"Basis: {estimated['manual_minutes_per_lead_assumed']} manual minutes/lead × "
            f"{estimated['leads_this_applies_to']} unique leads. Editable in "
            f"`src/core/rules_config.py` → `MANUAL_MINUTES_PER_LEAD`."
        )
        with st.expander("Minute-by-minute assumption breakdown"):
            for k, v in estimated["minutes_breakdown"].items():
                st.write(f"- {k.replace('_', ' ')}: {v} min")
        st.caption(estimated["disclaimer"])

    st.divider()
    st.subheader("Before vs. after")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**Before — manual**")
        st.markdown(
            "- Reviews incoming leads one by one\n"
            "- Checks organisational fit by eye\n"
            "- Decides pipeline placement\n"
            "- Identifies likely decision-makers\n"
            "- Drafts outreach from scratch\n"
            "- Schedules follow-ups manually\n"
            "- Updates HubSpot by hand"
        )
    with b2:
        st.markdown("**After — automated, manager still approves**")
        st.markdown(
            "- Software imports, validates, dedupes\n"
            "- Pipeline + score computed with visible reasoning\n"
            "- Decision-maker gaps flagged automatically\n"
            "- Outreach drafts prepared, not sent\n"
            "- Follow-up tasks proposed with due dates\n"
            "- CRM record updates simulated, ready to sync\n"
            "- **Manager reviews, edits, approves or rejects everything**"
        )

# --- Lead management ---------------------------------------------------------
with tab_leads:
    st.subheader("Leads")
    f1, f2, f3, f4 = st.columns([2, 2, 2, 3])
    pipeline_filter = f1.multiselect("Pipeline", sorted(df["pipeline"].unique()), default=list(df["pipeline"].unique()))
    score_range = f2.slider("Fit score", 0, 100, (0, 100))
    review_only = f3.checkbox("Needs review only")
    search = f4.text_input("Search organisation or contact")

    filtered = df[df["pipeline"].isin(pipeline_filter)]
    filtered = filtered[(filtered["score"] >= score_range[0]) & (filtered["score"] <= score_range[1])]
    if review_only:
        filtered = filtered[filtered["needs_review"]]
    if search:
        s = search.lower()
        filtered = filtered[
            filtered["organisation_name"].str.lower().str.contains(s)
            | filtered["contact_name"].str.lower().str.contains(s)
        ]

    st.caption(f"{len(filtered)} of {len(df)} leads shown")
    st.dataframe(
        filtered[["lead_id", "organisation_name", "pipeline", "score", "decision_maker_status",
                  "budget_status", "needs_review", "excluded", "is_duplicate", "next_action"]],
        width="stretch", hide_index=True, height=320,
    )

    st.divider()
    st.subheader("Lead detail")
    lead_id = st.selectbox("Select a lead", filtered["lead_id"].tolist() if len(filtered) else df["lead_id"].tolist())
    lead_record = next(p for p in processed if p["lead_id"] == lead_id)
    score = lead_record["score"]

    dcol1, dcol2 = st.columns([1, 1])
    with dcol1:
        st.markdown(f"### {lead_record['organisation_name'] or 'Unknown organisation'}")
        st.write(f"**Contact:** {lead_record['contact_name'] or 'Unknown'} — {lead_record['contact_job_title'] or 'Unknown title'}")
        st.write(f"**Pipeline:** {score['pipeline']}  |  **Score:** {score['overall_score']}/100")
        if score["excluded_from_outreach"]:
            st.error(f"🔴 Excluded from outreach — {score['exclusion_reason']}")
        elif score["needs_human_review"]:
            st.warning("🟡 Needs human review before outreach")
        else:
            st.success("🟢 Clear to proceed per current rules")
        st.write(f"**Recommended next action:** {score['recommended_next_action']}")
        if score["missing_information"]:
            st.write(f"**Missing information:** {', '.join(score['missing_information'])}")
        if lead_record.get("notes"):
            st.write(f"**Notes on file:** {lead_record['notes']}")

    with dcol2:
        st.markdown("**Scoring reasoning (explainable, reproducible)**")
        for factor in score["factors"]:
            st.write(f"`{factor['points']:+d}` {factor['factor']} — {factor['reason']}")
        if score["reasons"]:
            st.markdown("**Flags**")
            for r in score["reasons"]:
                st.write(f"- {r}")

# --- Outreach workspace -------------------------------------------------------
with tab_outreach:
    st.subheader("Outreach workspace")
    st.caption("Nothing here is sent automatically. Edit freely, then approve or reject each lead's sequence.")

    approvals = load_approvals()
    outreach_leads = [p for p in processed if p["lead_id"] in drafts]
    status_filter = st.radio("Show", ["All", "Pending", "Approved", "Rejected"], horizontal=True)

    for lead_record in outreach_leads:
        lead_id = lead_record["lead_id"]
        current_status = approvals.get(lead_id, {}).get("status", "Pending")
        if status_filter != "All" and current_status != status_filter:
            continue

        bundle = drafts[lead_id]
        badge = {"Pending": "🟡", "Approved": "🟢", "Rejected": "🔴"}[current_status]
        with st.expander(
            f"{badge} {lead_record['organisation_name']} — {lead_record['contact_name']} "
            f"({lead_record['score']['pipeline']}, score {lead_record['score']['overall_score']}) — {current_status}"
        ):
            st.markdown("**Internal briefing**")
            st.code(bundle["internal_briefing"], language=None)

            st.markdown("**Initial outreach email**")
            st.code(bundle["initial_email"], language=None)

            st.markdown("**Follow-up 1**")
            st.code(bundle["followup_1"], language=None)

            st.markdown("**Follow-up 2**")
            st.code(bundle["followup_2"], language=None)

            st.markdown("**LinkedIn message**")
            st.code(bundle["linkedin_message"], language=None)

            bcol1, bcol2, bcol3 = st.columns(3)
            if bcol1.button("✅ Approve", key=f"approve_{lead_id}"):
                save_approval(lead_id, "Approved")
                sequencer.enroll(lead_id, lead_record["organisation_name"])
                st.rerun()
            if bcol2.button("❌ Reject", key=f"reject_{lead_id}"):
                save_approval(lead_id, "Rejected")
                if sequencer.is_enrolled(lead_id):
                    sequencer.log_reply(lead_id, "Rejected after enrollment")
                st.rerun()
            if bcol3.button("↩️ Reset to pending", key=f"pending_{lead_id}"):
                save_approval(lead_id, "Pending")
                sequencer.unenroll(lead_id)
                st.rerun()

            if sequencer.is_enrolled(lead_id):
                seq_record = sequencer.get(lead_id)
                st.caption(
                    f"📨 Follow-up status: {seq_record['status']}"
                    + (f" — next due {seq_record['next_due_on']}" if seq_record.get("next_due_on") else "")
                )

# --- Follow-up queue -------------------------------------------------------
with tab_followup:
    st.subheader("Follow-up queue")
    st.caption(
        "This is the layer on top of classification: once a lead's outreach is approved, it "
        "enters a cadence. This queue shows exactly who needs a touch *today*, with the next "
        "message already written — no one has to remember where each lead was left."
    )

    clock_col1, clock_col2, clock_col3, clock_col4 = st.columns([2, 1, 1, 1])
    clock_col1.markdown(f"**Demo date:** {sequencer.today().isoformat()}")
    clock_col1.caption(
        "A virtual clock for this demo only — production would run on a real scheduler "
        "(timezone- and weekend-aware), not a button."
    )
    if clock_col2.button("+1 day"):
        sequencer.advance_clock(1)
        st.rerun()
    if clock_col3.button("+4 days"):
        sequencer.advance_clock(4)
        st.rerun()
    if clock_col4.button("Reset clock"):
        sequencer.reset_clock()
        st.rerun()

    st.divider()

    due = sequencer.due_today()
    st.markdown(f"### 🔔 Due today ({len(due)})")

    if not due:
        st.info("Nothing due today. Approve more leads in Outreach workspace, or advance the demo clock.")

    for record in due:
        lead_id = record["lead_id"]
        bundle = drafts.get(lead_id)
        step_label = CADENCE_STEP_LABELS.get(record["current_step"], record["current_step"])
        with st.expander(f"📨 {record['organisation_name']} — {step_label} due {record['next_due_on']}", expanded=True):
            if bundle:
                st.code(bundle.get(record["current_step"], "(draft not found)"), language=None)
            fcol1, fcol2 = st.columns(2)
            if fcol1.button("✅ Mark as sent", key=f"sent_{lead_id}"):
                sequencer.mark_sent(lead_id)
                st.rerun()
            if fcol2.button("💬 Log a reply (stop sequence)", key=f"reply_{lead_id}"):
                sequencer.log_reply(lead_id, "Replied")
                st.rerun()

    st.divider()
    st.markdown("### All enrolled leads")
    all_records = sequencer.all_records()
    if all_records:
        seq_df = pd.DataFrame(all_records)
        seq_df["current_step"] = seq_df["current_step"].map(lambda s: CADENCE_STEP_LABELS.get(s, s or "—"))
        st.dataframe(
            seq_df[["organisation_name", "status", "current_step", "last_sent_on", "next_due_on", "reply_status"]],
            width="stretch", hide_index=True, height=260,
        )
    else:
        st.caption("No leads enrolled yet — approve outreach in the Outreach workspace tab to enroll them.")

# --- CRM activity --------------------------------------------------------------
with tab_crm:
    st.subheader("Simulated CRM activity (local — not a real HubSpot connection)")

    ccol1, ccol2 = st.columns(2)
    with ccol1:
        st.markdown("**Deals / pipeline stages**")
        deals_df = pd.DataFrame(list(crm_state.get("deals", {}).values()))
        if not deals_df.empty:
            st.dataframe(deals_df[["organisation_name", "pipeline", "stage", "score"]],
                         width="stretch", hide_index=True, height=260)

    with ccol2:
        st.markdown("**Open tasks**")
        tasks_df = pd.DataFrame(crm_state.get("tasks", []))
        if not tasks_df.empty:
            st.dataframe(tasks_df[["lead_id", "title", "due_date", "status"]],
                         width="stretch", hide_index=True, height=260)

    st.markdown("**Activity log**")
    activities_df = pd.DataFrame(crm_state.get("activities", []))
    if not activities_df.empty:
        st.dataframe(activities_df.sort_values("timestamp", ascending=False),
                     width="stretch", hide_index=True, height=300)

    st.divider()
    st.caption(
        "This is a local JSON-backed simulation of HubSpot-style objects (contacts, "
        "companies, deals, tasks, activity). See HUBSPOT_INTEGRATION_PLAN.md for what "
        "a real HubSpot connection would require."
    )
