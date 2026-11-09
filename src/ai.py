"""Optional OpenAI Responses extraction; no SDK required. Live calls are opt-in."""
import hashlib
import json
import os
import re
import time
from .ai_usage import estimate_cost, record_attempt
from pathlib import Path
from typing import Literal
import requests
from pydantic import BaseModel, ConfigDict, model_validator
from .models import Evidence

FIELDS = Literal['residential_management','weg_management','rental_management',
    'commercial_management','managed_units','managed_buildings','heating_cost_billing_relevance',
    'operating_cost_billing_relevance','digital_features','property_coverage','Berlin_service_area']


class Fact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    field: FIELDS
    boolean_value: bool | None
    count_value: int | None
    quote: str

    @model_validator(mode='after')
    def correct_type(self):
        if self.field in ('managed_units','managed_buildings'):
            if self.count_value is None or self.count_value < 0 or self.boolean_value is not None:
                raise ValueError('Count requires a nonnegative integer only')
        elif self.boolean_value is None or self.count_value is not None:
            raise ValueError('Boolean fact requires boolean only')
        return self


class Extraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    facts: list[Fact]


def validate_grounding(result, text):
    seen = set()
    for fact in result.facts:
        if fact.field in seen:
            raise ValueError(f'Duplicate field: {fact.field}')
        if len(fact.quote.strip()) < 12:
            raise ValueError(f'Quote too short: {fact.field}')
        if fact.quote not in text:
            raise ValueError(f'Quote not found verbatim: {fact.field}')
        seen.add(fact.field)
        if fact.count_value is not None:
            numbers = [int(x.replace('.','')) for x in re.findall(r'\b\d{1,3}(?:\.\d{3})+\b|\b\d+\b',fact.quote)]
            if fact.count_value not in numbers:
                raise ValueError('Count not present in supporting quote')
    return result


def meets_field_definition(fact):
    """Reject quote-backed claims that do not meet the scoring definition."""
    if fact.field in ('managed_units','managed_buildings'):
        # Static HTML often exposes animated counters as zero. Do not score those.
        if fact.count_value == 0 or re.search(r'bis zu|up to',fact.quote,re.I):
            return False
    if fact.field == 'managed_units':
        return bool(re.search(r'einheiten|wohnungen|units|apartments',fact.quote.replace('\u00ad',''),re.I))
    if fact.field == 'managed_buildings':
        return bool(re.search(r'gebäude|häuser|haeuser|objekte|liegenschaften|buildings',fact.quote,re.I))
    if fact.field == 'property_coverage' and fact.boolean_value is True:
        return bool(re.search(r'\b(?:[2-9]|\d{2,}|mehrere|zahlreiche)\s+(?:verwaltete\s+)?(?:gebäude|häuser|haeuser|objekte|liegenschaften|buildings)\b',fact.quote,re.I))
    if fact.boolean_value is True and fact.field == 'residential_management':
        return bool(re.search(r'wohn|residential',fact.quote,re.I))
    if fact.boolean_value is True and fact.field in ('operating_cost_billing_relevance','heating_cost_billing_relevance'):
        return bool(re.search(r'abrechnung|billing',fact.quote,re.I))
    if fact.boolean_value is True and fact.field == 'Berlin_service_area':
        return bool(re.search(r'\b(?:in|für|fuer|raum)\s+Berlin\b', fact.quote, re.I) and re.search(
            r'verwalt|betreu|tätig|taetig|servicegebiet|einzugsgebiet', fact.quote, re.I))
    if fact.boolean_value is True and fact.field == 'digital_features':
        return bool(re.search(r'portal|kundenlogin|kunden.log.?in|web.app|mieter.app|eigentümer.app', fact.quote, re.I))
    return True


