"""Owned-cursor checkpoints and per-action storage/display forensic gates."""
import json
import os
from collections import defaultdict
_counts=defaultdict(int)
from pathlib import Path
import s10_p0_21_contract as c

pending={}

def snapshot(env,full=False):
    env.flush_all()
    snap={}
    # Explicit display-only projection, not used to decide economic equality.
    spec={'ydental.treatment.event':['id','display_name','ydental_document_id'],
          'ydental.treatment.fee':['id','display_name','ydental_event_id'],
          'account.move':['id','display_name','partner_id'],
          'stock.move':['id','display_name','product_id'],
          'stock.quant':['id','display_name','product_id','lot_id']}
    display={m:env[m].search([],order='id').read(fields) for m,fields in spec.items()}
    env.flush_all()
    snap=c.capture(env.cr,full=full)
    snap['orm_display']=display
    snap['display_fields_explicit']=spec
    return snap

def step(env,label,call,gate=c.unchanged_economics):
    before=snapshot(env);c.save(c.PRIVATE/(label+'-pre-action.json'),before)
    c.event('business_action_intent',label=label)
    try:
        result=call();after=snapshot(env)
    except BaseException as e:
        try:
            after=snapshot(env)
            c.persist(label+'-exception',before,after,lambda a,b,i:{'failed_action':True,'no_success_inferred':True})
        finally:c.event('business_action_failure',label=label,error=type(e).__name__)
        raise
    c.save(c.PRIVATE/(label+'-display-before.json'),before['orm_display']);c.save(c.PRIVATE/(label+'-display-after.json'),after['orm_display'])
    raw,idx=c.diff({'tables':before['orm_display']},{'tables':after['orm_display']})
    c.save(c.PRIVATE/(label+'-display-full-diff.json'),raw);c.save(c.OUT/(label+'-display-diff-index.json'),{'changes':idx,'not_an_economic_gate':True,'source_contract':'display-field-contract.json'})
    c.persist(label,before,after,gate)
    c.event('business_action_response',label=label,status='accepted_after_storage_gate')
    return result

def checkpoint(cr,env,label,markers=None):
    # This verification runner owns this cursor and the business transaction.
    verify_native_facts(env)
    if markers:c.save(c.PRIVATE/(label+'-pending-markers-not-success.json'),markers)
    snap=snapshot(env,full=True);c.save(c.PRIVATE/(label+'-precommit-full.json'),snap)
    c.event('commit_intent',label=label,economic_storage_sha256=c.sha(c.canonical({t:r for t,r in snap['tables'].items() if c.economic(t)}).encode()))
    try:cr.commit()
    except BaseException as e:
        c.event('commit_result_unknown',label=label,error=type(e).__name__)
        c.readonly(label+'-commit-unknown')
        raise
    c.event('commit_returned',label=label)
    independent=c.readonly(label+'-independent')
    def committed_gate(a,b,index):
        c.unchanged_economics(a,b,index)
        for change in index:
            assert change['table'].startswith('orm_signaling_'),('COMMIT_READBACK_DRIFT',change['table'],change['columns'])
            t=change['table'];old=a['tables'].get(t,[]);new=b['tables'].get(t,[])
            oldrows={c.canonical(r) for r in old};assert oldrows<={c.canonical(r) for r in new}
            added=[r for r in new if c.canonical(r) not in oldrows];assert len(added)<=1
            assert all(set(r)-{'__physical_table__','__physical_oid__'}=={'id','date'} for r in added)
        return {'every_stored_row_read_back':True,'native_cache_signals_only_if_any':True}
    c.persist(label+'-committed',snap,independent,committed_gate)
    # Markers are published only after COMMIT and independent exact stored readback.
    if markers:
        for filename,value in markers.items():
            assert filename in {'b-chain.json','b-multi.json','trade.json','original.json'}
            c.save(c.RUN/filename,value|{'database':c.NAME,'oid':snap['oid'],'verified_checkpoint':label})
    c.save(c.OUT/(label+'-committed-checkpoint.json'),{'commit_returned':True,'independent_RO_RR_verified':True,'markers_published':sorted(markers or {}),'economic_storage_exact':True,'database':c.NAME,'oid':snap['oid']})
    return independent


def observed(env,label,call):
    label=os.environ['YDENTAL_P021_ACTION']+'-'+label
    _counts[label]+=1;label+='-'+str(_counts[label])
    before=snapshot(env);c.save(c.PRIVATE/(label+'-pre-action.json'),before)
    c.event('operation_intent',label=label)
    try:result=call()
    except BaseException as e:
        after=snapshot(env)
        c.persist(label+'-failed',before,after,lambda a,b,i:{'failed_action_only':True,'business_PASS':False})
        c.event('operation_failed',label=label,error=type(e).__name__)
        raise
    after=snapshot(env)
    c.persist(label,before,after,lambda a,b,i:{'expected_economic_action_delta_saved':True,'business_assertions':'pending scenario result/native accounting invariants before commit','business_PASS':False})
    c.event('operation_returned',label=label)
    return result


def verify_native_facts(env):
    env.flush_all()
    for move in env['account.move'].search([('state','=','posted')]):
        assert move.company_id.currency_id.is_zero(sum(move.line_ids.mapped('balance'))),('UNBALANCED_NATIVE_MOVE',move.id)
        assert all(line.company_id==move.company_id for line in move.line_ids),('MIXED_COMPANY_LINES',move.id)
    for source in env['ydental.settlement.source'].search([]):
        fee=source.ydental_fee_id;event=fee.ydental_event_id;invoice=source.ydental_invoice_id
        assert source.ydental_store_id==fee.ydental_store_id==event.ydental_store_id
        assert source.ydental_patient_id==fee.ydental_patient_id==event.ydental_patient_id
        assert invoice.company_id==source.ydental_store_id.company_id and invoice.state=='posted'
        assert source.ydental_line_id.move_id==invoice and event.state=='confirmed'
        assert source.ydental_currency_id==fee.ydental_currency_id==invoice.currency_id
    for payment in env['ydental.settlement.payment'].search([]):
        assert payment.ydental_payment_id.move_id.state=='posted'
        assert payment.ydental_payment_id.company_id==payment.ydental_store_id.company_id
        reserved=env['ydental.settlement.refund'].search([('ydental_payment_id','=',payment.id),('ydental_state','in',['approved','failed','unknown','done'])])
        assert sum(reserved.mapped('ydental_amount'))<=payment.ydental_amount
    for refund in env['ydental.settlement.refund'].search([]):
        if refund.ydental_state=='done':assert refund.ydental_native_payment_id.move_id.state=='posted'
        if refund.ydental_state=='rejected':assert not refund.ydental_native_payment_id and not refund.ydental_credit_note_id
    for event in env['ydental.inventory.event'].search([('state','=','done')]):
        assert event.ydental_move_id.state=='done',('INVENTORY_WITHOUT_DONE_MOVE',event.id)
    for original in env['ydental.settlement.bill.original'].search([]):
        assert original.attachment_id and not original.attachment_id.public and not original.attachment_id.access_token
        assert c.sha(original.attachment_id.raw.content)==original.pdf_sha256
    return True
