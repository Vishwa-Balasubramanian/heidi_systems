def score(c, config):
    def observed(field):
        return getattr(c, field) if field in c.evidence else None
    def either(*fields):
        values = [observed(f) for f in fields]
        return True if True in values else (False if all(v is False for v in values) else None)
    groups = {
        'services': either('residential_management', 'weg_management', 'rental_management'),
        'portfolio': observed('managed_units'),
        'billing': either('heating_cost_billing_relevance', 'operating_cost_billing_relevance'),
        'coverage': observed('property_coverage'),
        'digital': observed('digital_features'),
    }
    total = known = 0
    notes = []
    for group, value in groups.items():
        weight = config['weights'][group]
        points = 0
        if value is not None:
            known += weight
            if group == 'portfolio':
                points = next(p for minimum, p in config['portfolio_bands'] if value >= minimum)
                points = round(points * weight / 25)
            else:
                points = weight if value else 0
        total += points
        notes.append(f'{group}: {points}/{weight}; ' + ('unknown' if value is None else f'observed {value}'))
    c.business_fit_score = total
    c.evidence_completeness = known
    c.score_upper_bound = total + 100 - known
    c.qualification_notes = notes
    c.confidence = 'Medium' if known >= config['min_completeness'] else 'Low'
    relevant = c.berlin_office or observed('Berlin_service_area') is True
    if observed('Berlin_service_area') is False and not c.berlin_office:
        c.priority = 'Excluded'
    elif not relevant or known < config['min_completeness'] or groups['services'] is not True:
        c.priority = 'Needs Research'
    elif total >= config['high_threshold']:
        c.priority = 'High Priority'
    elif total >= config['medium_threshold']:
        c.priority = 'Medium Priority'
    else:
        c.priority = 'Low Priority'
    c.contact_readiness_score = max((
        (40 if x.verified_professional_email else 0) +
        (40 if x.decision_maker_relevance is True and x.job_title else 0) +
        (20 if x.linkedin_url else 0) for x in c.contacts), default=0)
    return c