def ai_extract(company, page, mode, cache_dir='data/raw/ai', audit_dir='reports/runs/ai_attempts'):
    model = os.environ.get('OPENAI_MODEL','').strip()
    if not model:
        raise ValueError('Set OPENAI_MODEL in .env')
    prompt = Path('prompts/extract-v1.txt').read_text(encoding='utf-8')
    source_text = page['text'][:20000]
    payload = dict(model=model,store=False,
        input=[{'role':'system','content':prompt},
               {'role':'user','content':json.dumps({'company_name':company.company_name,'source_url':page['source_url'],'text':source_text},ensure_ascii=False)}],
        text={'format':{'type':'json_schema','name':'company_facts','strict':True,'schema':Extraction.model_json_schema()}})
    key = hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    cache = Path(cache_dir); cache.mkdir(parents=True,exist_ok=True)
    path = cache/(key+'.json')
    response_model = model
    if path.exists():
        saved=json.loads(path.read_text(encoding='utf-8'))
        result=Extraction.model_validate(saved['extraction'])
        response_model=saved['model']
    elif mode == 'snapshot':
        raise FileNotFoundError('No cached AI extraction; snapshot mode forbids API calls')
    else:
        api_key=os.environ.get('OPENAI_API_KEY','').strip()
        if not api_key:
            raise ValueError('Set OPENAI_API_KEY in .env')
        for attempt in range(3):
            event = dict(company_id=company.company_id,model=model,cache_key=key,attempt=attempt+1,
                         usage=None,estimated_cost_usd=None,status='started')
            started=time.monotonic()
            retryable=True
            try:
                response=requests.post('https://api.openai.com/v1/responses',json=payload,
                    headers={'Authorization':'Bearer '+api_key},timeout=90)
                if response.status_code != 200:
                    event['http_status']=response.status_code
                    retryable=response.status_code in (408,429) or response.status_code>=500
                    raise RuntimeError(f'OpenAI HTTP {response.status_code}')
                data=response.json()
                event['usage']=data.get('usage')
                event['model']=data.get('model',model)
                event['estimated_cost_usd']=estimate_cost(event['model'],event['usage'])
                event['response_id']=data.get('id')
                if data.get('status') != 'completed':
                    raise ValueError('AI response incomplete')
                text=''.join(part['text'] for item in data.get('output',[]) for part in item.get('content',[]) if part.get('type')=='output_text')
                result=validate_grounding(Extraction.model_validate_json(text),source_text)
                response_model=data.get('model',model)
                path.write_text(json.dumps({'extraction':result.model_dump(),'model':response_model,'prompt_version':'extract-v1','usage':event['usage'],'estimated_cost_usd':event['estimated_cost_usd']},ensure_ascii=False),encoding='utf-8')
                event['status']='success'
                break
            except (ValueError, requests.RequestException, RuntimeError) as exc:
                event['status']='failed'
                # Validation exceptions can contain full model text: retain category only.
                event['error_type']=type(exc).__name__
                event['error_detail']=str(exc) if type(exc) in (ValueError,RuntimeError) else type(exc).__name__
                if attempt == 2 or not retryable:
                    raise RuntimeError(f"AI extraction failed after {attempt+1} attempts: {event['error_type']}: {event['error_detail']}") from None
            finally:
                event['elapsed_seconds']=round(time.monotonic()-started,3)
                record_attempt(event,audit_dir)
    validate_grounding(result,source_text)
    for fact in result.facts:
        if not meets_field_definition(fact):
            continue
        # Preserve independently extracted facts; disagreements need manual review.
        if fact.field in company.evidence:
            continue
        setattr(company,fact.field,fact.count_value if fact.count_value is not None else fact.boolean_value)
        if fact.field == 'managed_units':
            company.managed_units_qualifier = 'lower bound' if re.search(r'über|mehr als|\d\s*\+',fact.quote,re.I) else ('approximate' if re.search(r'rund|ca\.|circa|etwa',fact.quote,re.I) else 'published count')
        company.evidence[fact.field]=Evidence(source_url=page['source_url'],quote=fact.quote,
            retrieved_at=page['retrieved_at'],content_hash=page['content_hash'],
            extraction_method='openai-structured',model_name=response_model,prompt_version='extract-v1')
    company.model_name=response_model
    if company.managed_buildings is not None and company.managed_buildings>1 and 'managed_buildings' in company.evidence and 'property_coverage' not in company.evidence:
        company.property_coverage=True
        company.evidence['property_coverage']=company.evidence['managed_buildings'].model_copy()
    company.prompt_version='extract-v1'
    return company
