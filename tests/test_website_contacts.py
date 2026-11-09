from src.website_contacts import public_contacts


def test_contact_join_uses_record_id_and_preserves_email_phone():
    c={'raw_ids':['A'],'contacts':[{'contact_name':'Example','directory_email':'person@example.org'}]}
    raw={'A':{'Directory email':'person@example.org','Telephone (directory)':'030/123456','Original source URL':'https://example.org/directory'},
         'B':{'Directory email':'other@other.org','Telephone (directory)':'999999'}}
    result=public_contacts(c,raw)
    assert len(result)==1 and result[0]['telephone']=='030/123456'
    assert result[0]['directory_email']=='person@example.org'
    assert result[0]['verified_professional_email'] is None
    assert '999999' not in str(result)


def test_phone_only_contact_and_empty_company():
    result=public_contacts({'raw_ids':['A'],'contacts':[]},{'A':{'Telephone (directory)':'03012345'}})
    assert len(result)==1 and result[0]['telephone']=='03012345'
    assert public_contacts({'raw_ids':['B'],'contacts':[]},{})==[]
