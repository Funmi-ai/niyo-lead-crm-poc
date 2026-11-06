# niyo-lead-crm-poc — Niyo-inspired Lead Qualification & CRM Prototype

**Independent prototype using synthetic data. Not a live deployment or endorsed integration.**

A proof-of-concept lead-qualification and CRM pipeline, inspired by the public offering of [Niyo](https://niyo.co) — a UK company that trains people for AI and tech careers and places them with corporate and public-sector partners. Built on synthetic data, using only facts from Niyo's own public website. Not a live integration, not a signed engagement, not commissioned or endorsed by Niyo.

## Problem

Niyo runs two distinct partnership tracks, by its own public description: companies paying for workforce upskilling or hiring from cohorts, and publicly-funded programmes with their own eligibility rules (Innovate UK, DCMS, WMCA are the named funders on their site). Any organisation running two tracks like this needs different qualifying logic for each — a company's budget and seniority signals mean nothing against a funding-eligibility rubric, and vice versa. This POC explores what a shared lead-scoring and CRM layer for that kind of two-track pipeline could look like.

## Solution

An 8-step pipeline, run end to end on synthetic data (`run_workflow.py`):

```
Import leads → Validate & normalise → Detect duplicates → Classify pipeline
→ Score against rules → Draft outreach → Simulate CRM update → Write run summary
```

A Streamlit dashboard (`dashboard/app.py`) lets a reviewer step through the same pipeline, inspect what the scoring engine decided and why, and approve or reject each generated outreach draft before anything would "go out" (`dashboard/approvals.py`) — nothing here ever sends a real message.

## Architecture

- **`src/core/`** — validation, deduplication, and scoring, each a small, independently testable module. Scoring rules live in one config file (`rules_config.py`), explicitly labelled as provisional, so they can be swapped for a real client's ICP without touching the engine.
- **`src/crm/`** — an abstract `CRMInterface` (`interface.py`) with two implementations: `LocalCRMSimulator` (`simulator.py`), a JSON-backed stand-in that runs today, and `HubSpotLiveCRM` (`hubspot_live_stub.py`), a deliberately unimplemented placeholder for a real connection later. The orchestrator only ever talks to the interface, so the CRM backend can change without touching the scoring or outreach code.
- **`src/outreach/`** — deterministic, template-based outreach drafting by default (`generator.py`), with a documented, intentionally-unwired seam for an LLM call later (`llm_adapter.py`). The demo runs with zero API keys and zero spend.
- **`dashboard/`** — a human-in-the-loop review UI over the same pipeline state.
- **`tests/`** — automated tests over the sequencing and workflow logic (`tests/test_sequencer.py`, `tests/test_workflow.py`).

## My contribution

Designed and built solo: the pipeline, the scoring rules, the CRM abstraction and both its implementations, the outreach templates, the dashboard, the synthetic dataset generator, and the test suite. No team, no prior codebase.

## Reliability considerations

This is explicitly **not** a durable-execution system — there is no retry logic, no backoff, and no replay of a crashed run anywhere in this codebase (checked directly, not assumed). What it does have:

- Input validation that surfaces explicit, specific errors (malformed email, missing required field) rather than failing silently or crashing downstream.
- A documented, honest limitation on the dedupe heuristic: fuzzy matching on organisation name *and* contact name together, flagged in the code itself as "demo-grade... not real entity resolution," with the reasoning for why both signals are required (to avoid false positives) written down next to the threshold values.
- A real integration seam between business logic and the CRM backend, so a future production cutover is a new class, not a rewrite.
- A human-approval gate before any outreach draft is treated as sent.

## Commercial relevance

This is the closest project in this portfolio, in *shape*, to the kind of system a company buys workflow-reliability tooling to run: a multi-step pipeline with a real integration boundary, built with the expectation that the rules behind it will change once a real client signs off on them. It does not replace a durable-execution platform; it's the kind of business logic that would eventually need to run on one.

## Limitations

- Built on synthetic, fictional leads (`generate_synthetic_data.py` — RFC 2606 example.com/.org/.net domains, no real companies or people).
- Scoring thresholds and ICP rules are invented placeholders, explicitly labelled as such (see `ASSUMPTIONS.md`), not a real client's confirmed criteria.
- No live CRM connection; `HubSpotLiveCRM` raises `NotImplementedError` on purpose.
- Not multi-user, not transactional — state is a single local JSON file, and a reset is destructive by design.
- No retry, backoff, or crash recovery anywhere in the pipeline.
