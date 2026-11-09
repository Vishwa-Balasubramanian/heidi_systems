"""Read back every simple lead row and check against the validated JSON."""
import json
from pathlib import Path
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]


def main():
    data=json.loads((ROOT/'website/heidi-leads/dist/data.json').read_text(encoding='utf-8'))
    companies={c['company_name']:c for c in data['companies']}
    path=ROOT/'outputs/berlin_ai/Heidi_Berlin_AI.xlsx'
    wb=load_workbook(path,data_only=False)
    assert wb.sheetnames==['Priority Leads','All Companies','Sources & Methodology']
    for name,count in [('Priority Leads',35),('All Companies',292)]:
        sheet=wb[name]
        assert sheet.max_column==16 and sheet.max_row==count+7
        assert sheet.freeze_panes=='B8' and len(sheet.tables)==1
        for cells in sheet.iter_rows(min_row=8):
            row=[cell.value for cell in cells]
            c=companies[row[0]]
            assert row[1]==c['priority'] and row[2]==c['business_fit_score']
            assert abs(row[3]-c['evidence_completeness']/100)<0.000001
            assert row[4]==(c['managed_units'] if c['managed_units'] is not None else 'Not found')
            if name=='Priority Leads': assert c['priority'] in ('High Priority','Medium Priority')
            for contact in c['contacts']:
                for field,index in [('contact_name',9),('directory_email',10),('verified_professional_email',10),('telephone',11)]:
                    if contact.get(field): assert contact[field] in row[index]
            if not c['contacts']: assert row[9]=='No public contact found'
            for index,url in [(12,c['website']),(15,c['source_url'])]:
                if url and url.startswith(('http://','https://')):
                    assert cells[index].hyperlink.target==url and cells[index].value==url
        assert len(sheet.conditional_formatting)>0
    source=wb['Sources & Methodology']
    assert source.max_row==1004 and len(source.tables)==1
    assert all(row[3].hyperlink for row in source.iter_rows(min_row=17))
    assert not any(cell.data_type=='f' for sheet in wb for row in sheet for cell in row)
    assert not any('HYPERLINK is not implemented' in str(cell.value) for sheet in wb for row in sheet for cell in row)
    result={'tabs':wb.sheetnames,'companies_verified':292,'priority_leads_verified':35,'source_rows':988,'columns_in_main_sheets':16,'scores_unchanged':True,'contacts_preserved':True,'native_links_verified':True,'formula_errors':0}
    wb.close()
    (ROOT/'reports/SIMPLE_WORKBOOK_QA.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
