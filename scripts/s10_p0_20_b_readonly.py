"""New B-only RO/RR full snapshot and redacted complete diff before decision."""
import json
import sys
import time
import psycopg2
import s10_p0_20_contract as c
from s10_p0_20_b_control import NAME,RUN
c.checkpoint();label=sys.argv[1];assert label in ('round1-before','final')
c.save(c.PRIVATE/('B-'+label+'-RO-intent.json'),{'database':NAME,'READ_ONLY':True,'REPEATABLE_READ':True,'attempt':1})
conn=psycopg2.connect(dbname=NAME,options=c.OPTIONS,connect_timeout=5,**c.credentials())
try:
    conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
    with conn.cursor() as cur:
        cur.execute('SHOW transaction_read_only');assert cur.fetchone()[0]=='on'
        cur.execute('SHOW transaction_isolation');assert cur.fetchone()[0]=='repeatable read'
        cur.execute(c.IDENTITY_SQL);db,oid,cluster,pid=cur.fetchone();m=c.read(RUN/'database.json');assert (db,oid,cluster)==(NAME,m['oid'],c.CLUSTER)
        cur.execute(c.CATALOG_SQL);cols={}
        for t,k in cur.fetchall():cols.setdefault(t,[]).append(k)
        tables={}
        for t,fields in cols.items():
            cur.execute('SELECT to_jsonb(t)::text FROM public."'+t+'" t ORDER BY '+('"id"' if 'id' in fields else 'to_jsonb(t)::text'))
            tables[t]=[json.loads(r[0]) for r in cur.fetchall()]
        snap={'tables':tables,'schema':cols,'database':NAME,'oid':oid,'cluster':cluster,'backend_pid':pid}
        c.save(c.PRIVATE/('B-'+label+'-RO-rows.json'),snap)
        c.save(c.OUT/('B-'+label+'-RO-signatures.json'),{k:v for k,v in snap.items() if k not in ('tables','schema')}|{'READ_ONLY':True,'REPEATABLE_READ':True,'full_snapshot_saved':True,'signatures':{t:{'rows':len(r),'sha256':c.sha(c.canonical(r).encode())} for t,r in tables.items()}})
        if label=='round1-before':
            expected=['ydental_access_store','ydental_patient','ydental_inventory_event','ydental_treatment_event','ydental_treatment_fee','ydental_settlement_source','ydental_settlement_payment','ydental_settlement_refund','account_move','account_payment','stock_move','ydental_access_audit']
            counts={t:len(tables[t]) for t in expected}
            c.save(c.OUT/'B-round0-rollback-confirmation.json',{'counts':counts,'economic_no_commit':all(v==0 for v in counts.values()),'evidence_saved_before_gate':True})
            assert all(v==0 for v in counts.values()),'FAILED_FIXTURE_NOT_ROLLED_BACK'
finally:
    conn.rollback();conn.close()
    c.save(c.PRIVATE/('B-'+label+'-RO-closed.json'),{'rollback':True,'closed':True})
