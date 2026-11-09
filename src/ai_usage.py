"""Append-only per-attempt audit. Never records keys, headers or source text."""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

LOCK = threading.Lock()
PRICING_SOURCE = 'https://developers.openai.com/api/docs/models/gpt-5-mini'


def estimate_cost(model, usage):
    if model not in ('gpt-5-mini','gpt-5-mini-2025-08-07') or not usage:
        return None
    if 'input_tokens' not in usage or 'output_tokens' not in usage:
        return None
    cached = (usage.get('input_tokens_details') or {}).get('cached_tokens',0)
    return round(((usage['input_tokens']-cached)*0.25 + cached*0.025 + usage['output_tokens']*2)/1_000_000,9)


def record_attempt(event, directory):
    event = dict(timestamp=datetime.now(timezone.utc).isoformat(),pricing_source=PRICING_SOURCE,
                 pricing_checked='2026-11-09',**event)
    path=Path(directory); path.mkdir(parents=True,exist_ok=True)
    # Unique files avoid interleaved concurrent JSONL writes and overwritten attempts.
    with LOCK:
        (path/(uuid4().hex+'.json')).write_text(json.dumps(event,indent=2),encoding='utf-8')
