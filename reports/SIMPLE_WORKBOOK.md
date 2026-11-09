# Simple workbook redesign

The current `outputs/berlin_ai/Heidi_Berlin_AI.xlsx` replaces the detailed six-tab presentation with three tabs:

- **Priority Leads:** 35 companies, comprising 18 High Priority and 17 Medium Priority.
- **All Companies:** all 292 directory-listed Berlin companies.
- **Sources & Methodology:** plain-language KPI definitions and 988 source rows, including 696 accepted field evidence records and 292 directory citations.

The main sheets use 16 columns: Company Name, Priority, Customer Fit Score /100, Evidence Coverage %, Managed Units, Residential Management, Billing Services, Multiple Properties, Digital Portal, Contact Person, Email, Phone, Website, Berlin Address, Contact Verification and Source Link. Technical identifiers, model names, prompt versions and JSON arrays are excluded from the main presentation.

Scores, priorities and underlying facts were not recalculated. Yes/No/Not found labels distinguish observed information from missing research. Unit figures remain numeric and retain Over/approximate display qualifiers. Contact names, public directory emails and telephone numbers are beside their companies, with verification labels. All quotes remain in their original language.

Verification compared every main-sheet row with validated JSON and contact exports. Filters, numeric percentages, numeric portfolio figures, frozen headers/company names, conditional priority formatting and 1,584 native source/website hyperlinks were checked. All three tabs and representative contact/evidence ranges were rendered and visually reviewed. The renderer does not implement the HYPERLINK formula, so literal URL values and native OOXML hyperlink relationships are used instead. No formulas or formula errors remain. Excel desktop was not launched.

The original detailed workbook was retained at `outputs/berlin_ai/backups/Heidi_Berlin_AI_detailed.xlsx`; raw sources, model caches and processed records remain intact. The website download is refreshed from the new workbook without additional AI calls.

Reproduce using `python tools/refresh_simple_workbook.py` in the configured runtime. Exact readback results are in `reports/SIMPLE_WORKBOOK_QA.json`.
