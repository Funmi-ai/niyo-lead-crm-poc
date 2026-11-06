"""Step 8-ish of the workflow: outreach drafting.

Default mode is fully deterministic templating — no API key required, so
the demo always runs. If ANTHROPIC_API_KEY is set in the environment, the
engine can optionally hand the same structured brief to an LLM for more
natural phrasing (see llm_adapter.py) — but it never fabricates facts about
the recipient, their company, or Niyo's services that aren't present on the
lead record or in niyo.co (Niyo's public website).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict

from ..core.models import Lead, ScoreResult

RESEARCH_PLACEHOLDER = "[RESEARCH NEEDED — not enough verified information to personalise this further]"

# Niyo's own terminology, drawn only from niyo.co (Niyo's public website).
PIPELINE_OFFER_LANGUAGE = {
    "Private-sector": {
        "programme_name": "a Niyo workforce upskilling academy (or a sponsored AI accelerator seat)",
        "value_prop": "a practical way to upskill your team on Niyo Learn, with attendance and outcome evidence in one place, plus early access to hire from Niyo's cohorts at Demo & Hire",
        "proof": "Niyo already works this way with partners like KPMG, Goldman Sachs and HSBC",
    },
    "Government-funded": {
        "programme_name": "a commissioned Niyo programme (e.g. She Builds, the SME sprint, or a bespoke accelerator cohort)",
        "value_prop": "a funded route to AI/digital skills, youth employment or inclusive-growth outcomes, reported live against Niyo's impact dashboard and mapped to PPN 002 / the Social Value Model",
        "proof": "Niyo's WMCA-backed work won an Innovative Delivery Award, with 600 women enrolled and 61 into new jobs",
    },
    "Unclear": {
        "programme_name": "the right Niyo programme once we understand your priorities",
        "value_prop": "Niyo's AI/digital skills accelerators and workforce programmes",
        "proof": "Niyo's public case studies",
    },
}


@dataclass
class OutreachBundle:
    lead_id: str
    mode: str  # "template" or "llm"
    initial_email: str
    followup_1: str
    followup_2: str
    linkedin_message: str
    internal_briefing: str

    def to_dict(self) -> dict:
        return asdict(self)


def _offer(pipeline: str) -> dict:
    return PIPELINE_OFFER_LANGUAGE.get(pipeline, PIPELINE_OFFER_LANGUAGE["Unclear"])


def _known(value: str) -> bool:
    return bool(value) and value.lower() not in ("unknown", "")


def _initial_email(lead: Lead, score: ScoreResult) -> str:
    offer = _offer(score.pipeline)
    first_name = lead.contact_name.split()[0] if lead.contact_name else "there"
    programme_line = (
        f"I noticed {lead.organisation_name} might be a fit for {offer['programme_name']}"
        if _known(lead.organisation_name) else
        f"I think your organisation might be a fit for {offer['programme_name']}"
    )
    interest_line = (
        f" — your note on {lead.partnership_interest.lower()} is what prompted me to reach out."
        if _known(lead.partnership_interest) else f" {RESEARCH_PLACEHOLDER}"
    )
    return (
        f"Subject: Niyo — {offer['programme_name'].split('(')[0].strip()}\n\n"
        f"Hi {first_name},\n\n"
        f"{programme_line}{interest_line}\n\n"
        f"In short, it's {offer['value_prop']}. {offer['proof']}.\n\n"
        f"Would it be useful to have a short call to see whether this lines up with what "
        f"{lead.organisation_name or 'your team'} is trying to do"
        f"{' with ' + lead.relevant_programme if _known(lead.relevant_programme) else ''}?\n\n"
        f"Best,\nNiyo Partnerships Team"
    )


def _followup_1(lead: Lead, score: ScoreResult) -> str:
    first_name = lead.contact_name.split()[0] if lead.contact_name else "there"
    return (
        f"Subject: Re: Niyo partnership — following up\n\n"
        f"Hi {first_name},\n\n"
        f"Just making sure my last note didn't get buried. "
        f"{'Given ' + lead.partnership_interest + ', I thought this was worth a second look.' if _known(lead.partnership_interest) else RESEARCH_PLACEHOLDER}\n\n"
        f"Happy to send a one-pager instead of a call if that's easier — whichever works for you.\n\n"
        f"Best,\nNiyo Partnerships Team"
    )


def _followup_2(lead: Lead, score: ScoreResult) -> str:
    first_name = lead.contact_name.split()[0] if lead.contact_name else "there"
    return (
        f"Subject: Re: Niyo partnership — one more try\n\n"
        f"Hi {first_name},\n\n"
        f"I'll leave this here for now — if {lead.organisation_name or 'this'} isn't the right fit at the moment, "
        f"no problem at all. If priorities shift, my door's open.\n\n"
        f"Best,\nNiyo Partnerships Team"
    )


def _linkedin_message(lead: Lead, score: ScoreResult) -> str | None:
    if score.pipeline == "Unclear" or not _known(lead.contact_job_title):
        return None
    offer = _offer(score.pipeline)
    return (
        f"Hi {lead.contact_name.split()[0] if lead.contact_name else ''} — I work in partnerships at Niyo. "
        f"Given your role as {lead.contact_job_title} at {lead.organisation_name or 'your organisation'}, "
        f"thought {offer['programme_name']} might be relevant. Open to a quick chat?"
    )


def _internal_briefing(lead: Lead, score: ScoreResult) -> str:
    lines = [
        f"INTERNAL BRIEFING — {lead.organisation_name or 'Unknown organisation'} ({lead.lead_id})",
        f"Pipeline: {score.pipeline}  |  Score: {score.overall_score}/100  |  Needs review: {score.needs_human_review}",
        f"Contact: {lead.contact_name or 'Unknown'} — {lead.contact_job_title or 'Unknown title'} "
        f"({lead.decision_maker_status})",
        f"Lead source: {lead.lead_source}  |  Relationship: {lead.existing_relationship_status}",
        f"Budget status: {lead.budget_status}  |  Funding route: {lead.potential_funding_route or 'n/a'}",
        f"Recommended next action: {score.recommended_next_action}",
    ]
    if score.missing_information:
        lines.append(f"Missing information: {', '.join(score.missing_information)}")
    if score.reasons:
        lines.append("Scoring notes: " + "; ".join(score.reasons))
    if lead.notes:
        lines.append(f"Existing notes on file: {lead.notes}")
    return "\n".join(lines)


def generate_outreach(lead: Lead, score: ScoreResult, mode: str | None = None) -> OutreachBundle | None:
    """Generate the outreach bundle for one lead.

    Returns None if the lead is excluded from outreach (duplicate or
    'Do not contact'). mode defaults to 'template' (no API key needed);
    pass mode='llm' to route through llm_adapter if a key is configured.
    """
    if score.excluded_from_outreach:
        return None

    use_mode = mode or ("llm" if os.environ.get("ANTHROPIC_API_KEY") else "template")

    if use_mode == "llm":
        from .llm_adapter import try_generate_with_llm
        bundle = try_generate_with_llm(lead, score)
        if bundle is not None:
            return bundle
        # Fall through to deterministic templates if the LLM path declines
        # or isn't actually wired up yet.

    linkedin = _linkedin_message(lead, score)
    return OutreachBundle(
        lead_id=lead.lead_id,
        mode="template",
        initial_email=_initial_email(lead, score),
        followup_1=_followup_1(lead, score),
        followup_2=_followup_2(lead, score),
        linkedin_message=linkedin or "(No LinkedIn message generated — insufficient role/pipeline information.)",
        internal_briefing=_internal_briefing(lead, score),
    )
