"""Summarize observed attempts; unknown billing remains explicitly unknown."""
import json
import argparse
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--directory',default='reports/runs/ai_attempts')
parser.add_argument('--output',default='reports/AI_USAGE.json')
args=parser.parse_args()
events=[json.loads(p.read_text(encoding='utf-8')) for p in Path(args.directory).glob('*.json')]
priced=[e for e in events if e['estimated_cost_usd'] is not None]
summary={
    'scope':'Instrumented API attempts only; earlier pilot usage was not captured',
    'attempts':len(events),
    'successful_attempts':sum(e['status']=='success' for e in events),
    'failed_attempts':sum(e['status']=='failed' for e in events),
    'attempts_without_usage':sum(e['usage'] is None for e in events),
    'attempts_without_cost_estimate':len(events)-len(priced),
    'input_tokens_observed':sum((e['usage'] or {}).get('input_tokens',0) for e in events),
    'output_tokens_observed':sum((e['usage'] or {}).get('output_tokens',0) for e in events),
    'known_estimated_cost_usd':round(sum(e['estimated_cost_usd'] for e in priced),9) if priced else None,
    'complete_cost_estimate':bool(events) and len(events)==len(priced),
    'billing_note':'Standard token-price estimate, not an invoice. Timeout billing and earlier unlogged calls are unknown. Local cache hits make no API call.',
    'attempts_detail':events,
}
Path(args.output).write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='attempts_detail'},indent=2))
