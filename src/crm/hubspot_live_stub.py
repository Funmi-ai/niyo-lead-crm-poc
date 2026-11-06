"""Placeholder for a future real-HubSpot implementation of CRMInterface.

Not implemented, and not callable — this file exists purely to document
the seam. A production build would implement each method against the
HubSpot CRM API (contacts, companies, deals, tasks, engagements) using a
private app token with at minimum:

  crm.objects.contacts.read / write
  crm.objects.companies.read / write
  crm.objects.deals.read / write
  crm.objects.owners.read
  tickets / tasks scopes if tasks are modelled as HubSpot tasks

See HUBSPOT_INTEGRATION_PLAN.md for the full checklist (subscription tier,
pipeline/stage mapping, rate limits, duplicate-matching rules, field
mapping) that must be confirmed with Niyo before any of this is built.
"""
from __future__ import annotations

from .interface import CRMInterface


class HubSpotLiveCRM(CRMInterface):
    def __init__(self, *_, **__):
        raise NotImplementedError(
            "Live HubSpot integration is out of scope for this POC. "
            "See HUBSPOT_INTEGRATION_PLAN.md."
        )

    def upsert_company(self, lead: dict) -> dict: ...
    def upsert_contact(self, lead: dict) -> dict: ...
    def upsert_deal(self, lead: dict, score: dict) -> dict: ...
    def create_task(self, lead_id: str, title: str, due_in_days: int) -> dict: ...
    def log_activity(self, lead_id: str, activity_type: str, detail: str) -> dict: ...
    def flag_duplicate(self, lead_id: str, primary_lead_id: str) -> dict: ...
    def get_state(self) -> dict: ...
    def reset(self) -> None: ...
