"""One native XML metadata transaction, only on the bound P0-20 clone."""
import sys
import s10_p0_20_contract as c

def main():
    c.checkpoint()
    marker=c.read(c.RUN/'database.json')
    assert marker['database']==c.NAME and marker['source_oid']==c.SOURCE_OID
    assert marker['oid'] not in (2100310,2100325,2100326,2100327)
    assert c.sha((c.RUN/'odoo.conf').read_bytes())==marker['config_sha256']
    assert not (c.PRIVATE/'xml-import-intent.json').exists(), 'NO_IMPORT_RETRY'
    sys.path.insert(0,str(c.CORE_ROOT))
    import odoo.init  # Fixed native bootstrap, as used by odoo.cli.command.
    from odoo.tools import config
    config.parse_config(['-c',str(c.RUN/'odoo.conf'),'--no-http'],setup_logging=True)
    assert config['db_name']==[c.NAME] and not config['update'] and not config['init']
    assert not config.get('import_partial') and not config['test_enable']
    from odoo.orm.registry import Registry
    from odoo.orm.environments import Environment
    from odoo.tools.convert import convert_file
    registry=Registry(c.NAME)
    cr=registry.cursor()
    try:
        before=c.capture_cursor(cr,c.NAME,marker['oid'])
        frozen=c.read(c.PRIVATE/'target-before-rows.json')
        c.persist_review('registry-initial',frozen,before,c.same_snapshot)
        env=Environment(cr,1,{'lang':'en_US'})
        for name,(model,table,ident,xid) in c.IDS.items():
            obj=env.ref('ydental_settlement.'+name)
            assert obj._name==model and obj.id==ident
    except BaseException:
        cr.rollback()
        cr.close()
        raise

    def load():
        c.save(c.PRIVATE/'xml-import-intent.json',{'attempt':1,'file':c.XML,'mode':'update','idref_explicit':True,'uid':1,'backend_pid':before['backend_pid']})
        idref={}
        convert_file(env,'ydental_settlement','views/ydental_settlement_templates.xml',idref,mode='update',noupdate=False)
        env.flush_all()

    c.guarded_import(cr,before,load,lambda:c.capture_cursor(cr,c.NAME,marker['oid']))

if __name__=='__main__':
    main()
