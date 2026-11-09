"""Enrich the 292 directory-listed Berlin records from saved homepages.

No website refresh. Existing AI responses are reused; successful records are checkpointed.
"""
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
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


def main():
    load_dotenv()
    config=yaml.safe_load(Path('config.yaml').read_text())
    out=Path('outputs/berlin_ai'); out.mkdir(parents=True,exist_ok=True)
    checkpoints=out/'checkpoints'; checkpoints.mkdir(exist_ok=True)
    baseline=Path('outputs/heidi_berlin/leads.json')
    companies=[Company.model_validate(x) for x in json.loads(baseline.read_text(encoding='utf-8')) if x['berlin_office']]
    audit=out/'api_attempts'; started=datetime.now(timezone.utc).isoformat()

    def work(c):
        cp=checkpoints/(c.company_id+'.json')
        if cp.exists():
            saved=json.loads(cp.read_text(encoding='utf-8'))
            return Company.model_validate(saved['company']),saved['status'],saved.get('error')
        status='no listed website'; error=None
        if c.website:
            try:
                page=Fetcher(config,'snapshot').fetch(c.website)
                ai_extract(c,page,'live',audit_dir=str(audit))
                status='AI completed'
            except FileNotFoundError:
                status='no saved homepage'
            except Exception as exc:
                status='AI failed'; error=str(exc)[:500]
        score(c,config)
        cp.write_text(json.dumps(dict(company=c.model_dump(),status=status,error=error),ensure_ascii=False),encoding='utf-8')
        return c,status,error

    statuses=[]; results=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(work,c) for c in companies]
        for i,future in enumerate(as_completed(futures),1):
            c,status,error=future.result(); results.append(c)
            statuses.append(dict(company_id=c.company_id,company_name=c.company_name,status=status,error=error))
            if i%10==0 or i==len(companies):
                progress=dict(completed=i,total=len(companies),ai_completed=sum(s['status']=='AI completed' for s in statuses),
                              ai_failed=sum(s['status']=='AI failed' for s in statuses))
                (out/'progress.json').write_text(json.dumps(progress),encoding='utf-8')
                print(json.dumps(progress),flush=True)
    results.sort(key=lambda c:(-c.business_fit_score,c.normalized_name))
    metrics=dict(companies=len(results),ai_completed=sum(s['status']=='AI completed' for s in statuses),
                 ai_failed=sum(s['status']=='AI failed' for s in statuses),
                 no_saved_homepage=sum(s['status']=='no saved homepage' for s in statuses),
                 no_listed_website=sum(s['status']=='no listed website' for s in statuses),
                 high_priority=sum(c.priority=='High Priority' for c in results),
                 medium_priority=sum(c.priority=='Medium Priority' for c in results),
                 needs_research=sum(c.priority=='Needs Research' for c in results))
    events=[json.loads(p.read_text()) for p in audit.glob('*.json')]
    priced=[e for e in events if e.get('estimated_cost_usd') is not None]
    metrics.update(api_attempts=len(events),attempts_without_cost=len(events)-len(priced),
                   estimated_tracked_cost_usd=round(sum(e['estimated_cost_usd'] for e in priced),9))
    (out/'leads.json').write_text(json.dumps([c.model_dump() for c in results],ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=dict(started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),
                  baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                  scope='Directory-listed Berlin offices; saved homepage AI + preserved baseline evidence',
                  metrics=metrics,statuses=statuses)
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    raw=[r for r in read_rows('data/raw/RAW_DIRECTORY.json') if r.get('Berlin address listed')=='Yes']
    export_workbook(results,raw,metrics,out/'Heidi_Berlin_AI.xlsx')
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':
    main()
