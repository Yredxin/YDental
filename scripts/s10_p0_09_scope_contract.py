"""Read-only default-store evidence and the exact shared native scope validator."""
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
import json
import s10_p0_09_control as c


def source_facts(name):
    facts={}
    with c.s.connect(name) as con,con.cursor() as cur:
        cur.execute('SELECT CURRENT_TIMESTAMP AT TIME ZONE \'UTC\'')
        now=cur.fetchone()[0]
        for uid,target in ((6,1),(14,3)):
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='res_users' AND column_name='ydental_test_default_store_id'")
            has_fixture_column=bool(cur.fetchall())
            cur.execute('SELECT active FROM res_users WHERE id=%s',(uid,));active=cur.fetchone()[0];assert active
            fixture=None
            if has_fixture_column:
                cur.execute('SELECT ydental_test_default_store_id FROM res_users WHERE id=%s',(uid,));fixture=cur.fetchone()[0]
            cur.execute('SELECT m.id,m.ydental_store_id,m.ydental_employee_id,m.active,e.active,s.active,s.ydental_timezone FROM ydental_access_membership m JOIN hr_employee e ON e.id=m.ydental_employee_id JOIN ydental_access_store s ON s.id=m.ydental_store_id WHERE m.ydental_user_id=%s ORDER BY m.id',(uid,))
            memberships=[dict(zip(('id','store','employee','active','employee_active','store_active','timezone'),r)) for r in cur.fetchall()]
            valid={r['store'] for r in memberships if r['active'] and r['employee_active'] and r['store_active']}
            cur.execute('SELECT m.ydental_store_id,g.ydental_level FROM ydental_access_grant g JOIN ydental_access_membership m ON m.id=g.ydental_membership_id WHERE m.ydental_user_id=%s AND m.active AND g.ydental_category=\'settlement\'',(uid,))
            levels=dict(cur.fetchall());assert levels[target] in ('read','write')
            cur.execute('SELECT id,ydental_store_id,ydental_start,ydental_end FROM ydental_supply_assignment WHERE ydental_user_id=%s AND state=\'active\' ORDER BY id',(uid,))
            assignments=[];eligible=[]
            zones={r['store']:r['timezone'] for r in memberships}
            for ident,store,start,end in cur.fetchall():
                assignments.append({'id':ident,'store':store,'start':str(start),'end':str(end)})
                if store not in valid:continue
                day=lambda t:t.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(zones[store])).date()
                if start<now+timedelta(days=2) and end>now-timedelta(days=2) and day(start)<=day(now)<=day(end-timedelta(microseconds=1)) and end>now:
                    eligible.append((ident,store,start,end))
            current=[r for r in eligible if r[2]<=now]
            pool=current or ([r for r in eligible if r[2]==min(x[2] for x in eligible)] if eligible else [])
            candidates=sorted({r[1] for r in pool})
            cur.execute('SELECT id,ydental_store_id,ydental_revision,write_date FROM ydental_access_session WHERE ydental_user_id=%s AND ydental_store_id IS NOT NULL ORDER BY write_date DESC,id DESC',(uid,))
            previous=[dict(zip(('id','store','revision','write_date'),r)) for r in cur.fetchall()]
            fallback=next((r['store'] for r in previous if r['store'] in valid),None)
            assert fixture is None,'fixture default is unexpected'
            default=candidates[0] if len(candidates)==1 else None if candidates else fallback
            cur.execute('SELECT id FROM ydental_queue_lease WHERE ydental_actor_id=%s AND ydental_active',(uid,));lease=[r[0] for r in cur.fetchall()]
            cur.execute('SELECT e.id FROM ydental_queue_execution e JOIN ydental_queue_lease l ON l.id=e.ydental_lease_id WHERE l.ydental_actor_id=%s AND e.state IN (\'serving\',\'verify\')',(uid,));execution=[r[0] for r in cur.fetchall()]
            cur.execute('SELECT id FROM ydental_queue_hold WHERE ydental_actor_id=%s AND state IN (\'active\',\'verify\')',(uid,));hold=[r[0] for r in cur.fetchall()]
            assert not lease and not execution and not hold,'actor busy'
            facts[str(uid)]={'target':target,'memberships':memberships,'valid_stores':sorted(valid),
                'settlement_levels':levels,'test_default':fixture,'test_default_column_installed':has_fixture_column,'assignments':assignments,
                'current_eligible_assignment_ids':[r[0] for r in pool],'default_candidates':candidates,
                'last_valid_session':next((r for r in previous if r['store'] in valid),None),
                'predicted_default':default,'execution':{'lease_ids':lease,'execution_ids':execution,'hold_ids':hold}}
    return {'actors':facts,'C_enabled':facts['14']['predicted_default']==4 and 4 in facts['14']['valid_stores'],
        'C_status':'ELIGIBLE_IF_ACTUAL_STORE4' if facts['14']['predicted_default']==4 else 'NOT_APPLICABLE_NO_DEFAULT4_EVIDENCE'}


def validate_scope(cookies,observed,baseline,actor,target,dom_revision,contract,expected=None,gets=()):
    from s10_p0_09_browser import require
    require((actor,target) in ((6,1),(14,3)),'S1_ACTOR_TARGET')
    tokens=[r.get('value') for r in cookies if r.get('name')=='session_id']
    require(len(tokens)==1 and isinstance(tokens[0],str) and len(tokens[0])>=42,'S2_COOKIE_SHAPE')
    digest=c.s.sha(tokens[0][:42].encode())
    old=baseline['all']['rows']['ydental_access_session']
    rows=[r for r in observed['all']['rows']['ydental_access_session'].values() if r['ydental_key_hash']==digest]
    require(len(rows)==1,'S2_SESSION_UNIQUE')
    row=rows[0];uid=row['ydental_user_id'];store=row['ydental_store_id'];rev=row['ydental_revision']
    require(row['id'] not in old and uid==actor and row['create_uid']==row['write_uid']==actor,'S2_NEW_OWN_SESSION')
    own=contract['actors'][str(actor)]
    require(target in own['valid_stores'] and own['settlement_levels'].get(str(target),own['settlement_levels'].get(target)) in ('read','write'),'S3_TARGET_PERMISSION')
    require(not any(own['execution'].values()),'S3_ACTOR_BUSY')
    require(store is None or store in own['valid_stores'],'S3_CURRENT_MEMBERSHIP')
    require(dom_revision==str(rev),'S4_DOM_REVISION')
    # The metadata gate includes exact native identity audit chains, not an audit-table exemption.
    c.web_diff(baseline,observed,scope_contract=contract,gets=gets)
    if expected is not None:
        require(row['id']==expected['session_id'] and actor==expected['actor'],'S5_SESSION_CHANGED')
        require(store==target and rev==expected['revision'],'S5_FINAL_SCOPE')
        return dict(expected)
    if store==target and rev==1:branch='A'
    elif store is None and rev==0:branch='B'
    elif actor==14 and store==4 and rev==1 and contract['C_enabled']:branch='C'
    else:require(False,'S6_UNAUTHORIZED_SCOPE_STATE')
    return {'actor':actor,'session_id':row['id'],'store':store,'revision':rev,'target':target,'branch':branch}


def main():
    facts=source_facts(c.s.SOURCE)
    c.save_once(c.PRIVATE/'scope-contract.json',facts)
    print(json.dumps(facts,default=str))


if __name__=='__main__':main()
