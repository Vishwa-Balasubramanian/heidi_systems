# Workspace cleanup

## Removed from the working folders
Removed 54 obsolete/generated files across 22 paths, approximately 6.2 MiB:

- Superseded five-company pilot output directory and pilot-only reports.
- One-off pilot retry/comparison scripts.
- The old six-tab screenshot helper and obsolete baseline replay helper. The latter rewrote the preserved baseline, so it is not part of the current usage workflow.
- Old console transcripts and a superseded submission brief describing earlier results.
- Generated workbook preview images, hyperlink-render intermediates and inspection output. The current workbook builder recreates these when needed.
- The already-published Sites deployment archive.
- Python bytecode, pytest cache and an accidentally created empty tools output directory.

The main README was rewritten. Ignore rules now also cover environment variants, deployment-local metadata, preview directories, console transcripts and workbook inspection output. Architecture documentation now distinguishes the original detailed export from the final three-tab presentation.

## Preserved
Original directory snapshots, saved HTML/text sources, cached AI responses, the 381-record baseline, final 292-company records, final Excel, detailed workbook backup, checkpoints, API usage/audit logs, final reports, all current application code/tests, website assets, Vercel configuration, runtime dependencies and `.env` remain in place. No API requests or deployments were made during cleanup.

## Recovery
The removed files were moved to a recovery folder outside the project rather than permanently erased:

`D:\heidi_systems-cleanup-backups\cleanup-20261109`

`manifest.json` lists each removed path, file count and size. Original relative paths are preserved in the recovery folder. `README.before-cleanup.md` contains the previous README. To restore a file, copy its matching relative path back into `D:\heidi_systems` after checking for an existing replacement.

## Validation
After cleanup: 49 Python tests passed; website data/filter/contact tests passed; all 292 workbook records and 35 priority records passed readback verification. CLI help, JavaScript syntax and remaining local references were checked. The workspace root is not a Git repository; the existing nested website repository and its user changes were retained.

## Subsequent GitHub setup
For the user's requested GitHub push, the project root was initialised as one repository. The former website-only `.git` directory was archived at `D:\heidi_systems-cleanup-backups\github-push-20261109\website.git`; website source files and current edits were retained. The destination is `Vishwa-Balasubramanian/heidi_systems`. Credentials and machine-specific hosting metadata are excluded; the already-public website dataset and workbook are included with the website source.
