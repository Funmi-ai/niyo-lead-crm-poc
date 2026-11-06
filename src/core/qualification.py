"""Steps 4-7 of the workflow: pipeline classification + explainable scoring.

Every score is reproducible from the lead's fields and the rules in
rules_config.py — no hidden state, no randomness, no invented certainty.
Where evidence is missing the engine returns 'Unknown' / 'Needs review'
rather than guessing.
"""
from __future__ import annotations

from . import rules_config as cfg
from .models import Lead, ScoreFactor, ScoreResult


def classify_pipeline(lead: Lead) -> str:
    """Classify a lead as 'Government-funded', 'Private-sector' or 'Unclear'.

    PROVISIONAL rule: organisation type is the primary signal; an explicit
    funding route mention is a secondary signal for ambiguous org types
    (e.g. charities, which can sit in either pipeline).
    """
    org_type = lead.organisation_type

    if org_type in cfg.GOVERNMENT_ORG_TYPES:
        return "Government-funded"
    if org_type in cfg.PRIVATE_ORG_TYPES:
        return "Private-sector"

    if lead.potential_funding_route and lead.potential_funding_route != "Unknown":
        return "Government-funded"

    return "Unclear"


def _score_private(lead: Lead, factors: list[ScoreFactor], missing: list[str]) -> int:
    points = 0

    if lead.sector in cfg.PRIVATE_SECTOR_FIT:
        points += cfg.SCORING_WEIGHTS["sector_fit"]
        factors.append(ScoreFactor("sector_fit", cfg.SCORING_WEIGHTS["sector_fit"],
                                    f"Sector '{lead.sector}' matches Niyo's corporate-offer fit list"))
    elif lead.sector == "Unknown":
        missing.append("sector")
    else:
        factors.append(ScoreFactor("sector_fit", 0, f"Sector '{lead.sector}' not on the current fit list"))

    if lead.organisation_type == "Private company" or lead.organisation_type == "Corporate (enterprise)":
        points += cfg.SCORING_WEIGHTS["org_type_fit"]
        factors.append(ScoreFactor("org_type_fit", cfg.SCORING_WEIGHTS["org_type_fit"],
                                    "Organisation type cleanly matches the private-sector pipeline"))

    if lead.organisation_size in cfg.PRIVATE_SIZE_SWEET_SPOT:
        points += cfg.SCORING_WEIGHTS["size_fit_private"]
        factors.append(ScoreFactor("size_fit", cfg.SCORING_WEIGHTS["size_fit_private"],
                                    f"Organisation size '{lead.organisation_size}' is in the provisional sweet spot"))
    elif lead.organisation_size == "Unknown":
        missing.append("organisation_size")

    return points


def _score_government(lead: Lead, factors: list[ScoreFactor], missing: list[str]) -> int:
    points = 0

    if lead.sector in cfg.GOVERNMENT_SECTOR_FIT:
        points += cfg.SCORING_WEIGHTS["sector_fit"]
        factors.append(ScoreFactor("sector_fit", cfg.SCORING_WEIGHTS["sector_fit"],
                                    f"Sector '{lead.sector}' matches Niyo's government-programme fit list"))
    elif lead.sector == "Unknown":
        missing.append("sector")
    else:
        factors.append(ScoreFactor("sector_fit", 0, f"Sector '{lead.sector}' not on the current fit list"))

    if lead.organisation_type in cfg.GOVERNMENT_ORG_TYPES:
        points += cfg.SCORING_WEIGHTS["org_type_fit"]
        factors.append(ScoreFactor("org_type_fit", cfg.SCORING_WEIGHTS["org_type_fit"],
                                    "Organisation type cleanly matches the government-funded pipeline"))

    if lead.potential_funding_route in cfg.KNOWN_FUNDING_ROUTES and lead.potential_funding_route != "Other public grant (unverified)":
        points += cfg.SCORING_WEIGHTS["funding_route_known"]
        factors.append(ScoreFactor("funding_route_known", cfg.SCORING_WEIGHTS["funding_route_known"],
                                    f"Funding route '{lead.potential_funding_route}' is a route Niyo has publicly confirmed"))
    elif not lead.potential_funding_route or lead.potential_funding_route == "Unknown":
        missing.append("potential_funding_route")
    else:
        factors.append(ScoreFactor("funding_route_known", 0,
                                    f"Funding route '{lead.potential_funding_route}' is unverified — needs an eligibility check"))

    return points


