from pathlib import Path
import configparser,hashlib,json,re,subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
root=Path.cwd();outdir=root/'docs/evidence/s07-rework'
queries={
'events':"SELECT id,ydental_source_namespace,ydental_source_key,ydental_kind,state,ydental_quantity,ydental_lot_id,ydental_move_id,ydental_parent_id,ydental_price_snapshot,ydental_synthetic,ydental_actor_id,ydental_responsible_id,ydental_actual_at,ydental_reconciled_at,ydental_correction_id FROM ydental_inventory_event WHERE ydental_lot_id=ANY(%s) ORDER BY id",
'moves':"SELECT m.id,m.state,m.product_id,m.quantity,m.uom_id,m.location_id,m.location_dest_id,m.ydental_store_id,e.id event_id FROM stock_move m JOIN ydental_inventory_event e ON e.ydental_move_id=m.id WHERE e.ydental_lot_id=ANY(%s) ORDER BY m.id",
'move_lines':"SELECT ml.id,ml.move_id,ml.lot_id,ml.quantity,ml.location_id,ml.location_dest_id,m.state FROM stock_move_line ml JOIN stock_move m ON m.id=ml.move_id WHERE ml.lot_id=ANY(%s) ORDER BY ml.id",
'quants':"SELECT q.id,q.product_id,q.lot_id,q.quantity,q.reserved_quantity,q.location_id,l.usage,l.ydental_store_id,l.name FROM stock_quant q JOIN stock_location l ON l.id=q.location_id WHERE q.lot_id=ANY(%s) ORDER BY q.id",
'audits':"SELECT a.id,a.ydental_event,a.ydental_target_model,a.ydental_target_id,a.ydental_store_id,a.ydental_user_id,a.ydental_before,a.ydental_after FROM ydental_access_audit a JOIN ydental_inventory_event e ON e.id=a.ydental_target_id AND a.ydental_target_model='ydental.inventory.event' WHERE e.ydental_lot_id=ANY(%s) ORDER BY a.id",
'batches':"SELECT b.id,b.ydental_store_id,b.ydental_lot_id,b.ydental_enabled,l.expiration_date FROM ydental_inventory_batch b JOIN stock_lot l ON l.id=b.ydental_lot_id WHERE l.id=ANY(%s) ORDER BY b.id",
}
for n in ('final','second'):
 db=Path('/tmp/ydental-s07-rework-'+n+'-db').read_text().strip();run=root/'.local'/db
 assert re.fullmatch(r'ydental_s07_test_[0-9]{14}_[a-f0-9]{8}',db)
 meta=json.loads((run/'database.json').read_text());assert meta['database']==db
 assert hashlib.sha256((run/'odoo.conf').read_bytes()).hexdigest()==meta['config_sha256']
 c=configparser.ConfigParser(interpolation=None);c.read(run/'odoo.conf');c=c['options'];assert (c['db_host'],c['db_port'],c['db_user'],c['db_name'],c['dbfilter'])==('127.0.0.1','5432','odoo',db,'^'+db+'$')
 preview=json.loads((run/'preview.json').read_text());out={'database':db,'test':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'scope':'read-only native rows for final Firefox synthetic fixture','preview_ids':preview}
 lots=[preview['lot'],preview['material'],preview['prosthesis']]+[h['lot'] for h in preview['history']]
 conn=psycopg2.connect(host=c['db_host'],port=c['db_port'],user=c['db_user'],password=c['db_password'],dbname=db,connect_timeout=3);conn.set_session(readonly=True)
 with conn:
  with conn.cursor(cursor_factory=RealDictCursor) as cr:
   cr.execute('SELECT system_identifier::text cluster FROM pg_control_system()');assert cr.fetchone()['cluster']==meta['cluster']
   cr.execute('SELECT oid FROM pg_database WHERE datname=%s',[db]);assert cr.fetchone()['oid']==meta['oid']
   for name,query in queries.items():cr.execute(query,[lots]);out[name]=[dict(row) for row in cr.fetchall()]
   cr.execute("SELECT count(*) n FROM ydental_inventory_event e JOIN product_product p ON p.id=e.ydental_product_id JOIN product_template t ON t.id=p.product_tmpl_id WHERE (e.ydental_kind IN ('prescription','chairside') AND t.ydental_inventory_kind!='medicine') OR (e.ydental_kind='treatment' AND t.ydental_inventory_kind!='material')");out['source_category_mismatch']=cr.fetchone()['n'];assert out['source_category_mismatch']==0
   cr.execute("SELECT count(*) n FROM ydental_inventory_event e WHERE e.ydental_reconciled_at IS NOT NULL AND (SELECT count(*) FROM ydental_access_audit a WHERE a.ydental_event='inventory.recovery' AND a.ydental_target_model='ydental.inventory.event' AND a.ydental_target_id=e.id)!=1");out['recovery_audit_mismatch']=cr.fetchone()['n'];assert out['recovery_audit_mismatch']==0
 conn.close()
 for h in preview['history']:
  event=next(e for e in out['events'] if e['id']==h['event']);assert event['state']=='done' and event['ydental_price_snapshot']['unit_price']==20 and event['ydental_correction_id']>event['id'] and event['ydental_reconciled_at']>=event['ydental_actual_at']
  qty=sum(q['quantity'] for q in out['quants'] if q['lot_id']==h['lot'] and q['usage']=='internal');assert qty==3
 out['result']='PASS';(outdir/('native-trace-'+n+'.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+'\n')
 print(json.dumps({'database':db,'result':'PASS','rows':{name:len(out[name]) for name in queries}}))
(outdir/'native-trace-queries.json').write_text(json.dumps(queries,indent=2)+'\n')
