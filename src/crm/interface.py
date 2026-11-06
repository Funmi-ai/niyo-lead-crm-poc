"""Abstract CRM interface.

LocalCRMSimulator (simulator.py) implements this against a local JSON file.
A future HubSpotLiveCRM would implement the same interface against the real
HubSpot API — see HUBSPOT_INTEGRATION_PLAN.md for what that would require
(scopes, auth, rate limits) before any production cutover.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class CRMInterface(ABC):
    @abstractmethod
    def upsert_company(self, lead: dict) -> dict: ...

    @abstractmethod
    def upsert_contact(self, lead: dict) -> dict: ...

    @abstractmethod
    def upsert_deal(self, lead: dict, score: dict) -> dict: ...

    @abstractmethod
    def create_task(self, lead_id: str, title: str, due_in_days: int) -> dict: ...

    @abstractmethod
    def log_activity(self, lead_id: str, activity_type: str, detail: str) -> dict: ...

    @abstractmethod
    def flag_duplicate(self, lead_id: str, primary_lead_id: str) -> dict: ...

    @abstractmethod
    def get_state(self) -> dict: ...

    @abstractmethod
    def reset(self) -> None: ...
