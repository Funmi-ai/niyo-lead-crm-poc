"""Lead data model shared across the pipeline, scoring, outreach and CRM modules."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

LEAD_FIELDS = [
    "lead_id",
    "organisation_name",
    "organisation_type",
    "sector",
    "organisation_size",
    "website",
    "contact_name",
    "contact_job_title",
    "contact_email",
    "lead_source",
    "location",
    "partnership_interest",
    "relevant_programme",
    "potential_funding_route",
    "budget_status",
    "decision_maker_status",
    "existing_relationship_status",
    "previous_contact_date",
    "last_interaction",
    "pipeline",
    "crm_stage",
    "notes",
    "consent_status",
]


@dataclass
class Lead:
    lead_id: str
    organisation_name: str = ""
    organisation_type: str = "Unknown"
    sector: str = "Unknown"
    organisation_size: str = "Unknown"
    website: str = ""
    contact_name: str = ""
    contact_job_title: str = ""
    contact_email: str = ""
    lead_source: str = "Unknown"
    location: str = "Unknown"
    partnership_interest: str = ""
    relevant_programme: str = ""
    potential_funding_route: str = ""
    budget_status: str = "Unknown"
    decision_maker_status: str = "Unknown"
    existing_relationship_status: str = "New"
    previous_contact_date: str = ""
    last_interaction: str = ""
    pipeline: str = "Unclassified"
    crm_stage: str = "New"
    notes: str = ""
    consent_status: str = "Unknown"

    @classmethod
    def from_dict(cls, data: dict) -> "Lead":
        clean = {k: data.get(k, "") for k in LEAD_FIELDS}
        return cls(**clean)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScoreFactor:
    factor: str
    points: int
    reason: str


@dataclass
class ScoreResult:
    lead_id: str
    pipeline: str
    overall_score: int
    factors: list = field(default_factory=list)  # list[ScoreFactor]
    reasons: list = field(default_factory=list)
    missing_information: list = field(default_factory=list)
    recommended_next_action: str = ""
    needs_human_review: bool = False
    excluded_from_outreach: bool = False
    exclusion_reason: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["factors"] = [asdict(f) if not isinstance(f, dict) else f for f in self.factors]
        return d
