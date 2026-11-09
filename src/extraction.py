import re
from .models import Evidence

PATTERNS = {
    'weg_management': r'\bWEG[ -]Verwaltung\b|\bWohnungseigentumsverwaltung\b',
    'rental_management': r'\bMietverwaltung\b|\bMietshausverwaltung\b|\bMiethausverwaltung\b',
    'residential_management': r'\bWohnimmobilienverwaltung\b|Verwaltung von Wohnimmobilien',
    'commercial_management': r'\bGewerbeverwaltung\b',
    'heating_cost_billing_relevance': r'\bHeizkostenabrechnung(?:en)?\b',
    'operating_cost_billing_relevance': r'\b(?:Betriebskosten|Nebenkosten)abrechnung(?:en)?\b',
    'digital_features': r'\b(?:Kundenportal|Eigentümerportal|Mieterportal)\b',
}


def extract(c, page):
    text = page['text']
    def evidence(quote):
        return Evidence(**{k: page[k] for k in ('source_url','retrieved_at','content_hash')}, quote=quote)
    for field, pattern in PATTERNS.items():
        if field in c.evidence:
            continue
        for m in re.finditer(pattern, text, re.I):
            quote = text[max(0, m.start()-100):m.end()+160]
            # Conservative rejection of negation and editorial contexts.
            if re.search(r'\b(kein\w*|nicht|früher|ehemalig|blog|nachrichten)\b', quote, re.I):
                continue
            if 'billing' in field and re.search(r'\b(FAQ|Fragen|gesetzlich)\b', quote, re.I):
                continue
            setattr(c, field, True)
            c.evidence[field] = evidence(quote)
            break
    # Portfolio figures need an explicit self-description and units, not dates or listings.
    pattern = r'(?:wir\s+verwalten|wir\s+betreuen|verwaltet\s+derzeit|betreuen\s+derzeit)\s+(?:(?:aktuell|derzeit|rund|über|ca\.?|mehr\s+als)\s+)*(\d{1,3}(?:\.\d{3})+|\d+)\s+(?:Wohn(?:ungs)?einheiten|Verwaltungseinheiten|Einheiten|Wohnungen)\b'
    m = re.search(pattern, text, re.I)
    if m and 'managed_units' not in c.evidence:
        c.managed_units = int(m[1].replace('.', ''))
        c.managed_units_qualifier = 'lower bound' if re.search(r'über|mehr als',m[0],re.I) else ('approximate' if re.search(r'rund|ca\.',m[0],re.I) else 'published count')
        c.evidence['managed_units'] = evidence(m[0])
    # Do not infer multiple buildings from multiple units.
    m = re.search(r'(?:wir verwalten|wir betreuen)\s+(?:rund\s+|über\s+)?(\d+)\s+(?:Gebäude|Mehrfamilienhäuser|Objekte)\b', text, re.I)
    if m and 'managed_buildings' not in c.evidence:
        c.managed_buildings = int(m[1])
        c.evidence['managed_buildings'] = evidence(m[0])
        c.property_coverage = c.managed_buildings > 1
        c.evidence['property_coverage'] = evidence(m[0])
    m = re.search(r'(?:verwalten|betreuen)[^.]{0,100}\bin Berlin\b', text, re.I)
    if m:
        c.Berlin_service_area = True
        c.evidence['Berlin_service_area'] = evidence(m[0])
    return c
