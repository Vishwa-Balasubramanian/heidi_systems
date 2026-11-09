import json
import pytest
from src.ai import Extraction, validate_grounding, ai_extract
from src.identity import import_company
from src.ai import Fact, meets_field_definition


@pytest.mark.parametrize('field,quote,accepted',[
    ('Berlin_service_area','Mittelstraße 49 10117 Berlin',False),
    ('Berlin_service_area','ABEGO Immobilienverwaltung GmbH Mittelstraße 49 10117 Berlin',False),
    ('Berlin_service_area','Wir verwalten Immobilien in Berlin',True),
    ('digital_features','Wir nutzen moderne digitale Lösungen',False),
    ('digital_features','Web-App für Mieter / Eigentümer',True),
    ('operating_cost_billing_relevance','Betriebskosten-Optimierung',False),
    ('operating_cost_billing_relevance','Erstellung von Betriebs- und Heizkostenabrechnungen',True),
    ('residential_management','Professionelle Verwaltung von Immobilien',False),
    ('residential_management','Verwaltung von Wohnimmobilien',True),
    ('property_coverage','Wir verwalten Immobilien in Berlin und Brandenburg',False),
    ('property_coverage','Unser Portfolio: 116 Liegenschaften',True),
])
def test_field_definitions(field,quote,accepted):
    fact=Fact(field=field,boolean_value=True,count_value=None,quote=quote)
    assert meets_field_definition(fact)==accepted


def test_reject_invented_quote():
    result=Extraction.model_validate({'facts':[{'field':'managed_units','boolean_value':None,'count_value':1000,'quote':'Wir verwalten 1000 Wohnungen.'}]})
    with pytest.raises(ValueError):
        validate_grounding(result,'Wir verwalten 100 Wohnungen.')


def test_reject_count_not_in_quote():
    quote='Wir verwalten 100 Wohnungen.'
    result=Extraction.model_validate({'facts':[{'field':'managed_units','boolean_value':None,'count_value':1000,'quote':quote}]})
    with pytest.raises(ValueError):
        validate_grounding(result,quote)


def test_bounded_malformed_retry(tmp_path,monkeypatch):
    calls=[]
    class Response:
        status_code=200
        def json(self):
            return {'status':'completed','output':[{'content':[{'type':'output_text','text':'not JSON'}]}]}
    monkeypatch.setenv('OPENAI_MODEL','test-model')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-key')
    def post(*a,**kw):
        calls.append(1); return Response()
    monkeypatch.setattr('requests.post',post)
    with pytest.raises(RuntimeError):
        ai_extract(import_company({'company_name':'Test'},1),{'text':'Synthetic example','source_url':'https://example.org'},'live',str(tmp_path),str(tmp_path/'audit'))
    assert len(calls)==3
    events=[json.loads(p.read_text()) for p in (tmp_path/'audit').glob('*.json')]
    assert len(events)==3 and all(e['error_type']=='ValidationError' for e in events)
    assert 'synthetic-test-key' not in json.dumps(events)


def test_cost_includes_cached_input_and_reasoning_output():
    from src.ai_usage import estimate_cost
    assert estimate_cost('gpt-5-mini',{'input_tokens':1000,'input_tokens_details':{'cached_tokens':400},'output_tokens':200}) == 0.00056
    assert estimate_cost('unknown-model',{'input_tokens':1000,'output_tokens':200}) is None
    assert estimate_cost('gpt-5-mini',None) is None


def test_auth_failure_not_retried(tmp_path,monkeypatch):
    class Response:
        status_code=401
    calls=[]
    monkeypatch.setenv('OPENAI_MODEL','gpt-5-mini')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-key')
    def post(*a,**kw):
        calls.append(1); return Response()
    monkeypatch.setattr('requests.post',post)
    with pytest.raises(RuntimeError,match='HTTP 401'):
        ai_extract(import_company({'company_name':'Test'},1),{'text':'Synthetic example','source_url':'https://example.org'},'live',str(tmp_path),str(tmp_path/'audit'))
    assert len(calls)==1


def test_usage_recorded_before_invalid_extraction(tmp_path,monkeypatch):
    class Response:
        status_code=200
        def json(self):
            return {'status':'completed','model':'gpt-5-mini','usage':{'input_tokens':1000,'output_tokens':200},'output':[]}
    monkeypatch.setenv('OPENAI_MODEL','gpt-5-mini')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-key')
    monkeypatch.setattr('requests.post',lambda *a,**kw:Response())
    with pytest.raises(RuntimeError):
        ai_extract(import_company({'company_name':'Test'},1),{'text':'Synthetic example','source_url':'https://example.org'},'live',str(tmp_path),str(tmp_path/'audit'))
    events=[json.loads(p.read_text()) for p in (tmp_path/'audit').glob('*.json')]
    assert len(events)==3 and all(e['estimated_cost_usd']==0.00065 for e in events)


def test_ai_snapshot_never_network(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL','test-model')
    monkeypatch.setattr('requests.post',lambda *a,**kw:pytest.fail('Network attempted'))
    with pytest.raises(FileNotFoundError):
        ai_extract(import_company({'company_name':'Test'},1),{'text':'Synthetic','source_url':'https://example.org'},'snapshot',str(tmp_path))


def test_success_cache_does_not_charge_again(tmp_path,monkeypatch):
    class Response:
        status_code=200
        def json(self):
            return {'status':'completed','model':'gpt-5-mini','usage':{'input_tokens':100,'output_tokens':20},
                    'output':[{'content':[{'type':'output_text','text':'{"facts":[]}'}]}]}
    calls=[]
    monkeypatch.setenv('OPENAI_MODEL','gpt-5-mini')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-key')
    def post(*a,**kw):
        calls.append(1); return Response()
    monkeypatch.setattr('requests.post',post)
    c=import_company({'company_name':'Test'},1)
    page={'text':'Synthetic example','source_url':'https://example.org'}
    ai_extract(c,page,'live',str(tmp_path),str(tmp_path/'audit'))
    ai_extract(c,page,'snapshot',str(tmp_path),str(tmp_path/'audit'))
    assert len(calls)==1 and len(list((tmp_path/'audit').glob('*.json')))==1


@pytest.mark.parametrize('count,quote,accepted',[
    (3500,'3500 Mieter & Eigentümer',False),
    (0,'0 verwaltete Einheiten',False),
    (1000,'Wir verwalten bis zu 1000 Einheiten',False),
    (1500,'Über 1.500 Wohn- und Gewerbeeinheiten',True),
])
def test_portfolio_semantics(count,quote,accepted):
    assert meets_field_definition(Fact(field='managed_units',boolean_value=None,count_value=count,quote=quote))==accepted
