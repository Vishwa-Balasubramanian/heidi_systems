"""Join public directory contacts to companies by original record IDs."""
import re

FIELDS = ['contact_name','job_title','decision_maker_relevance','verified_professional_email',
          'directory_email','linkedin_url','contact_source','verification_status']


def public_contacts(company, raw_by_id):
    contacts=[{k:c.get(k) for k in FIELDS} for c in company.get('contacts',[])]
    for raw_id in company.get('raw_ids',[]):
        row=raw_by_id.get(raw_id,{})
        name=row.get('Directory contact (unverified role)') or None
        email=row.get('Directory email') or None
        telephone=row.get('Telephone (directory)') or None
        if not any((name,email,telephone)):
            continue
        match=next((c for c in contacts if (email and (c.get('directory_email') or '').casefold()==email.casefold())
                    or (name and (c.get('contact_name') or '').casefold()==name.casefold())),None)
        if match is None:
            match=dict.fromkeys(FIELDS)
            match.update(contact_name=name,directory_email=email,
                         verification_status='directory-listed; role unverified')
            contacts.append(match)
        match['telephone']=telephone
        match['email_classification']=row.get('Email classification') or None
        match['contact_source']=match.get('contact_source') or row.get('Original source URL')
        match['published_date']=row.get('Extracted on') or None
    return [c for c in contacts if any(c.get(k) for k in
            ['contact_name','directory_email','verified_professional_email','telephone','linkedin_url'])]
