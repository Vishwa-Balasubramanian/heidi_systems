# Berlin AI enrichment report

Scope: 292 directory-listed Berlin offices. This is a separate output from the preserved 381-record regional baseline.
Saved homepages were submitted to OpenAI; no additional website discovery or Google Sheet writes occurred.
AI interprets homepage text only. Existing rule evidence from homepage and service pages is preserved.

## Measured results

| Metric | Result |
|---|---:|
| companies | 292 |
| ai_completed | 182 |
| ai_failed | 9 |
| no_saved_homepage | 43 |
| no_listed_website | 58 |
| high_priority | 18 |
| medium_priority | 17 |
| needs_research | 257 |
| api_attempts | 230 |
| attempts_without_cost | 0 |
| estimated_tracked_cost_usd | 1.1806895 |
| published_unit_counts | 22 |
| field_evidence_validated | 696 |
| ai_fields_accepted | 335 |
| ai_fields_removed_by_final_review | 57 |
| Scores changed from baseline | 78 |

## Review and safeguards

All accepted evidence quotes were checked against saved page text. Cached AI responses were revalidated under the final field checks without further API calls.
Review of extracted portfolio quotes identified tenant/owner counts incorrectly treated as units, static HTML counters showing zero, and generic plural wording incorrectly treated as multiple-building evidence. These cases are rejected by the final checks. Approximate and lower-bound unit figures retain qualifiers. Company-wide totals are not claimed to be Berlin-only totals.
Address-only Berlin coverage, vague digital wording, general property management without residential wording, and cost optimisation without billing evidence are also rejected.
These checks reduce observed errors but do not establish measured precision or recall. No independent human audit was conducted. Official ownership of every directory-linked website and contacts remain unverified.

## API cost and failures

Estimated costs cover tracked API attempts in this run, including responses rejected by validation. Previously cached pilot calls are excluded. Unknown costs, if present, are not treated as zero. Rates and token usage are retained in API attempt records; estimates are not invoices.
Detailed usage: outputs/berlin_ai/usage.json. Failed or unavailable enrichment does not erase baseline facts.

- 9 × AI extraction failed after 3 attempts: ValidationError: ValidationError

## Reproduce offline

```powershell
.\.venv\Scripts\python tools/finalize_berlin_ai.py
.\.venv\Scripts\python tools/report_ai_usage.py --directory outputs/berlin_ai/api_attempts --output outputs/berlin_ai/usage.json
.\.venv\Scripts\python tools/report_berlin_ai.py
```

Keep baseline, raw page snapshots, AI cache, config, prompts and source together. Do not commit .env or credentials.