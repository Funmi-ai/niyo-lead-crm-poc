# Assumptions

Everything below is a placeholder used to make the proof of concept runnable, clearly separated from anything confirmed by a real client. Every value lives in `src/core/rules_config.py` so it can be replaced in one place once real rules are provided.

## Not yet confirmed by any real client

1. **Private-sector ICP** — sector list, size "sweet spot" (`50-249` / `250-999` employees), and which signals count as budget/decision-maker fit are all invented-but-reasonable placeholders, not a documented ICP from the business this was built for.
2. **Funding-route eligibility** — only a handful of named funding routes are treated as "verified" (because they were named on the client's own public site). Anything else is flagged `Needs review`, not accepted or rejected.
3. **Decision-maker titles** — the engine does not try to infer "is this person a decision-maker" from job-title text. It trusts an explicit `decision_maker_status` field. In production this would either come from CRM enrichment or a title-matching rule the client signs off on.
4. **Scoring weights and thresholds** (`SCORE_PRIORITISE_THRESHOLD = 70`, `SCORE_NURTURE_THRESHOLD = 40`, all point values) — arbitrary but documented, reproducible numbers. Expect to recalibrate against real win/loss data.
5. **Manual-effort-per-lead assumptions** (`MANUAL_MINUTES_PER_LEAD`) — used only for the "time saved" estimate on the dashboard. These are editable guesses, not measured figures, and the dashboard labels them as such.

## Technical assumptions

- Dedupe matches on normalised email OR normalised (organisation name + contact name). No fuzzy/phonetic matching — a real implementation might need it for noisier CRM data.
- "Decision-maker", "Influencer", "Not a decision-maker" and "Unknown" are the only decision-maker states modelled. A real CRM's property options may differ.
- The CRM simulation stores state in a single local JSON file (`data/crm_state.json`). It is not multi-user, not transactional, and resets are destructive by design — this is a demo, not a system of record.
- No LLM API is called by default (`src/outreach/llm_adapter.py` is a documented no-op stub) — outreach is fully deterministic template text, so the demo runs with zero API keys and zero spend.
