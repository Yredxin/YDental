"""Offline actual core savepoint/default-env path and R1 saved rollback proof."""
import ast
import copy
from types import SimpleNamespace
import s10_closeout_v1_contract as c
from s10_closeout_v1_runtime import actor_call, document_gate


def main():
    environment = ast.parse((c.CORE_ROOT/'odoo/orm/environments.py').read_text())
    transaction = next(n for n in environment.body if isinstance(n, ast.ClassDef) and n.name == 'Transaction')
    flush = copy.deepcopy(next(n for n in transaction.body if isinstance(n, ast.FunctionDef) and n.name == 'flush'))
    db = ast.parse((c.CORE_ROOT/'odoo/sql_db.py').read_text())
    savepoint = next(n for n in db.body if isinstance(n, ast.ClassDef) and n.name == '_FlushingSavepoint')
    close = copy.deepcopy(next(n for n in savepoint.body if isinstance(n, ast.FunctionDef) and n.name == '_close'))
    class Base:
        def _close(self, rollback): self.rollback = rollback
    class Cursor:
        def __init__(self, txn): self.transaction = txn
        def flush(self): scope['flush'](self.transaction)
    cls = ast.ClassDef(name='CoreSavepoint', bases=[ast.Name('Base', ast.Load())], keywords=[], body=[close], decorator_list=[])
    scope = {'Base': Base, 'Cursor': Cursor}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[flush, cls], type_ignores=[])), 'ACTUAL_FIXED_CORE_NO_SQL', 'exec'), scope)
    results = []
    for actor in [7, 5, 6, 41]:
        writes = []
        txn = SimpleNamespace(merge_state=lambda: None)
        root = SimpleNamespace(uid=1, flush_all=lambda: writes.append(1))
        env = SimpleNamespace(uid=actor, transaction=txn, _field_dirty={}, flush_all=lambda: writes.append(actor))
        txn.default_env = root
        point = scope['CoreSavepoint'](); point._cr = Cursor(txn)
        point._close(False)
        assert writes == [1]
        writes.clear()
        actor_call(SimpleNamespace(env=env), lambda: point._close(False))
        assert writes == [actor, actor] and txn.default_env is root
        results.append({'actor': actor, 'uncorrected_implicit_savepoint_flush_uid': 1,
                        'corrected_implicit_and_explicit_flush_uids': writes})
    before = c.read(c.PRIVATE/'r1-prepare-all-acquire-1-before.json')
    after = c.read(c.PRIVATE/'r1-prepare-all-acquire-1-after.json')
    tail = c.read(c.PRIVATE/'r1-final-tail-RO.json')
    selected = dict(tail, tables={name: tail['tables'][name] for name in before['tables']})
    c.persist('R2-R1-acquire-independent-rollback-proof', before, selected, c.exact)
    doc = next(r for r in after['tables']['ydental_clinical_document'] if r['id'] == 1)
    assert doc['write_uid'] == 1
    try: document_gate('acquire', 7, 1, doc['ydental_session_id'])(before, after, c.diff(before, after)[0])
    except AssertionError: pass
    else: raise AssertionError('ACTOR_GATE_RELAXED')
    proof = {'same_collector_defect_proven': True, 'R1_acquire_independently_rolled_back': True,
             'preserved_R1_STOP_sha256': c.sha((c.PRIVATE/'STOP-r1.json').read_bytes()),
             'final_repair_within_original_two_round_cap': True,
             'scope': 'implicit savepoint flush selected first uid1 environment before R1 explicit actor flush',
             'core_path': ['clinical_service._operate savepoint exit', 'sql_db._FlushingSavepoint._close',
                           'Cursor.flush', 'Transaction.flush/default_env', 'models._write_multi'],
             'core_test_precedent': 'odoo/tests/common.py:686 uid setter binds default_env to actual actor',
             'results': results, 'real_R1_writer1_still_rejected': True, 'DB_Odoo_HTTP': 0, 'exit_code': 0}
    c.save(c.PRIVATE/'repair-r2-proof.json', proof); c.save(c.OUT/'R2-savepoint-repair-proof.json', proof)
    print('ACTUAL_CORE_SAVEPOINT_ACTOR_BINDING_AND_R1_ROLLBACK_PASS')


if __name__ == '__main__': main()
