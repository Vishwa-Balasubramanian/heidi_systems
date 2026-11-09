import json
import re
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


def scalar(v):
    if v is None:
        return 'Unknown'
    if isinstance(v, (list, dict)):
        v = json.dumps(v, ensure_ascii=False)
    if isinstance(v, str):
        v = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', v)
    return v


def export_workbook(companies, raw, metrics, out):
    wb = Workbook()
    wb.remove(wb.active)
    def table(name, rows, headers=None):
        ws = wb.create_sheet(name)
        headers = headers or (list(rows[0]) if rows else ['Status'])
        ws.append([h.replace('_',' ').capitalize() for h in headers])
        for row in rows:
            ws.append([scalar(row.get(k)) for k in headers])
        for row in ws:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = 's'  # prevent formula injection from source text
                cell.font = Font(name='Arial', size=10)
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                if isinstance(cell.value, str) and cell.value.startswith(('https://','http://')) and len(cell.value) < 2000:
                    cell.hyperlink = cell.value
                    cell.font = Font(name='Arial', size=10, color='1765A3', underline='single')
        for cell in ws[1]:
            cell.fill = PatternFill('solid', fgColor='243A56')
            cell.font = Font(name='Arial', size=10, color='FFFFFF', bold=True)
        ws.row_dimensions[1].height = 42
        for i, header in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(i)].width = 44 if any(x in header for x in ('name','notes','quote','address','URL','url')) else 24
            if header in ('quote','qualification_notes'):
                ws.column_dimensions[get_column_letter(i)].width = 90
        for i in range(2, ws.max_row+1):
            import math
            lines = max((math.ceil(len(str(cell.value or '')) / max(12,ws.column_dimensions[cell.column_letter].width-3)) for cell in ws[i]),default=1)
            ws.row_dimensions[i].height = max(30,min(300,lines*13+6))
        ws.freeze_panes = 'C2' if len(headers) > 2 else 'A2'
        ws.auto_filter.ref = ws.dimensions
        ws.sheet_view.showGridLines = False
        return ws
    excluded = {'contacts','evidence'}
    leading = ['company_name','priority','business_fit_score','score_upper_bound','evidence_completeness','confidence','website','city','berlin_office','Berlin_service_area']
    rows = [{k:c.model_dump()[k] for k in leading + [f for f in type(c).model_fields if f not in excluded and f not in leading]} for c in companies]
    table('MASTER_LEADS', rows)
    table('PRIORITY_LEADS', [r for r in rows if r['priority'] in ('High Priority','Medium Priority')], list(rows[0]) if rows else None)
    contacts = [dict(company_id=c.company_id, company_name=c.company_name, **x.model_dump()) for c in companies for x in c.contacts]
    table('CONTACTS', contacts)
    evidence = [dict(company_id=c.company_id, field=field, value=getattr(c,field), **e.model_dump()) for c in companies for field,e in c.evidence.items()]
    # Keep imported directory rows alongside field evidence, preserving original columns.
    sources = [dict(source_kind='directory', **r) for r in raw] + [dict(source_kind='field evidence', **r) for r in evidence]
    headers = list(dict.fromkeys(k for r in sources for k in r))
    table('RAW_SOURCES', sources, headers)
    methodology = [dict(Topic='Score', Explanation='Observed lower-bound score, 0–100. Unknown facts earn no observed points; upper bound retains missing potential.'),
        dict(Topic='Completeness', Explanation='Sum of weights with usable evidence. Below 60 remains Needs Research.'),
        dict(Topic='Evidence', Explanation='Field quotes, URLs, timestamps and hashes in RAW_SOURCES; cached documents retained locally.'),
        dict(Topic='Contacts', Explanation='Directory contacts are not verified decision-makers. No email patterns inferred.'),
        dict(Topic='Limitations', Explanation='Rule extraction is conservative but can match editorial text. Manually review before outreach. Scores are static; rerun CLI after changes.'),
        dict(Topic='Coverage', Explanation='Berlin office and verified Berlin service area are separate. Regional records retained.'),
        dict(Topic='AI', Explanation='Optional AI candidates require review; baseline workbook uses deterministic rules.')]
    method_sheet = table('METHODOLOGY', methodology)
    method_sheet.column_dimensions['B'].width = 105
    for i in range(2,method_sheet.max_row+1):
        method_sheet.row_dimensions[i].height = 48
    qa = table('QA_DASHBOARD', [dict(Metric=k, Value=v) for k,v in metrics.items()])
    qa.column_dimensions['A'].width = 55
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    check = load_workbook(path, read_only=True)
    assert len(check.sheetnames) == 6 and check['MASTER_LEADS'].max_row == len(companies)+1
    check.close()
