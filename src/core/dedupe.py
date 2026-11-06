"""Step 3: duplicate detection.

Two signals are used:
  1. Exact match on normalised email — a strong, unambiguous signal.
  2. Fuzzy match on BOTH organisation name and contact name — catches the
     common real-world noise an exact-match-only check misses (e.g. "Ltd"
     vs "Limited", stray punctuation, minor typos from re-keying a business
     card), without just comparing one field, which would risk false
     positives (two different people at similarly-named organisations).

This is still a demo-grade heuristic, not real entity resolution — see
ASSUMPTIONS.md. Requiring BOTH org-name and contact-name similarity above
threshold is the deliberate guard against false positives.

The first occurrence in file order is kept as the primary record; later
matches are flagged with duplicate_of = <primary lead_id> and excluded
from outreach.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import Lead

# PROVISIONAL thresholds — tune against real data once available.
ORG_SIMILARITY_THRESHOLD = 0.90
NAME_SIMILARITY_THRESHOLD = 0.90

# Common UK company-suffix noise that shouldn't count as a real difference.
_ORG_SUFFIXES = re.compile(
    r"\b(ltd|limited|llp|plc|cic|inc|incorporated|co|company|group|holdings|"
    r"enterprises|enterprise|partnership|partners)\b",
    re.IGNORECASE,
)
_PUNCTUATION = re.compile(r"[^\w\s]")
_WHITESPACE = re.compile(r"\s+")


def _normalize_org_name(name: str) -> str:
    name = name.lower()
    name = _ORG_SUFFIXES.sub(" ", name)
    name = _PUNCTUATION.sub(" ", name)
    name = _WHITESPACE.sub(" ", name).strip()
    return name


def _normalize_person_name(name: str) -> str:
    name = name.lower()
    name = _PUNCTUATION.sub(" ", name)
    name = _WHITESPACE.sub(" ", name).strip()
    return name


def _normalize_email(email: str) -> str:
    return "".join(email.lower().split())


def _similar(a: str, b: str, threshold: float) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold


def detect_duplicates(leads: list[Lead]) -> dict[str, str]:
    """Return {duplicate_lead_id: primary_lead_id} for every duplicate found."""
    duplicates: dict[str, str] = {}
    # Each entry: (lead_id, normalised_email, normalised_org, normalised_name)
    primaries: list[tuple[str, str, str, str]] = []

    for lead in leads:
        email_key = _normalize_email(lead.contact_email) if lead.contact_email else ""
        norm_org = _normalize_org_name(lead.organisation_name) if lead.organisation_name else ""
        norm_name = _normalize_person_name(lead.contact_name) if lead.contact_name else ""

        match_id = None
        for pid, p_email, p_org, p_name in primaries:
            if email_key and p_email and email_key == p_email:
                match_id = pid
                break
            if _similar(norm_org, p_org, ORG_SIMILARITY_THRESHOLD) and \
               _similar(norm_name, p_name, NAME_SIMILARITY_THRESHOLD):
                match_id = pid
                break

        if match_id:
            duplicates[lead.lead_id] = match_id
        else:
            primaries.append((lead.lead_id, email_key, norm_org, norm_name))

    return duplicates
