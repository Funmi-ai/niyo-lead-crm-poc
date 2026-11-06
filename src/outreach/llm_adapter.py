"""Optional LLM integration point — NOT wired to a live API call by default.

This POC must run with zero paid API usage out of the box. This module is
the documented seam where a real Claude call would go in a later phase:
you'd pass the same structured brief used by generator.py's deterministic
templates (lead fields + score factors + niyo.co (Niyo's public website) excerpts) to the
model, with an explicit instruction not to invent facts about the recipient
or Niyo's services.

Deliberately left unimplemented: wiring a real API call here without the
partnership manager's explicit sign-off would mean outreach copy quality
(and API spend) shifts from "demo" to "production" without anyone deciding
that. Returning None here keeps the caller falling back to the labelled
template drafts, which is the correct default for a sales-demo POC.
"""
from __future__ import annotations

from ..core.models import Lead, ScoreResult


def try_generate_with_llm(lead: Lead, score: ScoreResult):
    """Return an OutreachBundle from a real LLM call, or None to fall back.

    Returns None unconditionally for now — see module docstring.
    """
    return None
