# Heidi Lead Intelligence website

Priority Leads is the default page. The static application includes all 292 companies, search, service/status filters, sorting, pagination, source evidence details, research overview, scoring methodology and workbook/report downloads.

No AI calls, database, package installation or build step is needed to browse it. Private Sites hosting is configured in `.openai/hosting.json`.

Vercel production: https://heidi-berlin-lead-intelligence.vercel.app . Static output is configured in `vercel.json`; `.vercelignore` excludes Sites metadata and development files. To publish subsequent changes from this directory, run `npx vercel@65.12.1 deploy --prod --yes` with the existing Vercel account login.

Refresh the presentation data from the repository root:
```powershell
.\.venv\Scripts\python tools/export_website.py
node website/heidi-leads/test.mjs
.\.venv\Scripts\python -m http.server 8765 --directory website/heidi-leads/dist
```
Open http://localhost:8765 . Query parameters preserve view, filters, page and stable company ID. The source exporter allowlists presentation fields, validates counts against the manifest and copies the final workbook. Raw HTML, API logs and credentials are excluded.

Validation: real-data count/identity, priority views, empty and case-insensitive search, combined filters, missing-value sort, status totals, download presence and JavaScript syntax checks. The local HTTP server returned 200. Browser preview was unavailable in the current tool session, so visual layout and keyboard interactions have not been browser-verified.
