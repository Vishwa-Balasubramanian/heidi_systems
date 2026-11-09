# Heidi Lead Intelligence website plan

## Purpose and scope
Create a polished, interactive presentation of the existing 292 Berlin company records for the Heidi Systems assignment reviewer. Let a visitor understand the results, explore every company, inspect why a lead was ranked, and download the final workbook.

Implementation uses a lightweight static dashboard in `website/heidi-leads`. Priority Leads is the opening view and main attraction. Build from the existing validated results; new discovery and additional AI calls are outside the website scope.

## Verified dataset
Source: `outputs/berlin_ai/leads.json` and `outputs/berlin_ai/manifest.json`.

| Measure | Count |
|---|---:|
| Berlin companies | 292 |
| High Priority | 18 |
| Medium Priority | 17 |
| Needs Research | 257 |
| Successful AI enrichments | 182 |
| Failed AI enrichments | 9 |
| No saved homepage | 43 |
| No listed website | 58 |
| Published unit counts | 22 |
| Accepted field evidence items | 696 |

Priority and enrichment status are separate dimensions. Do not assume all failed/skipped enrichment records are Needs Research; derive intersections from the actual records. 292 is the directory-listed Berlin-office population, not a claim that all Berlin property managers have been found. The baseline regional dataset contains 381 records and is outside the primary website view.

## Visitor journey and navigation
Navigation: Priority Leads · All Companies · Research Overview · Methodology. Priority Leads is the default page. A persistent Download Excel action opens the validated workbook.

### Overview
- Title: “Berlin property management intelligence”. Short explanation of the business question and research date from the manifest.
- Four concise metrics: 292 companies, 18 High Priority, 17 Medium Priority, 257 Needs Research. Each opens the matching list filter.
- One priority-distribution chart with an accessible text equivalent. Show research coverage separately, with 182 AI successes and 110 failed/skipped records, broken down by reason.
- Short preview of the highest-ranked candidates with company name, score, completeness and website link. Link to all 35 priority leads.
- Explain that scores reflect published evidence and unknowns, not measured purchase probability. Provide a visible path to methodology and full data.

### Companies: default view shows all 292
- Search company name, address and domain. Priority quick filters: All (292), High (18), Medium (17), Needs Research (257).
- Additional filters: service evidence (WEG/rental/residential), published unit count, billing evidence, portal evidence, enrichment status, and completeness range.
- Sort by company name, observed business-fit score, completeness or published units. Unknown values sort last for numeric fields.
- Table columns: Company, Priority, Business-fit score, Evidence completeness, Published units, Service signals, Website and Details.
- Keep score and completeness visually distinct. Unit figures show their approximate/lower-bound qualifier. A company-wide figure is not a Berlin-only apartment count.
- Display current result count, active filters, Clear filters and pagination (25 rows by default). Preserve state in the URL so reviewers can share a filtered view.
- Use a readable card layout on small screens. Empty searches show “No companies match these filters” with a reset action.

### Company details
Open a side panel on desktop and a full detail view on mobile; use stable company IDs for links.
- Identity: company name, directory-listed address, website, office flag, service-area evidence and address-validation note where applicable.
- Qualification: priority, observed score, possible upper bound, completeness, confidence and plain-language reasons for each scoring criterion.
- Business facts: services, units, buildings/properties, billing relevance and digital features. Explicitly label unknowns.
- Field evidence: factual value, exact German quote, source URL, retrieval date and extraction method. Expand audit information such as model/prompt only when requested.
- Research status: whether AI completed, failed or was skipped; translate technical errors into understandable labels.
- Contacts: show verification status alongside any professional contact. Directory-listed people remain unverified. Do not invent decision-maker titles or email validity.

### Priority Leads
- The same underlying company component, prefiltered to High + Medium: 35 records. No duplicate dataset or separate ranking logic.
- Group headings for High and Medium, with score/completeness and supporting facts readily visible.
- Avoid implying that the 257 research candidates are disqualified or unsuitable.

### Methodology and quality
- Explain import → normalization → deduplication → website collection → extraction → validation → scoring → export.
- Exact weights: services 30, portfolio 25, billing 25, multiple properties 10, digital portal 10.
- Explain the 60% completeness gate and priority thresholds from config.yaml; render these from the export metadata to avoid drifting from the pipeline.
- Distinguish directory facts, website claims, AI interpretations and deterministic scores.
- State coverage limits: cached homepage AI analysis, existing rule-derived service-page evidence, nine failed extractions, 101 missing/unlisted homepages, unverified roles and no independent accuracy study.
- Include provenance, research timestamps and a downloadable methodology/validation summary. API usage/cost can appear as optional technical detail, not the main business story.

