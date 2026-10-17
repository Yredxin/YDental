"""Native registry for B only; business actions in legal ordinary user services."""
import json
import os
from pathlib import Path
import sys
import s10_p0_20_contract as c
from s10_p0_20_b_control import NAME,RUN,SCENARIOS

def snapshot(env,label):
    cr=env.cr
    cr.execute(c.CATALOG_SQL);cols={}
    for table,col in cr.fetchall():cols.setdefault(table,[]).append(col)
    tables={}
    for table,fields in cols.items():
        cr.execute('SELECT to_jsonb(t)::text FROM public."'+table+'" t ORDER BY '+('"id"' if 'id' in fields else 'to_jsonb(t)::text'))
        tables[table]=[json.loads(r[0]) for r in cr.fetchall()]
    full={'tables':tables,'schema':cols}
    c.save(c.PRIVATE/('B-'+label+'-rows.json'),full)
    c.save(c.OUT/('B-'+label+'-signatures.json'),{'tables':{t:{'rows':len(rows),'sha256':c.sha(c.canonical(rows).encode())} for t,rows in tables.items()},'full_private_snapshot_saved':True})
    return full

c.checkpoint();name=sys.argv[1]
assert name in SCENARIOS+['snapshot-before-upgrade','snapshot-after-upgrade']
assert os.environ['YDENTAL_S10_RUN_DIR']==str(RUN)
sys.path.insert(0,str(c.CORE_ROOT))
import odoo.init
from odoo.tools import config
config.parse_config(['-c',str(RUN/'odoo.conf'),'--no-http'],setup_logging=True)
assert config['db_name']==[NAME] and not config['init'] and not config['update']
from odoo.orm.registry import Registry
from odoo.orm.environments import Environment
registry=Registry(NAME)
with registry.cursor() as cr:
    marker=c.read(RUN/'database.json')
    cr.execute(c.IDENTITY_SQL);db,oid,cluster,pid=cr.fetchone();assert (db,oid,cluster)==(NAME,marker['oid'],c.CLUSTER)
    env=Environment(cr,1,{'lang':'zh_CN','mail_create_nolog':True,'mail_notrack':True})
    if name.startswith('snapshot-'):
        after=snapshot(env,name)
        if name=='snapshot-after-upgrade':
            before=c.read(c.PRIVATE/'B-snapshot-before-upgrade-rows.json')
            # Freeze existing business, security and documents, allow only native installation metadata.
            protected=[t for t in before['tables'] if t.startswith(('account_','stock_','ydental_','res_users','res_groups','res_company','res_partner','hr_','resource_'))]
            raw,index=c.full_diff(before,after)
            c.save(c.PRIVATE/'B-upgrade-full-diff.json',raw)
            c.save(c.OUT/'B-upgrade-full-diff-index.json',{'changes':index,'saved_before_gate':True})
            changed=[t for t in protected if before['tables'][t]!=after['tables'][t]]
            c.save(c.OUT/'B-upgrade-protected-diff.json',{'protected_tables':protected,'changed_tables':changed})
            assert not changed,('UPGRADE_PROTECTED_DRIFT',changed)
        cr.rollback()
    else:
        if name=='f1_740':
            assert not env['ydental.treatment.fee'].search_count([])
            if not env.company.chart_template:env['account.chart.template'].try_loading('generic_coa',env.company)
            base_user=env.ref('base.group_user')
            allowed=[env.ref(x) for x in ['stock.group_stock_multi_warehouses','stock.group_stock_multi_locations','product.group_product_pricelist']]
            old=set(base_user.implied_ids.ids)
            for feature in allowed:base_user._apply_group(feature)
            assert set(base_user.implied_ids.ids)-old <= {g.id for g in allowed}
            c.save(c.OUT/'B-native-feature-configuration.json',{'purpose':'normal new-B multi-warehouse/location and pricelist setup prerequisite; no source permissions or business guard changes','base_group':base_user.id,'added_implied_ids':sorted(set(base_user.implied_ids.ids)-old),'allowed_feature_XMLIDs':['stock.group_stock_multi_warehouses','stock.group_stock_multi_locations','product.group_product_pricelist'],'actor':'new-B native configuration administrator only'})
            cr.commit() # Native synthetic initial chart/feature configuration only, no business facts.
        script=c.ROOT/('scripts/s10_p0_20_b_'+name+'.py')
        code=compile(script.read_text(),str(script),'exec')
        exec(code,{'env':env,'__name__':'__p020_new_B_scenario__'})
