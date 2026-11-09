import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from openpyxl import load_workbook
from .models import Company, Contact


def normalize(value):
    return re.sub(r'[^\w]+', ' ', unicodedata.normalize('NFKC', value).casefold()).strip()


def domain(url):
    host = urlsplit(url if '://' in url else 'https://' + url).hostname or ''
    return host.lower().removeprefix('www.')


def read_rows(path):
    path = Path(path)
    if path.suffix.lower() == '.json':
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(data, list):
            return data
        values = data['values']
        return [dict(zip(values[0], row)) for row in values[1:] if any(row)]
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))
    if path.suffix.lower() == '.xlsx':
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb['RAW_DIRECTORY'] if 'RAW_DIRECTORY' in wb.sheetnames else wb.active
        rows = list(ws.values)
        wb.close()
        return [dict(zip(rows[0], row)) for row in rows[1:] if any(row)]
    raise ValueError('Input must be JSON, CSV or XLSX')


def import_company(row, index):
    def get(*names):
        for name in names:
            v = row.get(name)
            if v is not None and str(v).strip():
                return str(v).strip()
        return None
    name = get('Company name (directory)', 'company_name')
    if not name:
        raise ValueError('Missing company name')
    address = get('Listed address', 'street_address')
    website = get('Website (directory)', 'website')
    if website and not website.startswith(('https://', 'http://')):
        website = 'https://' + website
    match = re.search(r'\b(\d{5})\s+(.+)', address or '')
    city = match[2].split(',')[0].strip() if match else get('city')
    if city and re.match(r'^Berlin\b',city,re.I):
        city = 'Berlin'
    listed_berlin = get('Berlin address listed')
    berlin_office = listed_berlin == 'Yes' if listed_berlin else (city or '').casefold() == 'berlin'
    address_note = None
    if berlin_office and (not match or city != 'Berlin'):
        address_note = 'Directory marks Berlin; address/postcode needs manual correction'
    source = get('Original source URL', 'source_url') or 'import:unknown'
    key = normalize(name) + '|' + normalize(address or '') + '|' + domain(website or '')
    if not address and not website:
        key += '|' + (get('Raw ID') or str(index))
    c = Company(company_id=hashlib.sha256(key.encode()).hexdigest()[:16], company_name=name,
        normalized_name=normalize(name), raw_ids=[get('Raw ID') or f'ROW-{index}'],
        street_address=address, postal_code=match[1] if match else None, city=city,
        berlin_office=berlin_office, address_validation_notes=address_note, website=website,
        domain=domain(website) if website else None, source_url=source,
        retrieved_at=get('Extracted on', 'retrieved_at'))
    person = get('Directory contact (unverified role)', 'contact_name')
    email = get('Directory email', 'directory_email')
    if person or email:
        c.contacts.append(Contact(contact_name=person, directory_email=email, contact_source=source))
    return c


def deduplicate(companies):
    result = []
    for c in companies:
        # Never merge on domain alone or remove legal-form distinctions.
        same = next((x for x in result if x.normalized_name == c.normalized_name
            and ((x.domain and x.domain == c.domain) or
                 (x.street_address and normalize(x.street_address) == normalize(c.street_address or '')))), None)
        if same:
            same.raw_ids = sorted(set(same.raw_ids + c.raw_ids))
            same.contacts.extend(x for x in c.contacts if x not in same.contacts)
            same.berlin_office = same.berlin_office or c.berlin_office
        else:
            result.append(c)
    return result
