"""Readonly verification of known committed chain; never replays an economic action."""
import s10_p0_21_contract as c
from s10_p0_21_runtime import committed_gate
c.gate()
before=c.read(c.PRIVATE/'chain-precommit-full.json');observed=c.read(c.PRIVATE/'chain-independent-RO-rows.json');markers=c.read(c.PRIVATE/'chain-pending-markers-not-success.json');f=markers['b-chain.json']
partner=next(r for r in observed['tables']['ydental_patient'] if r['id']==f['patient_id'])['ydental_partner_id']
payments=[r for r in observed['tables']['ydental_settlement_payment'] if r['id'] in (f['payment_first_id'],f['payment_second_id'])]
assert len(payments)==2 and sorted(str(r['ydental_amount']) for r in payments)==['350.0','390.0']
native={r['id']:r for r in observed['tables']['account_payment']}
move_ids=[native[r['ydental_payment_id']]['move_id'] for r in payments]
assert len(set(move_ids))==2
for move_id in move_ids:
    move=next(r for r in observed['tables']['account_move'] if r['id']==move_id)
    assert move['move_type']=='entry' and move['state']=='posted' and move['partner_id']==partner
expected=[{'partner_id':partner,'field':'customer_rank','delta':2,'actor_uid':f['manager_id'],'source':'two actual posted customer payment entries; fixed account_move.py6370-6386 + partner.py883-917','captured_before_commit':False,'scope':'P021 captured before/after rows and exact native source; no inference about missing P020 fields'}]
c.persist('chain-explained-native-rank',before,observed,lambda a,b,i:committed_gate(a,b,i,expected))
current=c.readonly('chain-recovery-current')
c.persist('chain-recovery-current',observed,current,lambda a,b,i:committed_gate(a,b,i,[]))
c.save(c.RUN/'b-chain.json',f|{'database':c.NAME,'oid':current['oid'],'verified_checkpoint':'chain'})
c.save(c.OUT/'chain-recovered-committed-checkpoint.json',{'commit_returned_already_recorded':True,'new_independent_RO_RR_exact':True,'marker_published_only_now':True,'no_economic_replay':True,'original_failed_decision_preserved':True,'native_postcommit_rank_explained':expected})
print('KNOWN_COMMITTED_CHAIN_VERIFIED_AND_MARKER_PUBLISHED; ECONOMIC_REPLAY0')
