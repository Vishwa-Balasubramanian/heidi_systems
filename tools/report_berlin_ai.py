import json
from pathlib import Path
from collections import Counter

out=Path('outputs/berlin_ai')
manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
records=json.loads((out/'leads.json').read_text(encoding='utf-8'))
baseline={r['company_id']:r for r in json.loads(Path('outputs/heidi_berlin/leads.json').read_text(encoding='utf-8'))}
metrics=manifest['metrics']
changed=sum(c['business_fit_score']!=baseline[c['company_id']]['business_fit_score'] for c in records)
errors=Counter(s['error'] for s in manifest['statuses'] if s['error'])
lines=['# Berlin AI enrichment report','',
       'Scope: 292 directory-listed Berlin offices. This is a separate output from the preserved 381-record regional baseline.',
       'Saved homepages were submitted to OpenAI; no additional website discovery or Google Sheet writes occurred.',
       'AI interprets homepage text only. Existing rule evidence from homepage and service pages is preserved.','',
       '## Measured results','', '| Metric | Result |','|---|---:|']
lines += [f'| {k} | {v} |' for k,v in metrics.items()]
lines += [f'| Scores changed from baseline | {changed} |','',
          '## Review and safeguards','',
          'All accepted evidence quotes were checked against saved page text. Cached AI responses were revalidated under the final field checks without further API calls.',
          'Review of extracted portfolio quotes identified tenant/owner counts incorrectly treated as units, static HTML counters showing zero, and generic plural wording incorrectly treated as multiple-building evidence. These cases are rejected by the final checks. Approximate and lower-bound unit figures retain qualifiers. Company-wide totals are not claimed to be Berlin-only totals.',
          'Address-only Berlin coverage, vague digital wording, general property management without residential wording, and cost optimisation without billing evidence are also rejected.',
          'These checks reduce observed errors but do not establish measured precision or recall. No independent human audit was conducted. Official ownership of every directory-linked website and contacts remain unverified.','',
          '## API cost and failures','',
          'Estimated costs cover tracked API attempts in this run, including responses rejected by validation. Previously cached pilot calls are excluded. Unknown costs, if present, are not treated as zero. Rates and token usage are retained in API attempt records; estimates are not invoices.',
          'Detailed usage: outputs/berlin_ai/usage.json. Failed or unavailable enrichment does not erase baseline facts.','']
lines += [f'- {count} × {error}' for error,count in errors.items()]
lines += ['', '## Reproduce offline','', '```powershell',
          '.\\.venv\\Scripts\\python tools/finalize_berlin_ai.py',
          '.\\.venv\\Scripts\\python tools/report_ai_usage.py --directory outputs/berlin_ai/api_attempts --output outputs/berlin_ai/usage.json',
          '.\\.venv\\Scripts\\python tools/report_berlin_ai.py',
          '```','', 'Keep baseline, raw page snapshots, AI cache, config, prompts and source together. Do not commit .env or credentials.']
Path('reports/BERLIN_AI.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'records':len(records),'changed_scores':changed,'metrics':metrics},indent=2))
