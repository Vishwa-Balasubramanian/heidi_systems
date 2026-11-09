# Heidi Lead Intelligence

Research and rank potential customers for Heidi's metering and billing services using public directory listings, saved company websites, optional OpenAI extraction and explainable scoring.

**Website:** https://heidi-berlin-lead-intelligence.vercel.app

## Start here

| What you need | File |
|---|---|
| Final, simplified Excel | [Heidi_Berlin_AI.xlsx](website/heidi-leads/dist/Heidi_Berlin_AI.xlsx) |
| Published company data and evidence | [data.json](website/heidi-leads/dist/data.json) |
| Latest Berlin research report | [BERLIN_AI.md](reports/BERLIN_AI.md) |
| Research and scoring explanation | [METHODOLOGY.md](METHODOLOGY.md) |
| Workbook verification | [SIMPLE_WORKBOOK_QA.json](reports/SIMPLE_WORKBOOK_QA.json) |

The final Excel has three tabs: **Priority Leads**, **All Companies**, and **Sources & Methodology**. It contains all 292 Berlin listings: 18 High Priority, 17 Medium Priority and 257 Needs Research. Contact names, emails and telephone numbers appear beside their companies and retain their verification labels.

This is a research snapshot from 9 November 2026, not a complete census of Berlin property managers. The original regional baseline contains 381 records; the final AI view uses its 292 directory-listed Berlin offices. Other cities need new source adapters and validation.

## How the project works

1. **Import** the existing VDIV Berlin–Brandenburg directory export from JSON, CSV or Excel.
2. **Prepare** records with schema validation, normalization and conservative duplicate checks.
3. **Research** company websites from saved snapshots or permitted live pages. Optional AI interprets homepage text.
4. **Validate** extracted facts against source quotes; keep missing facts unknown.
5. **Score** companies using the versioned rules in `config.yaml`.
6. **Present** the results in Excel and the static website. Browsing the website makes no AI calls.

The Google Sheet was captured as local snapshots. The application does not automatically read or overwrite the original sheet.

### The KPIs

| Evidence | Maximum points |
|---|---:|
| Residential, WEG or rental management | 30 |
| Published managed-unit portfolio | 25 |
| Heating-cost or operating-cost billing | 25 |
| Multiple managed buildings/properties | 10 |
| Customer, owner or tenant portal | 10 |

High Priority starts at 70 points and Medium Priority at 40. Ranked leads also need Berlin relevance, management-service evidence and at least 60% weighted evidence coverage. Otherwise they remain Needs Research. Unknown information does not mean a service is absent. Missing contacts do not reduce business-fit scores.

Scores indicate observed fit, not purchase probability. Published portfolio totals may include properties outside Berlin. Approximate and lower-bound figures retain their qualifiers. Exact thresholds and portfolio bands are in [config.yaml](config.yaml).

## Setup

Use Python 3.12 (the pipeline supports Python 3.11+) and Node.js for website tests and workbook presentation. Run commands from the project root in PowerShell.

```powershell
cd D:\heidi_systems
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

For optional live AI extraction, fill in the local `.env`:

```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_id
```

Never commit `.env` or credentials. No key is needed to browse the website, export existing results or replay cached research.

The published website dataset and simplified Excel are included in Git, so a fresh clone can serve the completed website immediately. Raw research snapshots, AI caches, checkpoints, detailed outputs and credentials are excluded. To rerun the research or regenerate the workbook on another computer, copy those required local inputs separately or import a directory export.

## Everyday use

### Check the project

```powershell
.\.venv\Scripts\python -B -m pytest -q -p no:cacheprovider
node website/heidi-leads/test.mjs
.\.venv\Scripts\python tools/verify_simple_workbook.py
```

The current Python suite has 49 tests. Workbook checks compare all 292 companies, priorities, scores, units, contacts and links against validated data.

### Open the website locally

```powershell
.\.venv\Scripts\python -m http.server 8765 --directory website/heidi-leads/dist
```

Open **http://localhost:8765**. Stop with `Ctrl+C`. The website needs no database, model API or package installation to run.

### Refresh Excel and the local website download

```powershell
.\.venv\Scripts\python tools/refresh_simple_workbook.py
```

This rebuilds the three-tab Excel, verifies it and updates the local website data/download using saved results. It does not publish the website or make model API calls. The earlier detailed Excel is preserved in `outputs/berlin_ai/backups/`.

The simplified workbook builder requires the supplied `@oai/artifact-tool` runtime through the existing `tools/node_modules` junction. That runtime is not installed by `requirements.txt`. Without it, the Python pipeline can still create its detailed workbook and the existing static website can still run.

To update only website data and copy the existing Excel:

```powershell
.\.venv\Scripts\python tools/export_website.py
```

### Publish to Vercel

```powershell
cd website\heidi-leads
npx.cmd --yes vercel@65.12.1 deploy --prod --yes
```

This requires your Vercel login and updates the linked production project. `dist/` is the published output; `.vercelignore` excludes development files and Sites metadata.

## Run or reproduce research

These commands change research outputs. Use separate output directories for experiments because the completed Berlin AI run depends on the preserved regional baseline and checks its hash.

### Baseline pipeline

```powershell
# Offline replay; no website or model API requests
.\.venv\Scripts\python main.py --city Berlin --mode snapshot --output outputs/replay

