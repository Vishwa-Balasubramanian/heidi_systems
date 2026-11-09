export const priorityRank={'High Priority':0,'Medium Priority':1,'Needs Research':2,'Low Priority':3,'Excluded':4};
export function filterCompanies(companies,s){
 const q=(s.q||'').trim().toLocaleLowerCase();
 return companies.filter(c=>{
  if(s.view==='priority'&&!['High Priority','Medium Priority'].includes(c.priority))return false;
  if(s.priority&&s.priority!=='all'&&c.priority!==s.priority)return false;
  if(q&&![c.company_name,c.street_address,c.domain].some(v=>(v||'').toLocaleLowerCase().includes(q)))return false;
  if(s.service&&c[s.service]!==true)return false;
  if(s.units==='known'&&c.managed_units==null)return false;
  if(s.billing==='yes'&&c.heating_cost_billing_relevance!==true&&c.operating_cost_billing_relevance!==true)return false;
  if(s.digital==='yes'&&c.digital_features!==true)return false;
  if(s.status&&c.ai_enrichment_status!==s.status)return false;
  if(s.completeness&&c.evidence_completeness<Number(s.completeness))return false;
  return true;
 });
}
export function sortCompanies(companies,sort='recommended',group=false){return [...companies].sort((a,b)=>{
 if(group&&a.priority!==b.priority)return priorityRank[a.priority]-priorityRank[b.priority];
 if(sort==='name')return a.company_name.localeCompare(b.company_name,'de');
 if(sort==='units'){if(a.managed_units==null||b.managed_units==null)return a.managed_units==null?(b.managed_units==null?0:1):-1;return b.managed_units-a.managed_units;}
 if(sort==='completeness')return b.evidence_completeness-a.evidence_completeness||b.business_fit_score-a.business_fit_score;
 return b.business_fit_score-a.business_fit_score||b.evidence_completeness-a.evidence_completeness||a.company_name.localeCompare(b.company_name,'de');
});}
