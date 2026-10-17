"""One committed source: original issuance, separate document actions, exact retake."""
import json
from types import SimpleNamespace
from odoo import api
from s10_p0_21_fixture import key,bind,queue_bind
from s10_p0_21_runtime import pending,checkpoint,step
import s10_p0_21_contract as c

f=c.read(c.RUN/'b-chain.json');assert f['verified_checkpoint']=='chain' and f['database']==env.cr.dbname
with env.registry.cursor() as cr:
    root=api.Environment(cr,1,{})
    store=root['ydental.access.store'].browse(f['store_id']);holder=SimpleNamespace(root=root,stores=[store])
    manager=bind(holder,root['res.users'].browse(f['manager_id'])).env['ydental.settlement.service']
    original_key=key()
    original=step(root,'original-first',lambda:manager._store_bill_original(f['invoice_id'],original_key))
    checkpoint(cr,root,'original-first',{'original.json':original|{'invoice_id':f['invoice_id'],'request_key':original_key}})
    duplicate=step(root,'original-idempotency',lambda:manager._store_bill_original(f['invoice_id'],original_key))
    assert duplicate['original_id']==original['original_id'] and duplicate['duplicate']
    doctor=root['res.users'].browse(f['doctor_id'])
    owner=queue_bind(holder,doctor).env['ydental.clinical.service']
    held=step(root,'document-acquire',lambda:owner._operate('acquire',{'document_id':f['document_id']}))
    confirmed=step(root,'document-confirm',lambda:owner._operate('confirm',{'document_id':held['document_id'],'editor_token':held['editor_token'],'expected_version':held['version'],'content':held['content'],'key':key()}))
    content=dict(confirmed['content'],chief_complaint='P021 synthetic administrative wording correction only')
    corrected=step(root,'document-correct',lambda:owner._operate('correct',{'document_id':held['document_id'],'editor_token':held['editor_token'],'expected_version':confirmed['version'],'content':content,'key':key(),'reason':'Synthetic wording only; no economic change requested'}))
    step(root,'document-release',lambda:owner._operate('release',{'document_id':held['document_id'],'editor_token':held['editor_token']}))
    checkpoint(cr,root,'document-completion')
    raw,digest=step(root,'original-retake-after-document',lambda:manager._bill_original_bytes(original['original_id']))
    assert digest==original['sha256'] and c.sha(raw)==digest
    (c.PRIVATE/'original-retaken.pdf').write_bytes(raw)
    current,current_sha=step(root,'current-bill-after-document',lambda:manager._pdf('bill',f['invoice_id']))
    (c.PRIVATE/'current-bill.pdf').write_bytes(current)
    second=step(root,'original-explicit-next-version',lambda:manager._store_bill_original(f['invoice_id'],key(),original['original_id']))
    assert second['version']==2 and second['original_id']!=original['original_id']
    checkpoint(cr,root,'original-retake-and-new-version')
    c.save(c.OUT/'same-source-original-result.json',{'database':c.NAME,'patient_id':f['patient_id'],'execution_id':f['execution_id'],'document_id':f['document_id'],'confirmed_version':confirmed['version'],'corrected_version':corrected['version'],'old_price':600,'new_price':620,'original':original,'retaken_sha256':digest,'current_pdf_sha256':current_sha,'new_original':second,'old_snapshot_not_replaced':True,'committed_independently_verified':True})
