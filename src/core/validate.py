"""Step 1-2 of the workflow: import + validate/normalise raw lead records."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .models import Lead, LEAD_FIELDS

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REQUIRED_FOR_OUTREACH = [
    "organisation_name",
    "contact_name",
    "contact_email",
]


def load_leads(path: str) -> list[Lead]:
    """Load raw leads from CSV or JSON into Lead objects (unvalidated)."""
    p = Path(path)
    if p.suffix.lower() == ".json":
        raw = json.loads(p.read_text())
    elif p.suffix.lower() == ".csv":
        with p.open(newline="", encoding="utf-8") as f:
            raw = list(csv.DictReader(f))
    else:
        raise ValueError(f"Unsupported file type: {path}")
    return [Lead.from_dict(r) for r in raw]


def normalise_lead(lead: Lead) -> tuple[Lead, list[str]]:
    """Trim whitespace, lower-case emails, fill blanks with 'Unknown'.

    Returns the normalised lead plus a list of validation issues found.
    """
    issues: list[str] = []

    for field_name in LEAD_FIELDS:
        value = getattr(lead, field_name)
        if isinstance(value, str):
            setattr(lead, field_name, value.strip())

    lead.contact_email = lead.contact_email.lower()
    lead.organisation_name = lead.organisation_name.strip()

    if lead.contact_email and not EMAIL_RE.match(lead.contact_email):
        issues.append(f"Malformed email: '{lead.contact_email}'")

    for req in REQUIRED_FOR_OUTREACH:
        value = getattr(lead, req)
        if not value or value.lower() == "unknown":
            issues.append(f"Missing required field: {req}")

    # Normalise blank optional fields to the explicit 'Unknown' sentinel so
    # downstream scoring can distinguish "we checked and there's none" from
    # "we never captured this".
    optional_fields = [
        "organisation_type", "sector", "organisation_size",
        "budget_status", "decision_maker_status", "consent_status",
    ]
    for f in optional_fields:
        value = getattr(lead, f)
        if not value:
            setattr(lead, f, "Unknown")

    return lead, issues


def validate_and_normalise(leads: list[Lead]) -> tuple[list[Lead], dict[str, list[str]]]:
    """Normalise every lead; return (leads, {lead_id: [issues]})."""
    issues_by_lead: dict[str, list[str]] = {}
    cleaned = []
    for lead in leads:
        lead, issues = normalise_lead(lead)
        cleaned.append(lead)
        if issues:
            issues_by_lead[lead.lead_id] = issues
    return cleaned, issues_by_lead
