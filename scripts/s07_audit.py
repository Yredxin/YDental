"""Read-only native ledger invariants, executed only by the guarded S07 runner."""
from datetime import datetime, timezone
import json
import hashlib
import subprocess
import os
from pathlib import Path
import re

run=Path(os.environ['YDENTAL_S07_RUN_DIR'])
assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s07_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
queries={
'negative_internal_quant':"SELECT count(*) FROM stock_quant q JOIN stock_location l ON l.id=q.location_id WHERE l.ydental_store_id IS NOT NULL AND l.usage='internal' AND q.quantity < -0.000001",
'duplicate_source':"SELECT count(*) FROM (SELECT ydental_store_id,ydental_source_namespace,ydental_source_key FROM ydental_inventory_event GROUP BY 1,2,3 HAVING count(*)>1) d",
'half_event':"SELECT count(*) FROM ydental_inventory_event e LEFT JOIN stock_move m ON m.id=e.ydental_move_id WHERE (e.state='done' AND (m.id IS NULL OR m.state!='done')) OR (e.state='pending' AND (m.id IS NOT NULL OR e.ydental_responsible_id IS NULL))",
'event_move_quantity_mismatch':"SELECT count(*) FROM ydental_inventory_event e JOIN stock_move m ON m.id=e.ydental_move_id WHERE abs(e.ydental_quantity-m.quantity)>0.000001 OR e.ydental_product_id!=m.product_id OR e.ydental_from_id!=m.location_id OR e.ydental_to_id!=m.location_dest_id",
'movement_audit_mismatch':"SELECT count(*) FROM ydental_inventory_event e WHERE e.state='done' AND (SELECT count(*) FROM ydental_access_audit a WHERE a.ydental_event='inventory.movement' AND a.ydental_target_model='ydental.inventory.event' AND a.ydental_target_id=e.id)!=1",
'quant_move_reconciliation':"""WITH deltas AS (
SELECT ml.product_id,ml.lot_id,ml.location_dest_id loc,ml.quantity qty FROM stock_move_line ml JOIN stock_move m ON m.id=ml.move_id WHERE m.state='done'
UNION ALL SELECT ml.product_id,ml.lot_id,ml.location_id loc,-ml.quantity qty FROM stock_move_line ml JOIN stock_move m ON m.id=ml.move_id WHERE m.state='done'),
m AS (SELECT product_id,lot_id,loc,sum(qty) qty FROM deltas GROUP BY 1,2,3),
q AS (SELECT product_id,lot_id,location_id loc,sum(quantity) qty FROM stock_quant GROUP BY 1,2,3)
SELECT count(*) FROM m FULL OUTER JOIN q USING(product_id,lot_id,loc) JOIN stock_location l ON l.id=coalesce(m.loc,q.loc)
WHERE l.ydental_store_id IS NOT NULL AND abs(coalesce(m.qty,0)-coalesce(q.qty,0))>0.000001""",
'wrong_quant_store':"SELECT count(*) FROM stock_quant q JOIN stock_location l ON l.id=q.location_id WHERE l.ydental_store_id IS NOT NULL AND q.ydental_store_id IS DISTINCT FROM l.ydental_store_id",
}
audit_result={}
with env.registry.cursor() as audit_cr:
    for name,query in queries.items():
        audit_cr.execute(query);audit_result[name]=audit_cr.fetchone()[0]
    assert all(v==0 for v in audit_result.values()),audit_result
    audit_cr.execute("SELECT count(*) FROM ydental_inventory_event");audit_result['event_count']=audit_cr.fetchone()[0]
    signatures={}
    for table,query in {
        'event': 'SELECT row_to_json(e) FROM ydental_inventory_event e ORDER BY id',
        'batch': 'SELECT row_to_json(b) FROM ydental_inventory_batch b ORDER BY id',
        'move': 'SELECT id,product_id,uom_id,product_uom_qty,quantity,state,location_id,location_dest_id,ydental_store_id FROM stock_move WHERE ydental_store_id IS NOT NULL ORDER BY id',
        'move_line': 'SELECT id,move_id,product_id,lot_id,uom_id,quantity,location_id,location_dest_id,ydental_store_id FROM stock_move_line WHERE ydental_store_id IS NOT NULL ORDER BY id',
        'quant': 'SELECT id,product_id,lot_id,location_id,quantity,reserved_quantity,ydental_store_id FROM stock_quant WHERE ydental_store_id IS NOT NULL ORDER BY id',
    }.items():
        audit_cr.execute(query)
        signatures[table]=hashlib.sha256(json.dumps(audit_cr.fetchall(),sort_keys=True,default=str).encode()).hexdigest()
    audit_result['ledger_signatures']=signatures
    audit_result['tested_commit']=subprocess.check_output(['git','-C',str(Path(__file__).resolve().parents[1]),'rev-parse','HEAD'],text=True).strip()
audit_result.update(status='PASS',database=env.cr.dbname,time_utc=datetime.now(timezone.utc).isoformat())
path=Path(__file__).resolve().parents[1]/'docs/evidence/s07/invariants'
path.mkdir(parents=True,exist_ok=True)
(path/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')).write_text(json.dumps(audit_result,indent=2)+'\n')
print(json.dumps(audit_result))
