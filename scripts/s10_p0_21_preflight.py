"""Pure-file symbol/dataflow/API and actual storage-comparator counterexamples."""
import ast
import builtins
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import symtable
import s10_p0_21_contract as c


def symbols(path):
    text=path.read_text();tree=symtable.symtable(text,str(path),'exec')
    globals_known=set(dir(builtins))|{'env','__name__','__file__'}|{s.get_name() for s in tree.get_symbols() if s.is_assigned() or s.is_imported() or s.is_namespace()}
    bad=[]
    def scan(t):
        for s in t.get_symbols():
            if s.is_referenced() and s.is_global() and s.get_name() not in globals_known:bad.append(s.get_name())
        for child in t.get_children():scan(child)
    scan(tree);return sorted(set(bad))

def main():
    assert c.git('rev-parse','HEAD')==c.BASE and c.git('rev-parse','HEAD',cwd=c.CORE_ROOT)==c.CORE
    assert not c.RUN.exists()
    idx=c.read(c.ROOT/'docs/evidence/s10-p0-20/sha256-index.json');deps=['scripts/s10_p0_20_fixture.py',*['scripts/s10_p0_20_b_'+n+'.py' for n in ['f1_740','f5_270_200','f2_f3_refund_close','discount_waive','quantity_correction','drug_return','t09_trade','same_company_transfer','audit_integrity','security_matrix','late_close','idempotency']], 'docs/evidence/s10-p0-20/exit-table-final.json']
    for p in deps:
        data=(c.ROOT/p).read_bytes();assert c.sha(data)==idx['files'][p]['sha256'] and data==subprocess.check_output(['git','show',c.BASE+':'+p])
    checks=['fixed referenced P020 Git blobs/SHA read only; no old tests executed']
    undefined={}
    for p in c.ROOT.glob('scripts/s10_p0_21_*.py'):
        compile(ast.parse(p.read_text()),str(p),'exec');bad=symbols(p);undefined[str(p.relative_to(c.ROOT))]=bad;assert not bad,(p,bad)
    assert 'execution' in symbols(c.ROOT/'scripts/s10_p0_20_b_f1_740.py')
    checks.append('all new scenario globals/imports/success path analyzed; old execution defect detected; new real opened_actual execution bound')
    fixtures={'tables':{'account_move':[{'id':1,'company_id':1,'amount_total':'740.00','amount_residual':'0.00','__physical_table__':'account_move','__physical_oid__':12}], 'account_move_line':[{'id':2,'move_id':1,'debit':'740.00','credit':'0.00'}], 'ydental_intake_snapshot':[{'id':1,'ydental_unit_price':'600.00','ydental_price_id':1}], 'ydental_clinical_document':[{'id':1,'state':'pending'}]},'schema':{}}
    good=deepcopy(fixtures);good['tables']['ydental_clinical_document'][0]['state']='confirmed'
    raw,index=c.diff(fixtures,good);c.unchanged_economics(fixtures,good,index);checks.append('stored money unchanged / separate legitimate document state accepted')
    for table,field,value in [('account_move','amount_residual','0.01'),('account_move','company_id',2),('account_move_line','move_id',2),('ydental_intake_snapshot','ydental_price_id',2),('ydental_intake_snapshot','ydental_unit_price','620.00')]:
        bad=deepcopy(good);bad['tables'][table][0][field]=value;_,i=c.diff(fixtures,bad)
        try:c.unchanged_economics(fixtures,bad,i)
        except AssertionError:checks.append('reject stored '+table+'.'+field)
        else:raise AssertionError('UNSAFE_COMPARATOR')
    # Same numerical action IDs in distinct physical children stay separate.
    a={'tables':{'ir_actions':[{'id':1,'__physical_table__':'ir_act_url','name':'a'},{'id':1,'__physical_table__':'ir_act_window','name':'b'}]}};b=deepcopy(a);b['tables']['ir_actions'][1]['name']='c'
    full,index=c.diff(a,b);assert len(index)==1 and index[0]['physical_key']==['public','ir_act_window',1];checks.append('sameID physical inheritance keys preserved without dict overwrite')
    display1={'tables':{'account.move':[{'id':1,'partner_id':[6,'old label']}]}};display2={'tables':{'account.move':[{'id':1,'partner_id':[6,'new label']}]}}
    assert c.diff(display1,display2)[1] and not c.diff(fixtures,fixtures)[1];checks.append('display labels differ independently of identical stored IDs/money; no inference about P020 actual root cause')
    work=c.PRIVATE/('pure-file-rejection-'+str(len(list(c.PRIVATE.glob('pure-file-rejection*')))));work.mkdir()
    oldp,oldo=c.PRIVATE,c.OUT;c.PRIVATE=work/'private';c.OUT=work/'public'
    try:
        try:c.persist('reject',fixtures,bad,c.unchanged_economics)
        except AssertionError:pass
        assert (c.PRIVATE/'reject-before.json').exists() and (c.PRIVATE/'reject-after.json').exists() and (c.PRIVATE/'reject-full-diff.json').exists()
        assert not c.read(c.OUT/'reject-decision.json')['PASS'];checks.append('actual persist function saves full row/column values and redacted index before failed gate')
    finally:c.PRIVATE=oldp;c.OUT=oldo
    proposed=c.read(c.OUT/'proposed-product-contract.json')
    for target,f in proposed['files'].items():
        p=c.ROOT/f['proposed_file'];assert c.sha(p.read_bytes())==f['sha256']
        if p.suffix=='.py':assert not symbols(p),(p,symbols(p))
    original_service=(c.PRIVATE/'proposed/ydental_settlement_original_service.py').read_text()
    cls=next(n for n in ast.parse(original_service).body if isinstance(n,ast.ClassDef));getter=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_bill_original_bytes')
    assert not any(isinstance(n,ast.Attribute) and n.attr in ('_pdf','_render_qweb_pdf') for n in ast.walk(getter));checks.append('retake has no render fallback; checksum/attachment identity and live source/export guard required')
    core=(c.CORE_ROOT/'odoo/addons/base/models/ir_binary.py').read_text();assert core.index('verify_limited_field_access_token')<core.index('if record._can_return_content')
    checks.append('fixed core native binary limited-token early bypass covered before super _find_record')
    contract={'economic_storage':'all actual catalog columns in account/stock/inventory/treatment/settlement source-payment-refund-close-correction-trade and price snapshot/price, all relationship rows; stored computed totals/residual retained','numeric':'PostgreSQL exact JSON numeric parsed Decimal; no epsilon/rounding-away','physical_key':['schema','actual tableoid/regclass','id or full relationship tuple'],'display':'explicit id/display_name and selected Many2one tuple only; independent before/after full values and diff, never gate economics','document_actions':'acquire/confirm/correct/release/PDF/original generation/retake separate flushed snapshots, full private diff before assertions','commit':'owned cursor, prior full snapshot and pending marker private only, commit intent/returned/unknown durable; independent new RO/RR exact row verification before success marker','old_root_cause':'P020 missing transient fields permanently UNKNOWN'}
    c.save(c.OUT/'stable-facts-contract.json',contract)
    c.save(c.OUT/'display-field-contract.json',{'fixed_sources':['odoo/orm/models.py:_compute_display_name','odoo/orm/fields_relational.py:Many2one display conversion','ydental_clinical/models/ydental_clinical_document.py:name/state/version stored separately'],'actual observed changes':'must inspect runtime before/after display diff before explanation; never infer P020 cause'})
    c.save(c.OUT/'static-result.json',{'checks':checks,'count':len(checks),'exit_code':0,'global_symbol_analysis':undefined,'old_dependency_SHA':{p:idx['files'][p]['sha256'] for p in deps},'database_HTTP_Firefox_budget_used':0,'pure_file_only':True})
    print(json.dumps({'checks':len(checks),'exit_code':0,'runtime_budget':0}))
if __name__=='__main__':main()
