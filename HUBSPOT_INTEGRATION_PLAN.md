# HubSpot Integration Plan

This POC runs against a **local simulation** of HubSpot (`src/crm/simulator.py`), not a live account. This document is what would need to be verified and built before a real connection — it is a planning checklist, not a commitment.

## Why simulate rather than connect now

- No HubSpot credentials were provided for this POC — correctly, since it's a pre-sales demo with no production scope agreed.
- A simulation lets a reviewer see the exact shape of what would sync, without risking any write to a live CRM, and without needing IT/security sign-off before the first demo.

## Architecture: the seam is already there

`src/crm/interface.py` defines `CRMInterface` — an abstract contract (`upsert_company`, `upsert_contact`, `upsert_deal`, `create_task`, `log_activity`, `flag_duplicate`, `get_state`, `reset`).

- `src/crm/simulator.py` → `LocalCRMSimulator` implements it today, against a JSON file.
- `src/crm/hubspot_live_stub.py` → `HubSpotLiveCRM` is the placeholder for a real implementation of the *same* interface. The orchestrator (`run_workflow.py`) only ever talks to the interface, so swapping the simulator for a live client later should not require changing the scoring, outreach or dashboard code.

## What a real cutover would need (not yet confirmed with any client)

- A private app token scoped to: `crm.objects.contacts.read/write`, `crm.objects.companies.read/write`, `crm.objects.deals.read/write`, `crm.objects.owners.read`, plus a tasks/tickets scope if tasks are modelled as native HubSpot tasks.
- The real pipeline and stage IDs for whatever deal pipelines exist in that HubSpot portal — this POC's stage names (`DEAL_STAGES_BY_SCORE` in `src/crm/simulator.py`) are placeholders.
- A decision on how duplicate detection here should reconcile with HubSpot's own duplicate management, since they can disagree.
- Rate-limit handling for the real API (this POC's simulator has no rate limits to respect, since it's local).