def score_lead(lead: Lead, is_duplicate: bool = False, duplicate_of: str | None = None) -> ScoreResult:
    pipeline = classify_pipeline(lead)
    factors: list[ScoreFactor] = []
    missing: list[str] = []
    reasons: list[str] = []

    score = cfg.BASE_SCORE
    factors.append(ScoreFactor("base_score", cfg.BASE_SCORE, "Starting baseline for every lead"))

    dm_points = cfg.SCORING_WEIGHTS["decision_maker"].get(lead.decision_maker_status, 0)
    score += dm_points
    factors.append(ScoreFactor("decision_maker_status", dm_points,
                                f"Contact decision-maker status: {lead.decision_maker_status}"))
    if lead.decision_maker_status == "Unknown":
        missing.append("decision_maker_status")

    budget_points = cfg.SCORING_WEIGHTS["budget_status"].get(lead.budget_status, 0)
    score += budget_points
    factors.append(ScoreFactor("budget_status", budget_points, f"Budget status: {lead.budget_status}"))
    if lead.budget_status in ("Unknown", "Unclear"):
        missing.append("budget_status")

    rel_points = cfg.SCORING_WEIGHTS["relationship"].get(lead.existing_relationship_status, 0)
    score += rel_points
    factors.append(ScoreFactor("existing_relationship", rel_points,
                                f"Existing relationship: {lead.existing_relationship_status}"))

    if pipeline == "Private-sector":
        score += _score_private(lead, factors, missing)
    elif pipeline == "Government-funded":
        score += _score_government(lead, factors, missing)
    else:
        reasons.append("Pipeline unclear — organisation type and funding route do not clearly indicate a pipeline")
        missing.append("organisation_type")

    score = max(0, min(100, score))

    needs_review = bool(missing) or pipeline == "Unclear" or lead.consent_status in ("Needs review", "Unknown")
    if lead.consent_status in ("Needs review", "Unknown"):
        reasons.append(f"Consent / lawful-outreach status is '{lead.consent_status}' — confirm before contacting")

    excluded = False
    exclusion_reason = None

    if lead.consent_status == "Do not contact":
        excluded = True
        exclusion_reason = "Consent/lawful-outreach review marked this lead 'Do not contact'"
        needs_review = False

    if is_duplicate:
        excluded = True
        exclusion_reason = (exclusion_reason + "; " if exclusion_reason else "") + f"Duplicate of {duplicate_of}"
        needs_review = False

    if missing:
        reasons.append("Missing information: " + ", ".join(sorted(set(missing))))

    if excluded:
        next_action = "Do not contact" if lead.consent_status == "Do not contact" else "Merge duplicate record — do not contact separately"
    elif needs_review:
        next_action = "Research / human review needed before outreach"
    elif lead.decision_maker_status == "Not a decision-maker":
        next_action = "Identify the actual budget holder; use this contact only as an internal introduction"
    elif score >= cfg.SCORE_PRIORITISE_THRESHOLD:
        next_action = "Prioritise — send initial outreach"
    elif score >= cfg.SCORE_NURTURE_THRESHOLD:
        next_action = "Add to nurture sequence; revisit in future outreach batches"
    else:
        next_action = "Low priority — monitor only, no active outreach"

    return ScoreResult(
        lead_id=lead.lead_id,
        pipeline=pipeline,
        overall_score=score,
        factors=factors,
        reasons=reasons,
        missing_information=sorted(set(missing)),
        recommended_next_action=next_action,
        needs_human_review=needs_review,
        excluded_from_outreach=excluded,
        exclusion_reason=exclusion_reason,
        is_duplicate=is_duplicate,
        duplicate_of=duplicate_of,
    )