# Refresh permitted public websites; no AI unless --ai is supplied
.\.venv\Scripts\python main.py --city Berlin --mode live --output outputs/fresh_run

# Small AI pilot; uncached calls may incur charges
.\.venv\Scripts\python main.py --mode live --limit 5 --ai --output outputs/new_pilot
```

`--limit` limits enrichment, not import: all imported records remain in the output. Snapshot mode makes no network requests. Missing source/model caches are reported as failures or unknowns. Live mode observes robots policies and records source timestamps and failures.

The default baseline output is `outputs/heidi_berlin`. `--stage score` or `--stage export` reads existing `leads.json` from the selected output directory and refreshes scores/export. The baseline CLI produces the detailed six-tab research workbook; the final Berlin presentation is generated by the separate commands below.

### Import an existing directory export

```powershell
.\.venv\Scripts\python main.py --input data/raw/original.xlsx --mode snapshot --output outputs/imported
.\.venv\Scripts\python main.py --input data/raw/RAW_DIRECTORY.csv --mode live --output outputs/imported
```

Excel reads `RAW_DIRECTORY` when available, otherwise the first sheet. CSV must be UTF-8 and comma-separated. Required name header: `Company name (directory)` or `company_name`. Optional fields include `website`, `street_address`, `city`, `source_url`, `directory_email` and `contact_name`. Original directory headers are supported too. Automatic discovery of other cities or directories is not implemented.

### Berlin AI enrichment and finalization

```powershell
# Resume the Berlin homepage AI pass; new uncached calls may cost money
.\.venv\Scripts\python tools/enrich_berlin_ai.py

# Revalidate saved AI responses and regenerate Excel/website files offline
.\.venv\Scripts\python tools/finalize_berlin_ai.py

# Refresh usage summary and research report
.\.venv\Scripts\python tools/report_ai_usage.py --directory outputs/berlin_ai/api_attempts --output outputs/berlin_ai/usage.json
.\.venv\Scripts\python tools/report_berlin_ai.py
```

The AI job checkpoints every company, including failures. Re-running it does not automatically retry saved failed checkpoints. Finalization uses cached responses only and does not retry API failures. Run finalization after enrichment: enrichment first writes a detailed intermediate workbook, then finalization rebuilds the simple presentation.

Usage logs retain returned tokens and estimated cost for tracked attempts, including rejected responses. Earlier unlogged pilot calls are excluded; timeout billing can remain unknown. Cost estimates are not invoices.

## Project structure

```text
main.py                    Baseline import/research CLI
config.yaml                Source settings, limits and scoring rules
src/                       Models, imports, fetching, extraction, scoring, contacts
prompts/                   Versioned AI extraction prompt
tests/                     Synthetic and mocked tests
tools/                     Research, workbook, validation and website commands
data/raw/                  Original sheet snapshots, saved pages and AI caches
outputs/heidi_berlin/       Preserved 381-record regional baseline
outputs/berlin_ai/          Final 292-company data, Excel, checkpoints and usage
reports/                   Research findings, methodology and QA records
website/heidi-leads/        Static application, tests and Vercel configuration
```

The main tool workflow is `enrich_berlin_ai.py` → `finalize_berlin_ai.py` → `report_berlin_ai.py`. Workbook refresh uses `export_website.py` → `simplify_workbook.mjs` → `add_workbook_links.py` → `verify_simple_workbook.py`. Native hyperlinks are added to the XLSX package because the rendering runtime does not calculate HYPERLINK formulas.

The full project uses one Git repository at the root: https://github.com/Vishwa-Balasubramanian/heidi_systems . The former website-only Git history is archived locally outside the project. Local Vercel/Sites metadata, credentials and dependency folders are excluded from commits.

## Results and limitations

- 182 Berlin companies were AI-enriched; nine failed validation, 43 lacked saved homepages and 58 had no listed website.
- AI analysed saved homepages; rule evidence can also come from service pages.
- Contact names, roles and emails are directory-listed and unverified unless explicitly marked otherwise. No email addresses were guessed and no outreach was sent.
- Evidence traceability was checked; an independent human precision/recall study was not performed.
- Visual browser verification was unavailable. Workbook tabs were rendered and reviewed, and production file/data downloads were checked.

See [ARCHITECTURE.md](ARCHITECTURE.md), [METHODOLOGY.md](METHODOLOGY.md), [Berlin results](reports/BERLIN_AI.md), [workbook QA](reports/SIMPLE_WORKBOOK.md), and [website QA](reports/WEBSITE_QA.md). [PLAN.md](PLAN.md) and [WEBSITE_PLAN.md](WEBSITE_PLAN.md) retain the development/design plans. Historical statistics in `reports/VALIDATION.md` refer to the earlier regional rules-only run.

See [reports/CLEANUP.md](reports/CLEANUP.md) for removed files and recovery information.