## Visual direction
- A calm research dashboard: warm off-white background, white content surfaces, dark navy typography and one restrained teal accent. Use amber for research gaps; every status also has a text label.
- A compact sidebar or top navigation, clear page titles, ample spacing, subtle borders, readable type and aligned numeric columns.
- Table-first information design. Avoid a decorative landing page that hides the companies, stock photography, excessive cards or animation.
- Use a text wordmark “Heidi Lead Intelligence”; do not invent official brand assets or imply that Heidi endorsed this independent assignment.
- English interface and original German company names/evidence. Preserve Unicode end-to-end. Check suspected encoding problems against JSON/source text before changing names; terminal rendering alone does not establish corrupted data.
- Keyboard-accessible filters and detail panels, visible focus states, sufficient contrast, semantic table headings and sensible mobile layout.

## Implementation architecture
- Create a new website subdirectory, leaving the Python pipeline and original outputs intact.
- Use buildless HTML/CSS/JavaScript and the supported private Sites hosting workflow to minimise dependencies and runtime cost.
- Export an allowlisted presentation dataset from validated JSON. Include only fields needed by the UI; publish company evidence with provenance, not full crawled documents or API attempt payloads.
- Derive counts, filters and priority views from the same dataset. Cross-check aggregate metrics with manifest.json and fail the export if they disagree.
- All 292 records can be searched, filtered and sorted in-browser. No database, account system, map service or live model calls are needed for the first version.
- Bundle the final Excel file as a download and bind the displayed update date to the manifest. Show export filename/date so the website and workbook can be reconciled.
- Never include .env, credentials, API keys, source caches or runtime logs in the frontend bundle. Original business contact details require the same verification labels; start with company-level information and keep private-reviewer access as the initial hosting audience.
- A repeatable export/build command refreshes the website after pipeline results change. User-edited website values must not silently override pipeline facts.

## Small, testable milestones
1. **Data preparation:** validate 292 unique IDs, reconcile 18/17/257 priority counts and 182/9/43/58 enrichment statuses, check Unicode, generate the allowlisted site dataset and download assets.
2. **Core browsing:** implement Overview, all-company list, priority view, search/filter/sort/pagination and shareable filter state. Acceptance: All displays 292 and priority filters display 18/17/257.
3. **Explainable company details:** render facts and exact evidence, score breakdown, unknowns, qualifiers and research statuses. Acceptance: sample records match validated JSON and every displayed claim links to its source.
4. **Methodology and polish:** render real scoring configuration, responsive layouts, accessible controls and working download. Acceptance: company details work on mobile/desktop and no fabricated claims appear.
5. **QA and delivery:** test filter combinations, empty results, direct links, panel keyboard behavior and workbook download; visually inspect overview/list/details. Inspect the production bundle for secrets and excluded files. Complete the supported private deployment and return its verified URL when a build is requested.

## Initial acceptance criteria
- All 292 companies are reachable and none disappear because enrichment failed.
- High/Medium/Needs Research counts reconcile to 18/17/257.
- Search, filters and sorting operate on real data and can be cleared.
- Company details distinguish unknown, observed false and observed true values.
- Scores and evidence completeness are labelled separately; unit qualifiers remain visible.
- Every evidence quote retains a source link and retrieval timestamp.
- Website/download data agree with the validated workbook.
- No new API charges are required to browse the site.
- Private reviewer access is the starting audience; public access is a separate user-directed decision.

## Recommended first version
Build the interactive results dashboard first: Overview, Companies, Priority Leads, company details and Methodology. Defer maps, lead editing, CRM features, live AI chat and scheduled crawls until the submission experience is complete.

## Implementation status
The first version is implemented in `website/heidi-leads`, with Priority Leads as the default landing view. The supported private Sites deployment is registered. Real-data export and interaction-logic tests pass. Browser preview was unavailable; see `reports/WEBSITE_QA.md` for verification coverage. Refresh data with `tools/export_website.py` and run `node website/heidi-leads/test.mjs`.
