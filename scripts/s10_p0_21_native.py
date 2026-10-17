"""Native normal registry loader; owned transaction and independent checkpoint proof."""
import json
import os
import sys
import s10_p0_21_contract as c
from s10_p0_21_runtime import snapshot,checkpoint
from s10_p0_21_control import SCENARIOS
c.gate();name=sys.argv[1];assert name in SCENARIOS+['configure','audit-before-upgrade','audit-after-upgrade']
assert os.environ['YDENTAL_S10_RUN_DIR']==str(c.RUN)
sys.path.insert(0,str(c.CORE_ROOT))
import odoo.init
from odoo.tools import config
config.parse_config(['-c',str(c.RUN/'odoo.conf'),'--no-http'],setup_logging=True)
assert config['db_name']==[c.NAME] and not config['update'] and not config['init']
from odoo.orm.registry import Registry
from odoo.orm.environments import Environment
registry=Registry(c.NAME)
with registry.cursor() as cr:
    env=Environment(cr,1,{'lang':'zh_CN','mail_create_nolog':True,'mail_notrack':True})
    if name=='configure':
        assert not env['ydental.treatment.fee'].search_count([]) and not env['ydental.access.store'].search_count([])
        if not env.company.chart_template:env['account.chart.template'].try_loading('generic_coa',env.company)
        base=env.ref('base.group_user');old=set(base.implied_ids.ids)
        features=['stock.group_stock_multi_warehouses','stock.group_stock_multi_locations','product.group_product_pricelist']
        allowed={env.ref(x).id for x in features}
        for x in features:base._apply_group(env.ref(x))
        assert set(base.implied_ids.ids)-old<=allowed
        c.save(c.OUT/'initial-feature-configuration.json',{'feature_XMLIDs':features,'added_group_edges':sorted(set(base.implied_ids.ids)-old),'initial_only':True,'ordinary_roles_not_administrators':True})
        checkpoint(cr,env,'configuration')
    elif name.startswith('audit-'):
        s=snapshot(env,full=True);c.save(c.PRIVATE/(name+'-full.json'),s)
        if name=='audit-after-upgrade':
            before=c.read(c.PRIVATE/'audit-before-upgrade-full.json')
            def upgrade_gate(a,b,index):
                assert a['schema']==b['schema'],'SCHEMA_CHANGED_ON_FINAL_PRODUCT_UPGRADE'
                forbidden=[r for r in index if c.economic(r['table']) or r['table'].startswith(('ydental_','res_users','res_groups','res_company','res_partner','hr_','resource_')) or r['table']=='ir_attachment']
                assert not forbidden,('UPGRADE_PROTECTED_DATA_DRIFT',[(r['table'],r['columns']) for r in forbidden])
                return {'protected_business_identity_permission_attachment_rows_exact':True,'all_other_metadata_full_diff_retained':True}
            c.persist('final-product-upgrade',before,s,upgrade_gate)
        cr.rollback()
    else:
        script=c.ROOT/('scripts/s10_p0_21_b_'+name+'.py')
        exec(compile(script.read_text(),str(script),'exec'),{'env':env,'__name__':'__p021_native_synthetic_scenario__'})
