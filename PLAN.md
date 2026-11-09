# Heidi Lead Intelligence implementation plan

Deadline: 10 November 2026, 18:00 Europe/Berlin.

## Inspection
Workspace was empty. Python 3.11–3.14 are installed. No relevant API-key environment-variable names were present. Connected Google Sheets access works. Original sheet is read-only for this workflow; preserve all five tabs as JSON snapshots. Baseline counts must be measured from rows.

## Architecture and milestones
1. **P0 import and preservation.** Save original sheet responses and import RAW_DIRECTORY (CSV, XLSX and JSON adapters). Preserve contacts as unverified directory contacts. Acceptance: every input row accounted for, source hash recorded, originals unchanged.
2. **P0 identity and models.** Pydantic company/evidence/contact models; Unicode normalization; conservative name plus domain/address deduplication, preserving legal suffix distinctions. Acceptance: synthetic collision and missing-data tests pass; raw IDs retained.
3. **P0 source enrichment.** Robots-aware, rate-limited HTTP fetcher with immutable content-addressed snapshots, timeouts and per-company failures. Inspect same-host service/contact pages with bounded page count. Snapshot mode never accesses network. Only explicit positive German service phrases qualify; uncertain text remains unknown. Acceptance: evidence quotes and URLs trace to saved text; blocked sites remain research candidates.
4. **P0 qualification.** Config-versioned weights 30/25/25/10/10. Scores are observed lower bounds, accompanied by maximum possible score and weighted completeness. Berlin office is distinct from verified service coverage. Insufficient evidence gives Needs Research. Acceptance: exact boundaries and unknown-vs-false tests.
5. **P0 delivery.** Six-tab formatted XLSX, processed JSON, run statistics, methodology and short submission brief. Acceptance: reopen XLSX, correct row counts, filters and frozen panes, no injected formulas, deterministic snapshot rerun.
6. **P1 AI and contacts.** Optional environment-configured AI extraction, schema validation, quote grounding, bounded retries, cache keyed by source/model/prompt. API key added locally by user. Acceptance: mocked malformed/unsupported responses rejected; live AI is explicitly unverified until credentials are configured. Never infer email patterns or decision-maker roles from directory names.
7. **P1 audit.** Review a deterministic sample of source-backed records, record discrepancies and limits. Acceptance: report actual sample size and findings, no invented accuracy metric.
8. **P2 optional integrations.** Google Sheets write synchronization and further discovery providers are deferred until P0 is usable. Existing sheet must not be overwritten.

## Dependencies and interfaces
Python 3.11+, requests, BeautifulSoup, Pydantic, PyYAML, python-dotenv, openpyxl, pytest; pin installed versions. Openpyxl is explicitly requested in the project brief for the reproducible Python export. Sources return original row dictionaries; fetcher returns URL/time/text/hash; extractors return typed facts with quotes; scorer is a pure function; exporter consumes scored records.

## Risks and fallback approaches
- Public sites may block access, prohibit crawling, be stale or require JavaScript: retain unknowns and log reason; no bypass.
- Directory membership does not establish residential services or procurement responsibility.
- Names/domains shared by related legal entities must not trigger automatic merges.
- Website claims and regex matches require contextual review; publish audit limits.
- Missing API key: deterministic extraction works; optional AI remains off.
- Sheet unavailable later: export RAW_DIRECTORY as CSV/XLSX and import locally.
- Snapshot replay reproduces stored facts, not freshness. Live runs use new manifests and preserve prior content.

## Milestone reporting
Record actual test results, record counts, failures and remaining gaps in reports/VALIDATION.md. README must provide commands for import, live enrichment, offline replay, scoring and export.

## Implemented status
- Milestones 1–5: implemented and executed against all 381 real records; 28 synthetic tests pass. Workbook and reports generated.
- Milestone 6: OpenAI structured extraction implemented and live-tested with gpt-5-mini. Five-company pilot completed, usage/error tracking added, and Berlin-wide enrichment authorised. Independent contact research remains incomplete. See reports/BERLIN_AI.md for the separate full-run results.
- Milestone 7: 20-record assistant-assisted sample review and four portfolio-count checks documented. No independent human accuracy study.
- Milestone 8: deferred. Source Google Sheet preserved unchanged.
- See reports/VALIDATION.md for actual coverage, failures, limitations and next steps.
