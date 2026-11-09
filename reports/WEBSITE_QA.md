# Website verification

The priority-first static dashboard is implemented in `website/heidi-leads`.

Private deployment confirmed successful: https://heidi-berlin-lead-intelligence.quaintgiraffe.chatgpt.site

Source commit: `838b2b80313cc3df04e08abb0e6094f0051f0d95`.

## Vercel publication
Production URL: https://heidi-berlin-lead-intelligence.vercel.app

Vercel project: `teamsiemen/heidi-berlin-lead-intelligence`. Deployment: `dpl_9kujCTPU8tGh4ZKYu4pvCbaqxG1C`, ready state `READY`.

Unauthenticated HTTP checks returned 200 for the homepage, company dataset, JavaScript module and Excel download. The deployed dataset contains 292 companies and 35 priority leads. The production alias is accessible without sign-in; the individual deployment URL may use Vercel authentication.

## Public contact update
Company details now display available directory names, public directory emails, telephone numbers, roles, LinkedIn links when available, sources and verification labels. Directory emails remain labelled unverified. Contact data is joined using original raw record IDs, not fuzzy company-name matching. No contact data was guessed or newly researched.

Across 292 companies: 290 have public contact data, 279 have emails, 284 have telephone numbers and two show “No public contact found”. Contact matching tests passed (2 cases), along with website tests for empty contacts, email/telephone links, unverified labels, escaping and unsafe-source URLs. No new API calls were made.

## Implemented
- Default Priority Leads view with 18 High and 17 Medium Priority companies.
- All 292 companies with search, service/portfolio/billing/portal/status/completeness filters, sorting, result counts, pagination and URL state.
- Company detail panels with exact German quotes, provenance, retrieval dates, score reasons, unknowns and unverified contact labels.
- Research overview and methodology with real configuration thresholds, weights and coverage figures.
- Validated Excel and methodology-report downloads.
- Responsive layouts and native dialog keyboard containment; these interactions are implemented but browser verification is unavailable.

## Checks performed
- Exporter asserts unique company IDs, record totals, priority totals and enrichment-status totals against the run manifest.
- Node tests passed for the 292 records, 35 priority records, 18/17/257 distribution, empty search, case-insensitive domain search, combined filters, unknown-unit sorting, AI status, download presence and presentation export.
- JavaScript syntax check passed.
- Local HTTP server returned status 200.
- Site repository is restricted to presentation source, allowlisted exported data and final workbook/report. No .env, API key, raw source cache or API attempt logs were packaged.
- Existing Python results and Google Sheet were not modified. No new OpenAI calls were made for the website.

## Verification limit
The browser access host was unavailable when opening the local preview. Screenshots, visual layout, real browser interactions and assistive-technology behavior were not verified. The deployment service independently confirms hosting status; it does not substitute for browser QA.
