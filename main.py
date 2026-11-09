import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import yaml
from dotenv import load_dotenv
from src.identity import read_rows, import_company, deduplicate
from src.models import Company
from src.sources import Fetcher
from src.extraction import extract
from src.scoring import score
from src.export import export_workbook


def enrich(c, config, mode):
    errors = []
    if not c.website:
        c.website_status = 'no listed website'
        return c, errors
    fetcher = Fetcher(config, mode)
    try:
        first = fetcher.fetch(c.website)
        c.website_status = 'accessible; directory-linked identity'
        extract(c, first)
        if config.get('use_ai'):
            from src.ai import ai_extract
            try:
                ai_extract(c, first, mode)
            except Exception as exc:
                errors.append(dict(company_id=c.company_id, error='AIExtractionError', detail=str(exc)[:200]))
        for url in first['links'][:config['max_pages']-1]:
            try:
                extract(c, fetcher.fetch(url))
            except Exception as exc:
                errors.append(dict(company_id=c.company_id, url=url, error=type(exc).__name__, detail=str(exc)[:200]))
    except Exception as exc:
        c.website_status = 'unavailable: ' + type(exc).__name__
        errors.append(dict(company_id=c.company_id, url=c.website, error=type(exc).__name__, detail=str(exc)[:200]))
    return c, errors


def run(args):
    load_dotenv()
    config = yaml.safe_load(Path(args.config).read_text(encoding='utf-8'))
    config['use_ai'] = getattr(args, 'ai', False)
    if args.city != config['city']:
        raise ValueError('Configure and implement a source for this city; Berlin is the current adapter')
    if sum(config['weights'].values()) != 100:
        raise ValueError('Weights must sum to 100')
    out = Path(args.output or config['output'])
    out.mkdir(parents=True, exist_ok=True)
    input_path = Path(args.input or config['input'])
    raw = read_rows(input_path)
    failures = []
    if args.stage in ('score','export'):
        companies = [Company.model_validate(x) for x in json.loads((out/'leads.json').read_text(encoding='utf-8'))]
        if (out/'manifest.json').exists():
            failures = json.loads((out/'manifest.json').read_text(encoding='utf-8')).get('failures',[])
    else:
        companies = []
        for i,row in enumerate(raw,1):
            try:
                companies.append(import_company(row,i))
            except Exception as exc:
                failures.append(dict(row=i, error=type(exc).__name__, detail=str(exc)))
        companies = deduplicate(companies)
        selected = companies[:args.limit] if args.limit else companies
        with ThreadPoolExecutor(max_workers=config['workers']) as pool:
            futures = [pool.submit(enrich,c,config,args.mode) for c in selected]
            for i,future in enumerate(as_completed(futures),1):
                _, errors = future.result()
                failures.extend(errors)
                if i % 25 == 0:
                    print(f'Enriched {i}/{len(selected)}', flush=True)
    for c in companies:
        score(c, config)
    companies.sort(key=lambda c:(-c.business_fit_score,c.normalized_name,c.company_id))
    fields = ['weg_management','rental_management','residential_management','managed_units',
              'heating_cost_billing_relevance','operating_cost_billing_relevance','digital_features','property_coverage']
    metrics = dict(raw_records=len(raw), unique_companies=len(companies),
        berlin_office=sum(c.berlin_office for c in companies),
        berlin_relevant_candidates=sum(c.berlin_office or c.Berlin_service_area is True for c in companies),
        accessible_websites=sum(c.website_status.startswith('accessible') for c in companies),
        verified_service_signals=sum(any(getattr(c,f) is True for f in fields[:3]) for c in companies),
        published_unit_counts=sum(c.managed_units is not None for c in companies),
        high_priority=sum(c.priority=='High Priority' for c in companies),
        medium_priority=sum(c.priority=='Medium Priority' for c in companies),
        needs_research=sum(c.priority=='Needs Research' for c in companies),
        verified_decision_makers=sum(x.decision_maker_relevance is True for c in companies for x in c.contacts),
        failures=len(failures))
    metrics.update({f'missing_{f}':sum(getattr(c,f) is None for c in companies) for f in fields})
    payload = json.dumps([c.model_dump() for c in companies], ensure_ascii=False, indent=2)
    (out/'leads.json').write_text(payload, encoding='utf-8')
    manifest = dict(run_at=datetime.now(timezone.utc).isoformat(), mode=args.mode,stage=args.stage,
        input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
        config_sha256=hashlib.sha256(Path(args.config).read_bytes()).hexdigest(),
        result_sha256=hashlib.sha256(payload.encode()).hexdigest(), metrics=metrics, failures=failures)
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    runs = Path('reports/runs'); runs.mkdir(parents=True,exist_ok=True)
    (runs/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    export_workbook(companies, raw, metrics, out/'Heidi_Berlin_Leads.xlsx')
    print(json.dumps(metrics,indent=2))
    return metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evidence-backed Berlin lead intelligence')
    parser.add_argument('--city',default='Berlin')
    parser.add_argument('--mode',choices=['snapshot','live'],default='snapshot')
    parser.add_argument('--stage',choices=['all','score','export'],default='all')
    parser.add_argument('--source',choices=['import'],default='import')
    parser.add_argument('--input')
    parser.add_argument('--output')
    parser.add_argument('--config',default='config.yaml')
    parser.add_argument('--limit',type=int,help='Limit website enrichment only; preserve all imported records')
    parser.add_argument('--ai',action='store_true',help='Opt in to OpenAI extraction (requires model/key; snapshot uses cached responses only)')
    run(parser.parse_args())
