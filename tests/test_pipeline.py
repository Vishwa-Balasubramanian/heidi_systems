import json
from argparse import Namespace
from pathlib import Path
import pytest
import yaml
from pydantic import ValidationError
from openpyxl import load_workbook
from src.models import Company, Evidence
from src.identity import import_company, deduplicate, normalize, read_rows
from src.extraction import extract
from src.sources import Fetcher, text_and_links
from src.scoring import score
from src.export import export_workbook
from main import enrich, run

CONFIG = yaml.safe_load(Path('config.yaml').read_text())


def company(name='Example GmbH', address='Teststr. 1 10115 Berlin', website='https://example.org'):
    return import_company({'company_name':name,'street_address':address,'website':website},1)


def page(text):
    return dict(text=text,source_url='https://example.org/services',retrieved_at='2026-11-09T10:00:00Z',content_hash='abc')


def fact(c, field, value):
    setattr(c,field,value)
    c.evidence[field] = Evidence(source_url='https://example.org',quote='Synthetic test evidence',retrieved_at='2026-11-09',content_hash='test')


def test_normalize_unicode():
    assert normalize('  ACME—GmbH! ') == normalize('acme gmbh')


def test_berlin_district_and_directory_typo():
    assert company(address='Test 1 12203 Berlin-Lichterfelde West').berlin_office
    c=import_company({'company_name':'Test','Listed address':'Test 1 123555 Berlin','Berlin address listed':'Yes'},1)
    assert c.berlin_office and c.postal_code is None and c.address_validation_notes


def test_dedup_preserves_entities():
    assert len(deduplicate([company(),company('Example GmbH!')])) == 1
    assert len(deduplicate([company(),company('Example AG')])) == 2
    assert len(deduplicate([company(),company('Other GmbH')])) == 2


def test_dedup_no_empty_identity_merge():
    assert len(deduplicate([company(address='',website=''),company(address='',website='')])) == 2


def test_schema():
    with pytest.raises(ValidationError):
        company().managed_units = -1
    with pytest.raises(ValueError):
        import_company({},1)


def test_missing_vs_false():
    c=company(); score(c,CONFIG)
    assert c.business_fit_score == 0 and c.score_upper_bound == 100
    assert c.priority == 'Needs Research' and c.evidence_completeness == 0
    fact(c,'digital_features',False); score(c,CONFIG)
    assert c.score_upper_bound == 90 and c.evidence_completeness == 10


@pytest.mark.parametrize('units,points',[(0,0),(1,5),(99,5),(100,10),(499,10),(500,18),(999,18),(1000,25)])
def test_portfolio_boundaries(units,points):
    c=company(); fact(c,'managed_units',units); score(c,CONFIG)
    assert c.business_fit_score == points


def test_priority_and_completeness():
    c=company(); fact(c,'weg_management',True); fact(c,'managed_units',1000)
    score(c,CONFIG); assert c.priority == 'Needs Research'
    fact(c,'heating_cost_billing_relevance',True); score(c,CONFIG)
    assert c.priority == 'High Priority' and c.business_fit_score == 80 and c.evidence_completeness == 80
    assert c.contact_readiness_score == 0


def test_unbacked_fact_not_scored():
    c=company(); c.weg_management=True; score(c,CONFIG)
    assert c.business_fit_score == 0


def test_outside_berlin_not_excluded_without_evidence():
    c=company(address='Test 1 14467 Potsdam'); score(c,CONFIG)
    assert c.Berlin_service_area is None and c.priority == 'Needs Research'


def test_extraction_quotes_and_negation():
    c=company(); p=page('Wir bieten WEG-Verwaltung. Wir verwalten rund 1.250 Wohneinheiten. Kundenportal für Eigentümer.')
    extract(c,p)
    assert c.managed_units == 1250 and c.weg_management is True
    assert all(e.quote in p['text'] for e in c.evidence.values())
    c=company(); extract(c,page('Wir bieten keine WEG-Verwaltung an.'))
    assert c.weg_management is None


def test_html_parser():
    text,links=text_and_links('<script>secret</script><p>WEG-Verwaltung</p><a href="/leistungen">Leistungen</a>','https://example.org')
    assert 'secret' not in text and links == ['https://example.org/leistungen']


def test_snapshot_never_network(tmp_path,monkeypatch):
    config={**CONFIG,'cache':str(tmp_path)}
    monkeypatch.setattr('requests.get',lambda *a,**kw:pytest.fail('network called'))
    with pytest.raises(FileNotFoundError):
        Fetcher(config,'snapshot').fetch('https://example.org')


def test_recovery(tmp_path):
    c,errors=enrich(company(),{**CONFIG,'cache':str(tmp_path)},'snapshot')
    assert errors and c.website_status.startswith('unavailable') and c.weg_management is None


def test_export_no_formula_injection(tmp_path):
    c=company('=HYPERLINK("bad")'); path=tmp_path/'test.xlsx'
    export_workbook([c],[{'name':'=1+1'}],{'count':1},path)
    wb=load_workbook(path)
    assert len(wb.sheetnames)==6 and wb['MASTER_LEADS'].freeze_panes=='C2'
    assert all(cell.data_type!='f' for ws in wb for row in ws for cell in row)
    wb.close()


def test_json_csv_import(tmp_path):
    path=tmp_path/'input.json'; path.write_text(json.dumps({'values':[['company_name'],['Example']]}))
    assert read_rows(path)==[{'company_name':'Example'}]
    path=tmp_path/'input.csv'; path.write_text('company_name\nExample\n')
    assert read_rows(path)==[{'company_name':'Example'}]


def test_end_to_end_failure_recovery(tmp_path):
    inp=tmp_path/'input.json'; inp.write_text(json.dumps([{'company_name':'Example'},{}]))
    cfg=tmp_path/'config.yaml'; cfg.write_text(yaml.safe_dump({**CONFIG,'cache':str(tmp_path/'cache')}))
    args=Namespace(config=str(cfg),city='Berlin',input=str(inp),output=str(tmp_path/'out'),stage='all',limit=None,mode='snapshot')
    metrics=run(args)
    assert metrics['raw_records']==2 and metrics['unique_companies']==1 and metrics['failures']==1
