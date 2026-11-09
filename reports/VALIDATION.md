# Validation report

Run reviewed on 9 November 2026. Real input: the existing Google Sheet RAW_DIRECTORY tab. The original five tabs were preserved as local JSON snapshots; the Google Sheet was not edited.

## Measured coverage
| Measure | Count |
|---|---:|
| Imported raw records | 381 |
| Unique records after conservative deduplication | 381 |
| Directory-listed Berlin offices | 292 |
| Berlin candidates including explicit outside-office coverage | 294 |
| Accessible company websites | 253 |
| Records without a listed website | 79 |
| Companies with extracted residential/WEG/rental service signals | 175 |
| Published managed-unit figures | 4 |
| High Priority | 2 |
| Medium Priority | 15 |
| Needs Research | 364 |
| Verified decision-makers | 0 |
| Address records flagged for correction | 3 |
| Saved HTML documents | 685 |
| Missing-page events in offline replay | 54 |

The 54 events include missing subpages as well as unavailable homepages, so they are not 54 distinct companies. Original live error details are preserved in the first complete live run manifest under reports/runs/. Snapshot failures mean no saved page exists; they do not describe the original HTTP cause.

## Missing qualification data
| Field | Unknown records |
|---|---:|
| WEG management | 226 |
| Rental management | 246 |
| Explicit residential-management phrase | 378 |
| Managed units | 377 |
| Heating billing relevance | 359 |
| Operating-cost billing relevance | 299 |
| Digital portal | 339 |
| Multiple-building portfolio evidence | 381 |

These are missing observations, not confirmed negatives. Residential suitability can be supported by WEG or rental evidence even when the narrower residential phrase is absent. The current conservative regex does not capture many differently worded portfolio statements.

## Tests and readback
28 synthetic pytest cases passed. Coverage includes normalization, entity protection, schemas, missing facts, scoring boundaries, priority/completeness, HTML parsing, quote preservation, offline-only fetching, row/page failures, CSV/JSON input, XLSX structure, formula-injection prevention, and AI validation/retries. Tests use synthetic business fixtures and mocked API calls.

The workbook was reopened with openpyxl. All six sheets were rendered with Artifact Tool and visually reviewed; headers, first rows, source links, panes, filters and methodology layout were checked. Excel desktop was not launched; native Excel behavior is not claimed. Scores are static exports, refreshed through the CLI.

The original replay check compared leads.json byte-for-byte across offline runs, checked every evidence quote against stored page text, and verified source HTML SHA-256 hashes. Its measured result remains in `reports/replay_validation.json`. The original `tools/validate_run.py` helper was archived during cleanup because it rewrote the preserved baseline. For current presentation checks, use `tools/verify_simple_workbook.py`; for evidence revalidation, use the documented finalizer.

## Assistant-assisted source audit
Sample selected before final scoring: source rows 1, 2, 3, 11, 21, 31, 41, 51, 61, 71, 81, 91, 101, 111, 121, 131, 141, 151, 161, 171. This is a 20-record systematic convenience sample from the early alphabetic section, not a random accuracy study. Fourteen had cached homepages; three had no listed website and three had no saved homepage. The reviewer inspected names, source URLs, extracted contextual quotes and missing fields. This was assistant review, not independent human adjudication.

- 1A Hausverwaltung, Alma, Baurag, HAIM-Service and Fiedler: service navigation or explicit descriptions supported WEG/rental signals. The sample exposed a missing `Mietshausverwaltung` spelling; the rule was expanded and replayed.
- ABEGO: explicit residential-management service description supported the residential signal.
- Braun & Hubertus: an annual billing service statement supported operating-cost relevance.
- Artur Caesar Behrendt: billing terms appeared in an FAQ. The rule was tightened to reject nearby FAQ/legal-explanation wording before final scoring.
- EURIX: heating-billing framework agreements support relevance; they do not establish in-house meter provision or an existing Heidi relationship.
- Aadaktio, CPC, Gawehn and Grundmann: no qualifying homepage match was retained. This does not establish absence of services; Grundmann's directory entry illustrates why membership alone is not a fit criterion.
- Hausverwaltung Westbrandenburg: a WEG service signal is present, but the current Berlin-area regex can miss coverage stated in a title. This is a known recall limitation.
- Berliner Gesellschaft für Vermögensverwaltung, cg Hausverwaltung and Dominus-Casa: no cached homepage; no service facts invented.
- C&L, Langdon and HHV: no listed website; retained for further research.

Additional targeted review covered all four published-count records. Construction publishes over 10,000 units; M. Mende publishes over 3,000; ZenEstate publishes around 1,000; Manfred Wöller publishes around 400. Qualifiers are retained. These are total published management units, not independently verified apartment counts. Construction and M. Mende each score 80 from service, portfolio and operating-cost evidence. ZenEstate's statement about more than 30 properties is currently missed by the narrow building-count rule; no coverage points were invented.

Address investigation examined all seven discrepancies between a naive exact-city parse and the 292 directory flags: four were district/branch formatting, one had `Berllin`, and two had malformed postal codes. Original text remains unchanged. The three questionable addresses are flagged instead of silently corrected.

## Remaining limitations
No extraction precision/recall metric has been measured. Full legal-entity ownership verification of redirected websites is incomplete. Automatic phrase matches can be contextual false positives. Only three pages per website were attempted. Additional directory discovery, independently researched contact roles and Google Sheets write synchronization are not implemented. Optional OpenAI extraction is mocked-test validated but has not made a live authenticated call. The supplied key/provider still needs local configuration.
