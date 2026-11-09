"""Revalidate all AI caches under current rules without making API calls."""
import hashlib
import json
import sys
import subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import yaml
from dotenv import load_dotenv
from src.ai import ai_extract
from src.models import Company
from src.sources import Fetcher
from src.scoring import score
from src.identity import read_rows
from src.export import export_workbook

load_dotenv()
cfg=yaml.safe_load(Path('config.yaml').read_text())
out=Path('outputs/berlin_ai')
manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
baseline=Path('outputs/heidi_berlin/leads.json')
assert hashlib.sha256(baseline.read_bytes()).hexdigest()==manifest['baseline_sha256']
companies=[Company.model_validate(x) for x in json.loads(baseline.read_text(encoding='utf-8')) if x['berlin_office']]
statuses={s['company_id']:s for s in manifest['statuses']}
evidence_count=0
rejected=[]
for c in companies:
    c.ai_enrichment_status=statuses[c.company_id]['status']
    c.ai_enrichment_error=statuses[c.company_id].get('error')
    if statuses[c.company_id]['status']=='AI completed':
        page=Fetcher(cfg,'snapshot').fetch(c.website)
        ai_extract(c,page,'snapshot')
    score(c,cfg)
    checkpoint=json.loads((out/'checkpoints'/(c.company_id+'.json')).read_text(encoding='utf-8'))['company']
    for field,old in checkpoint['evidence'].items():
        if old['extraction_method']=='openai-structured' and field not in c.evidence:
            rejected.append(dict(company_id=c.company_id,company_name=c.company_name,field=field,
                                 proposed_value=checkpoint[field],quote=old['quote'],
                                 reason='Does not meet final field definition; retained as unknown'))
    for field,e in c.evidence.items():
        page=json.loads((Path(cfg['cache'])/(e.content_hash+'.json')).read_text(encoding='utf-8'))
        assert e.quote in page['text'],(c.company_name,field)
        evidence_count+=1
companies.sort(key=lambda c:(-c.business_fit_score,c.normalized_name))
metrics=manifest['metrics']
for priority,key in [('High Priority','high_priority'),('Medium Priority','medium_priority'),('Needs Research','needs_research')]:
    metrics[key]=sum(c.priority==priority for c in companies)
metrics['published_unit_counts']=sum(c.managed_units is not None for c in companies)
metrics['field_evidence_validated']=evidence_count
metrics['ai_fields_accepted']=sum(e.extraction_method=='openai-structured' for c in companies for e in c.evidence.values())
metrics['ai_fields_removed_by_final_review']=len(rejected)
(out/'rejected_ai_fields.json').write_text(json.dumps(rejected,ensure_ascii=False,indent=2),encoding='utf-8')
manifest['validation_code_sha256']=hashlib.sha256(Path('src/ai.py').read_bytes()).hexdigest()
manifest['config_sha256']=hashlib.sha256(Path('config.yaml').read_bytes()).hexdigest()
(out/'leads.json').write_text(json.dumps([c.model_dump() for c in companies],ensure_ascii=False,indent=2),encoding='utf-8')
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
raw=[r for r in read_rows('data/raw/RAW_DIRECTORY.json') if r.get('Berlin address listed')=='Yes']
export_workbook(companies,raw,metrics,out/'Heidi_Berlin_AI.xlsx')
subprocess.run([sys.executable,'tools/refresh_simple_workbook.py'],check=True)
print(json.dumps(metrics,indent=2))
