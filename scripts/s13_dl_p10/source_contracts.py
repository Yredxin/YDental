"""P10 offline canonical contracts, exact frozen resources and translation terms."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from lxml import etree
ROOT = Path.cwd()
BASE = '9ea71c63465ec3ab625f141dbbbe277edd436d90'
FILE = 'ydental_reporting/views/ydental_reporting_templates.xml'
PREFIX = 'o_ydental_reporting_main_'
def original(name):
    return subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
def restore(raw):
    tree=etree.fromstring(raw)
    for node in list(tree.iter()):
        if node.get('report_main_actions') is not None:
            assert node.get('report_main_actions')=='True'
            assert node.get('t-call') in ('ydental_reporting.ydental_operating_report_navigation','ydental_reporting.ydental_operating_report_scope')
            del node.attrib['report_main_actions']
        elif node.get('t-call','').startswith('ydental_inventory.p7_icon_'):
            assert node.get('t-call') in ['ydental_inventory.p7_icon_'+x for x in ['search','arrow_right','chevron_left','chevron_right']]
            node.getparent().remove(node)
    for node in list(tree.iter()):
        if node.tag=='span' and node.get('class')==PREFIX+'action_label':
            assert node.get('t-translation')=='on' and not len(node)
            parent=node.getparent()
            assert parent.text is None and len(parent)==1
            parent.text=node.text;parent.remove(node)
    for node in tree.iter():
        if node.get('data-dl-layout')=='report-actions-spacing':del node.attrib['data-dl-layout']
        if node.get('data-dl-actions')=='report-actions':del node.attrib['data-dl-actions']
        if 't-att-data-dl-actions' in node.attrib:
            assert node.get('t-att-data-dl-actions')=="'report-actions' if report_main_actions else None"
            del node.attrib['t-att-data-dl-actions']
        if 't-att-class' in node.attrib and 'report_main_actions' in node.get('t-att-class'):
            value=node.get('t-att-class');del node.attrib['t-att-class']
            if node.tag=='nav':node.set('class','o_ydental_reporting_navigation')
            elif node.tag=='div':node.set('class','o_ydental_reporting_scope')
            else:assert node.tag in ('a','summary')
        if 'class' in node.attrib:
            cls=[c for c in node.get('class').split() if not c.startswith(PREFIX)]
            if cls:node.set('class',' '.join(cls))
            else:del node.attrib['class']
    return tree
raw=(ROOT/FILE).read_bytes()
before=etree.fromstring(original(FILE));after=restore(raw)
a=etree.tostring(before,method='c14n');b=etree.tostring(after,method='c14n')
assert a==b,'Original full XML differs beyond enumerated P10 presentation changes'
manifest='ydental_reporting/__manifest__.py'
old=ast.literal_eval(original(manifest).decode());new=ast.literal_eval((ROOT/manifest).read_text())
for name in ['ydental_access','ydental_inventory']:
    assert new['depends'].count(name)==1;new['depends'].remove(name)
for name in ['report_actions','report_spacing']:
    asset='ydental_reporting/static/src/'+name+'/'+name+'.scss'
    assert new['assets']['web.assets_frontend'].count(asset)==1
    new['assets']['web.assets_frontend'].remove(asset)
assert old==new
frozen=['ydental_reporting/static/src/reporting/reporting.js','ydental_reporting/static/src/reporting/reporting.scss','ydental_reporting/static/src/report_filters/report_filters.js','ydental_reporting/static/src/report_filters/report_filters.scss','ydental_access/static/src/scss/_actions.scss','ydental_inventory/views/ydental_inventory_templates.xml','ydental_inventory/static/lib/lucide/SOURCE.json','ydental_print/static/src/documents_actions/documents_actions.scss','ydental_print/static/src/documents_spacing/documents_spacing.scss']
for name in frozen:assert original(name)==(ROOT/name).read_bytes(),name
sys.path.insert(0,str(ROOT.parent))
from odoo.tools.translate import xml_translate
def terms(tree):
    out=[]
    xml_translate(lambda v:out.append(v) or v,etree.tostring(tree,encoding='unicode'))
    return out
oldterms=terms(before);newterms=terms(etree.fromstring(raw))
assert oldterms==newterms,'Native full translation extraction changed'
print(json.dumps({'status':'P10_FULL_CANONICAL_SOURCE_MANIFEST_FROZEN_AND_NATIVE_TERMS_PASS','base':BASE,'candidate':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'canonical_sha256':hashlib.sha256(b).hexdigest(),'translation_occurrences':len(oldterms),'translation_unique':len(set(oldterms)),'frozen':[{'file':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in frozen],'layer':'SOURCE_PURE_NOT_LOADED_BROWSER'}))
