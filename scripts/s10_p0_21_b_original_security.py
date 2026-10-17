"""Real new-B ordinary-source denial, immutable attachment and revocation checks."""
from types import SimpleNamespace
from odoo import api
from odoo.exceptions import AccessError,UserError
import s10_p0_21_contract as c
from s10_p0_21_fixture import bind,key
from s10_p0_21_runtime import checkpoint,step
f=c.read(c.RUN/'b-chain.json');original=c.read(c.RUN/'original.json')
with env.registry.cursor() as cr:
    root=api.Environment(cr,1,{})
    store=root['ydental.access.store'].browse(f['store_id']);holder=SimpleNamespace(root=root,stores=[store])
    manager=root['res.users'].browse(f['manager_id']);front=root['res.users'].browse(f['frontdesk_id'])
    service=bind(holder,manager).env['ydental.settlement.service']
    row=root['ydental.settlement.bill.original'].browse(original['original_id']);attachment=row.attachment_id
    checks=[]
    def denied(label,call):
        with cr.savepoint():
            try:call()
            except AccessError:checks.append(label)
            else:raise AssertionError('ORIGINAL_DENIAL_MISSING:'+label)
    for actor in ['none_id','doctor_id','pharmacist_id']:
        bound=bind(holder,root['res.users'].browse(f[actor])).env['ydental.settlement.service']
        denied(actor+'-retrieve',lambda bound=bound:bound._bill_original_bytes(row.id))
        denied(actor+'-generate',lambda bound=bound:bound._store_bill_original(f['invoice_id'],key()))
    for label,record in [('original',row),('attachment',attachment)]:
        denied(label+'-RPC-read',lambda record=record:record.with_user(manager).read(['id']))
        denied(label+'-write',lambda record=record:record.with_user(manager).write({'name':'replacement'} if label=='attachment' else {'version':99}))
        denied(label+'-unlink',lambda record=record:record.with_user(manager).unlink())
    denied('native-binary-even-authorized',lambda:service.env['ir.binary']._find_record(res_id=attachment.id))
    denied('native-binary-token',lambda:service.env['ir.binary']._find_record(res_id=attachment.id,access_token='not-a-token'))
    other=root['ydental.access.store'].search([('company_id','=',store.company_id.id),('id','!=',store.id)],limit=1)
    wrong=bind(holder,manager,other).env['ydental.settlement.service']
    denied('wrong-store-session',lambda:wrong._bill_original_bytes(row.id))
    front_service=bind(holder,front).env['ydental.settlement.service']
    raw,digest=step(root,'other-authorized-reader',lambda:front_service._bill_original_bytes(row.id))
    assert digest==original['sha256']
    admin=bind(holder,manager).env['ydental.access.service']
    admin._grant(front.id,store.id,{'export':'none'})
    denied('old-bound-service-after-export-revoked',lambda:front_service._bill_original_bytes(row.id))
    reader=root['res.users'].browse(f['reader_id']);admin._grant(reader.id,store.id,{'settlement':'read','export':'none'})
    read_only=bind(holder,reader).env['ydental.settlement.service']
    assert read_only._workbench()['store']==store
    denied('settlement-read-without-export',lambda:read_only._bill_original_bytes(row.id))
    admin._grant(reader.id,store.id,{'settlement':'none','export':'write'})
    no_read=bind(holder,reader).env['ydental.settlement.service']
    denied('export-without-settlement-read',lambda:no_read._bill_original_bytes(row.id))
    try:service._bill_original_bytes(999999999)
    except UserError:checks.append('missing-original-no-render-fallback')
    else:raise AssertionError('MISSING_ORIGINAL_ACCEPTED')
    checkpoint(cr,root,'original-security')
    c.save(c.OUT/'original-security-result.json',{'checks':checks,'count':len(checks),'no_ordinary_account_promoted_to_admin':True,'attachment_id':attachment.id,'original_sha256':original['sha256'],'ordinary_frontdesk_revoked_after_verified_authorized_read':True,'committed_and_independently_read_back':True})
