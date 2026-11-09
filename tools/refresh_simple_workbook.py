"""Refresh the simple workbook and website download offline."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'outputs/berlin_ai/Heidi_Berlin_AI.xlsx'
backup=ROOT/'outputs/berlin_ai/backups/Heidi_Berlin_AI_detailed.xlsx'
if not backup.exists():
    backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(target,backup)
for command in [
    [sys.executable,'tools/export_website.py'],
    ['node','tools/simplify_workbook.mjs'],
    [sys.executable,'tools/add_workbook_links.py'],
    [sys.executable,'tools/verify_simple_workbook.py'],
    [sys.executable,'tools/export_website.py'],
]:
    subprocess.run(command,cwd=ROOT,check=True)
