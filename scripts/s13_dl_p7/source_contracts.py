from lxml import etree
from pathlib import Path
import subprocess,copy,json,hashlib
r=Path.cwd();path='ydental_inventory/views/ydental_inventory_templates.xml'
base=subprocess.check_output(['git','show','e31ea56d1ff903461eda86c08088c5f7e32aef7e:'+path]);after=(r/path).read_bytes()
b=etree.fromstring(base);a=etree.fromstring(after)
new=a.xpath('./template[starts-with(@id,"p7_icon_")]');assert len(new)==7
for n in new:a.remove(n)
xpaths=['//template[@id="ydental_inventory_page"]//button','//template[@id="ydental_inventory_page"]//summary', '//a[text()="Cancel and return to viewing"]','//a[text()="Open this source"]','//a[text()="Previous source page" or text()="Next source page"]','//h2[text()="Lots and alerts" or text()="Inventory sources and recovery"]']
counts=[]
for xp in xpaths:
 old=b.xpath(xp)
 # Stable DOM correspondence: same absolute structural position before child wrapping.
 for o in old:
  ep=b.getroottree().getpath(o);n=a.xpath(ep)[0]
  assert n.tag==o.tag
  assert n.get('t-att-data-dl-actions')=="'inventory-actions' if inventory_lookup else None"
  n.attrib.pop('t-att-data-dl-actions')
  for key in ['class','t-att-class']:
   if key in o.attrib:n.set(key,o.get(key))
   elif key in n.attrib:n.attrib.pop(key)
  branches=list(n);assert len(branches)==2 and branches[0].tag=='t' and branches[0].get('t-if')=='inventory_lookup' and branches[1].get('t-else')==''
  assert branches[1].text==o.text and not len(branches[1])
  parts=list(branches[0]);assert all((p.tag=='span' and p.attrib=={'class':'o_ydental_inventory_action_label','t-translation':'on'} and not len(p) and p.text==o.text) or (p.tag=='t' and list(p.attrib)==['t-call'] and p.get('t-call').startswith('ydental_inventory.p7_icon_') and not len(p)) for p in parts)
  assert len([p for p in parts if p.tag=='span'])==1
  for ch in list(n):n.remove(ch)
  n.text=o.text
 counts.append(len(old))
assert counts==[15,13,10,1,2,2],counts
# Normalizing only the exact allowed control presentation must recover the full original XML.
assert etree.tostring(a,method='c14n')==etree.tostring(b,method='c14n'),'Nonpresentation contract or frozen content changed'
assert subprocess.check_output(['git','diff','e31ea56d','--name-only','--','ydental_inventory/controllers','ydental_inventory/models','ydental_inventory/security']).decode()==''
print(json.dumps({'status':'FULL_BASELINE_XML_RESTORED_AFTER_VALIDATING_ONLY_ALLOWED_CONTROL_PRESENTATION','counts':counts,'baseline_sha256':hashlib.sha256(base).hexdigest(),'current_sha256':hashlib.sha256(after).hexdigest(),'fields_form_actions_conditions_DOM_order_permissions_unchanged':True}))
