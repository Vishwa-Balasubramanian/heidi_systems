"""Export only presentation fields; no API calls or credentials."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.website_contacts import public_contacts
OUT=ROOT/'website/heidi-leads/dist'


def main():
    leads=json.loads((ROOT/'outputs/berlin_ai/leads.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'outputs/berlin_ai/manifest.json').read_text(encoding='utf-8'))
    cfg=yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8'))
    snapshot=json.loads((ROOT/'data/raw/RAW_DIRECTORY.json').read_text(encoding='utf-8'))['values']
    original_rows=[dict(zip(snapshot[0],row)) for row in snapshot[1:]]
    raw_by_id={row['Raw ID']:row for row in original_rows}
    assert len(leads)==292 and len({c['company_id'] for c in leads})==292
    counts={p:sum(c['priority']==p for c in leads) for p in ('High Priority','Medium Priority','Needs Research')}
    for p,k in [('High Priority','high_priority'),('Medium Priority','medium_priority'),('Needs Research','needs_research')]:
        assert counts[p]==manifest['metrics'][k]
    for status,key in [('AI completed','ai_completed'),('AI failed','ai_failed'),('no saved homepage','no_saved_homepage'),('no listed website','no_listed_website')]:
        assert sum(c['ai_enrichment_status']==status for c in leads)==manifest['metrics'][key]
    fields=['company_id','company_name','website','domain','street_address','postal_code','city','berlin_office','Berlin_service_area','address_validation_notes','residential_management','weg_management','rental_management','commercial_management','managed_units','managed_units_qualifier','managed_buildings','heating_cost_billing_relevance','operating_cost_billing_relevance','digital_features','property_coverage','business_fit_score','score_upper_bound','evidence_completeness','priority','confidence','qualification_notes','website_status','ai_enrichment_status','source_url']
    companies=[]
    for c in leads:
        record={k:c.get(k) for k in fields}
        record['evidence']={f:{k:e.get(k) for k in ['source_url','quote','retrieved_at','extraction_method','model_name','prompt_version']} for f,e in c['evidence'].items()}
        record['contacts']=public_contacts(c,raw_by_id)
        companies.append(record)
    OUT.mkdir(parents=True,exist_ok=True)
    workbook=ROOT/'outputs/berlin_ai/Heidi_Berlin_AI.xlsx'
    data=dict(companies=companies,metrics=manifest['metrics'],date=manifest.get('finished_at'),
              scoring={k:cfg[k] for k in ['version','weights','portfolio_bands','min_completeness','high_threshold','medium_threshold']},
              workbook_sha256=hashlib.sha256(workbook.read_bytes()).hexdigest())
    (OUT/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    shutil.copy2(workbook,OUT/'Heidi_Berlin_AI.xlsx')
    shutil.copy2(ROOT/'reports/BERLIN_AI.md',OUT/'Methodology_and_validation.md')
    print(f'Exported {len(companies)} companies: {counts}')


if __name__=='__main__': main()
