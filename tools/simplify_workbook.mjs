import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=JSON.parse(await fs.readFile(path.join(root,'website/heidi-leads/dist/data.json'),'utf8'));
const target=path.join(root,'outputs/berlin_ai/Heidi_Berlin_AI.xlsx');
const backup=path.join(root,'outputs/berlin_ai/backups/Heidi_Berlin_AI_detailed.xlsx');
await fs.access(backup);
const preview=path.join(root,'reports/simple_workbook_previews');
await fs.mkdir(preview,{recursive:true});
const wb=Workbook.create();
const linkRecords=[];
const color={navy:'#213D45',teal:'#176F64',ink:'#263D43',muted:'#71817E',line:'#DFE7E1',green:'#E7F2E9',amber:'#FBF1DC',blue:'#EDF3F7'};
const literal=v=>typeof v==='string'&&/^[=+@]/.test(v)?"'"+v:v;
const unique=a=>[...new Set(a.filter(Boolean))];
const tri=v=>v===true?'Yes':v===false?'No':'Not found';
function either(c,fields){const values=fields.map(k=>c[k]);return values.includes(true)?true:values.every(v=>v===false)?false:null;}
function billing(c){const heat=c.heating_cost_billing_relevance===true,operating=c.operating_cost_billing_relevance===true;return heat&&operating?'Heating + operating costs':heat?'Heating costs':operating?'Operating costs':either(c,['heating_cost_billing_relevance','operating_cost_billing_relevance'])===false?'No':'Not found';}
const columns=['Company Name','Priority','Customer Fit Score /100','Evidence Coverage %','Managed Units','Residential Management','Billing Services','Multiple Properties','Digital Portal','Contact Person','Email','Phone','Website','Berlin Address','Contact Verification','Source Link'];
const widths=[48,20,17,18,20,22,25,19,18,35,40,30,45,48,40,60];
function row(c){const contacts=c.contacts||[];return [c.company_name,c.priority,c.business_fit_score,c.evidence_completeness/100,c.managed_units??'Not found',tri(either(c,['residential_management','weg_management','rental_management'])),billing(c),tri(c.property_coverage),tri(c.digital_features),unique(contacts.map(x=>x.contact_name)).join('\n')||(contacts.length?'Not listed':'No public contact found'),unique(contacts.flatMap(x=>[x.verified_professional_email,x.directory_email])).join('\n')||'Not found',unique(contacts.map(x=>x.telephone)).join('\n')||'Not found',c.website||'Not found',c.street_address||'Not found',contacts.length?(contacts.some(x=>x.verified_professional_email)?'See contact verification in sources':'Public directory; role and email unverified'):'No public contact found',c.source_url||'Not found'].map(literal);}
function base(sheet,lastCol,lastRow){sheet.showGridLines=false;sheet.getRange(`A1:${lastCol}${lastRow}`).format.font={name:'Arial',size:10,color:color.ink};sheet.getRange(`A1:${lastCol}${lastRow}`).format.verticalAlignment='center';sheet.getRange(`A1:${lastCol}${lastRow}`).format.rowHeight=30;}
function header(sheet,range){sheet.getRange(range).format={fill:color.navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,verticalAlignment:'center',horizontalAlignment:'center',rowHeight:42};}
function hyperlink(sheet,address,url){if(!/^https?:\/\//i.test(url||''))return;sheet.getRange(address).values=[[url]];sheet.getRange(address).format.font={name:'Arial',size:10,color:color.teal};linkRecords.push({sheet:sheet.name,cell:address,url});}
function leadSheet(name,records,tableName){const s=wb.worksheets.add(name);const last=records.length+7;base(s,'P',last);s.tabColor=name==='Priority Leads'?color.teal:color.navy;
 s.getRange('A2').values=[[name==='Priority Leads'?'Heidi · Priority Leads':'Heidi · All Berlin Companies']];s.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:color.navy};
 s.getRange('A3').values=[['Berlin property management companies. Research: 9 November 2026.']];s.getRange('A3').format.font={name:'Arial',size:10,color:color.muted};
 s.getRange('A4').values=[[name==='Priority Leads'?'35 companies to review: 18 High Priority and 17 Medium Priority.':'292 companies: 18 High Priority, 17 Medium Priority and 257 Needs Research.']];
 s.getRange('A5').values=[['Not found = no supporting information found. It does not mean No.']];s.getRange('A5').format.font={name:'Arial',size:10,italic:true,color:color.muted};
 s.getRange('A7:P7').values=[columns];s.getRange(`A8:P${last}`).values=records.map(row);const t=s.tables.add(`A7:P${last}`,true,tableName);t.style='TableStyleLight9';t.showBandedRows=false;t.showFilterButton=true;
 header(s,'A7:P7');s.getRange(`A8:P${last}`).format.wrapText=true;s.getRange(`A8:P${last}`).format.rowHeight=48;
 widths.forEach((width,i)=>s.getRangeByIndexes(0,i,last,1).format.columnWidth=width);
 s.getRange(`C8:E${last}`).format.horizontalAlignment='right';s.getRange(`C8:C${last}`).setNumberFormat('0');s.getRange(`D8:D${last}`).setNumberFormat('0%');s.getRange(`E8:E${last}`).setNumberFormat('#,##0');
 s.getRange(`J8:L${last}`).setNumberFormat('@');
 s.getRange(`B8:B${last}`).conditionalFormats.add('containsText',{text:'High Priority',format:{fill:color.green,font:{color:'#2B6244',bold:true}}});
 s.getRange(`B8:B${last}`).conditionalFormats.add('containsText',{text:'Medium Priority',format:{fill:color.blue,font:{color:'#45687C'}}});
 s.getRange(`B8:B${last}`).conditionalFormats.add('containsText',{text:'Needs Research',format:{fill:color.amber,font:{color:'#80602A'}}});
 for(let i=0;i<records.length;i++){const c=records[i],r=i+8;if(c.managed_units!=null){s.getRange(`E${r}`).setNumberFormat(c.managed_units_qualifier==='lower bound'?'"Over "#,##0':c.managed_units_qualifier==='approximate'?'#,##0" (approx.)"':'#,##0');}hyperlink(s,`M${r}`,c.website);hyperlink(s,`P${r}`,c.source_url);const contactLines=Math.max(...row(c).slice(9,12).map(v=>String(v).split('\n').length));if(contactLines>2)s.getRange(`A${r}:P${r}`).format.rowHeight=Math.min(120,contactLines*15+12);}
 s.freezePanes.freezeRows(7);s.freezePanes.freezeColumns(1);return s;}
const companies=[...data.companies].sort((a,b)=>({ 'High Priority':0,'Medium Priority':1,'Needs Research':2}[a.priority]-{'High Priority':0,'Medium Priority':1,'Needs Research':2}[b.priority])||b.business_fit_score-a.business_fit_score||a.company_name.localeCompare(b.company_name,'de'));
leadSheet('Priority Leads',companies.filter(c=>['High Priority','Medium Priority'].includes(c.priority)),'PriorityCompanies');
leadSheet('All Companies',companies,'AllBerlinCompanies');
const labels={residential_management:'Residential management',weg_management:'WEG management',rental_management:'Rental management',commercial_management:'Commercial management',managed_units:'Managed units',managed_buildings:'Managed buildings / properties',heating_cost_billing_relevance:'Heating-cost billing',operating_cost_billing_relevance:'Operating-cost billing',digital_features:'Digital portal',property_coverage:'Multiple properties',Berlin_service_area:'Berlin service coverage'};
const evidence=[];
for(const c of companies){evidence.push([c.company_name,'Directory / contacts',c.street_address||'Address not found',c.source_url,'2026-11-09','Public directory listing; contact roles and email unverified']);for(const [field,e]of Object.entries(c.evidence)){const value=c[field];evidence.push([c.company_name,labels[field]||field,e.quote,e.source_url,e.retrieved_at==null?null:new Date(e.retrieved_at),typeof value==='boolean'?tri(value):value]);}}
const s=wb.worksheets.add('Sources & Methodology');const end=evidence.length+16;base(s,'F',end);s.tabColor='#8A9A8B';
[48,30,88,65,20,60].forEach((width,i)=>s.getRangeByIndexes(0,i,end,1).format.columnWidth=width);
s.getRange('A2').values=[['Sources & Methodology']];s.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:color.navy};
s.getRange('A3').values=[['Use the Company Name filter below to find supporting quotes and source links.']];
s.getRange('A4:C4').values=[['Read this first','Rule / weight','What it means']];header(s,'A4:C4');
const sconf=data.scoring;
const methods=[
 ['Customer Fit Score','0–100 points','Observed business fit. Higher means stronger published evidence, not a probability of purchase.'],
 ['Evidence Coverage','Weighted coverage','How much of the scoring model has supporting evidence. It is not an accuracy percentage.'],
 ['Priority',`High ≥ ${sconf.high_threshold}; Medium ≥ ${sconf.medium_threshold}`,`Requires management-service evidence, Berlin relevance and at least ${sconf.min_completeness}% coverage. Otherwise Needs Research.`],
 ['Missing information','Not found','No supporting information was found. This is different from an explicit No.'],
 ['Residential management',`${sconf.weights.services} points`,'Yes when residential, WEG or rental management is evidenced. Detailed service quotes are listed below.'],
 ['Managed units',`${sconf.weights.portfolio} points maximum`,'1–99 units: 5; 100–499: 10; 500–999: 18; 1,000+: 25. Over / approximate qualifiers are retained. Totals may cover locations beyond Berlin.'],
 ['Billing services',`${sconf.weights.billing} points`,'Explicit heating-cost or operating-cost billing evidence. Missing billing information does not establish that no service exists.'],
 ['Multiple properties',`${sconf.weights.coverage} points`,'Evidence of managing more than one building or property. A count of apartments alone is insufficient.'],
 ['Digital portal',`${sconf.weights.digital} points`,'An evidenced customer, owner or tenant portal. Generic digital marketing wording is insufficient.'],
 ['Contacts and limitations','Public directory contacts','Roles, decision-making authority and email deliverability are unverified unless explicitly marked. Unknown contacts do not lower business-fit scores. Scores are a static research snapshot; refresh through the pipeline.'],
];
s.getRange('A5:C14').values=methods;s.getRange('A5:C14').format.wrapText=true;s.getRange('A5:C14').format.rowHeight=44;s.getRange('A10:C10').format.rowHeight=60;s.getRange('A14:C14').format.rowHeight=60;
s.getRange('A16:F16').values=[['Company Name','Information','Published Detail / Exact Quote','Source Link','Date Accessed','Value / Verification']];
s.getRange(`A17:F${end}`).values=evidence.map(r=>r.map(literal));const st=s.tables.add(`A16:F${end}`,true,'SupportingSources');st.style='TableStyleLight9';st.showFilterButton=true;st.showBandedRows=false;header(s,'A16:F16');s.getRange(`A17:F${end}`).format.wrapText=true;s.getRange(`A17:F${end}`).format.rowHeight=72;s.getRange(`E17:E${end}`).setNumberFormat('dd mmm yyyy');
for(let i=0;i<evidence.length;i++){const rowIndex=i+17;hyperlink(s,`D${rowIndex}`,evidence[i][3]);if(typeof evidence[i][4]==='string')s.getRange(`E${rowIndex}`).values=[[new Date(evidence[i][4])]];const lines=Math.max(Math.ceil(String(evidence[i][2]||'').length/85),Math.ceil(String(evidence[i][5]||'').length/55));if(lines>4)s.getRange(`A${rowIndex}:F${rowIndex}`).format.rowHeight=Math.min(180,lines*14+12);}
s.freezePanes.freezeColumns(1);
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Priority Leads!A7:I11',include:'values,formulas',tableMaxRows:5,tableMaxCols:9,maxChars:2000})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},summary:'Final error scan',maxChars:1000})).ndjson);
for(const [sheetName,range,name]of [['Priority Leads','A1:F12','priority'],['All Companies','A1:F12','all'],['Sources & Methodology','A1:C14','methodology'],['Sources & Methodology','A16:C21','evidence'],['Priority Leads','J7:O12','contacts']]){const image=await wb.render({sheetName,range,scale:1.5,format:'png'});await fs.writeFile(path.join(preview,`${name}.png`),new Uint8Array(await image.arrayBuffer()));}
await (await SpreadsheetFile.exportXlsx(wb)).save(target);
await fs.writeFile(path.join(preview,'links.json'),JSON.stringify(linkRecords));
console.log(`Saved ${target}: 35 priority leads, 292 companies, ${evidence.length} source rows, 16 main columns.`);
