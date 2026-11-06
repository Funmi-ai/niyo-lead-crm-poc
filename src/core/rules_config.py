"""
Configurable qualification, scoring and ICP rules.

IMPORTANT — PROVISIONAL RULES:
None of the thresholds, weights or ICP definitions below are Niyo's real
rules. They are reasonable, clearly-labelled placeholders built only from
Niyo's public website, designed to be replaced wholesale once a real ICP
and funding-eligibility rules are confirmed during discovery.

Every value here is deliberately kept in one file so a future discovery
session's findings can be dropped in without touching engine code.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Pipeline classification signals
# ---------------------------------------------------------------------------

GOVERNMENT_ORG_TYPES = {
    "Public sector body",
    "Local authority",
    "Combined authority",
    "Charity / social enterprise",
    "Community organisation",
}

PRIVATE_ORG_TYPES = {
    "Private company",
    "Corporate (enterprise)",
    "SME",
}

# Named funding routes Niyo has publicly confirmed working with
# (see niyo.co (Niyo's public website)). Any other value is treated as "needs verification".
KNOWN_FUNDING_ROUTES = {
    "Innovate UK",
    "DCMS",
    "West Midlands Combined Authority (WMCA)",
    "Other public grant (unverified)",
}

# Sectors considered adjacent to Niyo's verified offerings (AI/digital/tech
# upskilling, SME support, youth employment, inclusive growth). PROVISIONAL.
PRIVATE_SECTOR_FIT = {
    "Technology / Software",
    "Financial Services",
    "Professional Services / Consulting",
    "Engineering / Manufacturing",
    "Retail",
    "Logistics",
}

GOVERNMENT_SECTOR_FIT = {
    "Local Government",
    "Education",
    "Employment & Skills",
    "Health",
    "Youth Services",
    "Community / Voluntary",
}

# ---------------------------------------------------------------------------
# Scoring weights — PROVISIONAL, configurable
# ---------------------------------------------------------------------------

SCORING_WEIGHTS = {
    "decision_maker": {
        "Decision-maker": 20,
        "Influencer": 8,
        "Not a decision-maker": -10,
        "Unknown": 0,
    },
    "budget_status": {
        "Confirmed": 20,
        "Likely": 10,
        "Unclear": 0,
        "None identified": -15,
        "Unknown": 0,
    },
    "relationship": {
        "Existing partner": 15,
        "Warm": 10,
        "Previously contacted": 5,
        "New": 0,
    },
    "sector_fit": 15,       # awarded if sector matches the pipeline's fit list
    "org_type_fit": 10,     # awarded if org type matches the pipeline cleanly
    "funding_route_known": 15,  # government pipeline only
    "size_fit_private": 10,     # private pipeline only, mid-size sweet spot

}

BASE_SCORE = 20  # every lead starts here before factor adjustments

PRIVATE_SIZE_SWEET_SPOT = {"50-249", "250-999"}  # PROVISIONAL assumption

SCORE_PRIORITISE_THRESHOLD = 70
SCORE_NURTURE_THRESHOLD = 40

# ---------------------------------------------------------------------------
# Manual-effort assumptions used ONLY for the "time saved" estimate.
# These are explicitly editable, non-measured assumptions — see README /
# the pilot-scoping notes. They must never be presented as measured results.
# ---------------------------------------------------------------------------

MANUAL_MINUTES_PER_LEAD = {
    "triage_and_dedupe": 3,
    "pipeline_classification": 2,
    "scoring_and_research": 7,
    "decision_maker_identification": 5,
    "drafting_outreach_sequence": 15,
    "crm_update": 3,
}

# ---------------------------------------------------------------------------
# Follow-up cadence — PROVISIONAL. This is the gap, in days, between one
# outreach step being sent and the next one falling due. Niyo's partnership
# manager should confirm real spacing (this is a common-sense B2B default,
# not something Niyo has specified).
# ---------------------------------------------------------------------------

CADENCE_STEPS = ["initial_email", "followup_1", "followup_2"]

CADENCE_GAP_DAYS = {
    "initial_email": 0,   # sent on the day the lead is approved/enrolled
    "followup_1": 4,      # due 4 days after the initial email is sent
    "followup_2": 5,      # due 5 days after followup_1 is sent
}
