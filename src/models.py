from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_url: str
    quote: str = Field(min_length=1)
    retrieved_at: str
    content_hash: str
    extraction_method: str = 'rules-v1'
    model_name: str | None = None
    prompt_version: str | None = None


class Contact(BaseModel):
    contact_name: str | None = None
    job_title: str | None = None
    decision_maker_relevance: bool | None = None
    verified_professional_email: str | None = None
    directory_email: str | None = None
    linkedin_url: str | None = None
    contact_source: str
    verification_status: str = 'directory-listed; role unverified'


class Company(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    company_id: str
    company_name: str = Field(min_length=1)
    normalized_name: str
    raw_ids: list[str] = Field(default_factory=list)
    website: str | None = None
    domain: str | None = None
    street_address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    berlin_office: bool = False
    address_validation_notes: str | None = None
    Berlin_service_area: bool | None = None
    company_type: str | None = None
    residential_management: bool | None = None
    weg_management: bool | None = None
    rental_management: bool | None = None
    commercial_management: bool | None = None
    managed_units: int | None = Field(default=None, ge=0)
    managed_units_qualifier: str | None = None
    managed_buildings: int | None = Field(default=None, ge=0)
    heating_cost_billing_relevance: bool | None = None
    operating_cost_billing_relevance: bool | None = None
    digital_features: bool | None = None
    property_coverage: bool | None = None
    contacts: list[Contact] = Field(default_factory=list)
    evidence: dict[str, Evidence] = Field(default_factory=dict)
    website_status: str = 'not checked'
    ai_enrichment_status: str | None = None
    ai_enrichment_error: str | None = None
    business_fit_score: int = 0
    score_upper_bound: int = 100
    evidence_completeness: int = 0
    contact_readiness_score: int = 0
    priority: Literal['High Priority','Medium Priority','Low Priority','Needs Research','Excluded'] = 'Needs Research'
    confidence: str = 'Low'
    qualification_notes: list[str] = Field(default_factory=list)
    source_url: str
    source_type: str = 'association directory import'
    retrieved_at: str | None = None
    extraction_method: str = 'directory-import-v1'
    model_name: str | None = None
    prompt_version: str | None = None
    validation_status: str = 'automated; manual review recommended'
