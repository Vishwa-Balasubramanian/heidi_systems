"""Add native Excel hyperlinks missing from the renderer's supported APIs.

Patch only OOXML hyperlink elements/relationships; retain all other workbook bytes.
"""
import json
import os
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
DOCREL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ET.register_namespace('',MAIN)
ET.register_namespace('r',DOCREL)


def main():
    target=ROOT/'outputs/berlin_ai/Heidi_Berlin_AI.xlsx'
    links=json.loads((ROOT/'reports/simple_workbook_previews/links.json').read_text())
    by_sheet={name:[x for x in links if x['sheet']==name] for name in ['Priority Leads','All Companies','Sources & Methodology']}
    replacements={}
    with zipfile.ZipFile(target) as source:
        for i,(name,items) in enumerate(by_sheet.items(),1):
            filename=f'xl/worksheets/sheet{i}.xml'
            relfile=f'xl/worksheets/_rels/sheet{i}.xml.rels'
            sheet=ET.fromstring(source.read(filename))
            relationships=ET.fromstring(source.read(relfile)) if relfile in source.namelist() else ET.Element(f'{{{REL}}}Relationships')
            hyperlinks=ET.Element(f'{{{MAIN}}}hyperlinks')
            for n,item in enumerate(items,1):
                if not item['url'].startswith(('http://','https://')):
                    raise ValueError('Only public HTTP source links allowed')
                identifier=f'rIdPublicLink{n}'
                ET.SubElement(hyperlinks,f'{{{MAIN}}}hyperlink',{'ref':item['cell'],f'{{{DOCREL}}}id':identifier})
                ET.SubElement(relationships,f'{{{REL}}}Relationship',{'Id':identifier,'Type':DOCREL+'/hyperlink','Target':item['url'],'TargetMode':'External'})
            following={'printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst'}
            index=next((j for j,child in enumerate(sheet) if child.tag.split('}')[-1] in following),len(sheet))
            sheet.insert(index,hyperlinks)
            replacements[filename]=ET.tostring(sheet,encoding='utf-8',xml_declaration=True)
            replacements[relfile]=ET.tostring(relationships,encoding='utf-8',xml_declaration=True)
        tmp=target.with_suffix('.links.tmp')
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as result:
            for entry in source.infolist():
                result.writestr(entry,replacements.pop(entry.filename,source.read(entry.filename)))
            for name,content in replacements.items():
                result.writestr(name,content)
    os.replace(tmp,target)
    print(f'Added {len(links)} native source and website hyperlinks.')


if __name__=='__main__':main()
