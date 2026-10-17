"""Pure files: isolate fixed Odoo20 log-access merge and verify R0 rollback evidence."""
import ast
import copy
from types import SimpleNamespace
import s10_closeout_v1_contract as c
from s10_closeout_v1_runtime import document_gate


def main():
    model_path = c.CORE_ROOT / 'odoo/orm/models.py'
    module = ast.parse(model_path.read_text())
    function = copy.deepcopy(next(n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == '_write_multi'))
    # Execute only the actual prefix through log_vals merge, before SQL update grouping.
    end = next(i for i, n in enumerate(function.body) if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'updates' for t in n.targets))
    function.body = function.body[:end] + [ast.Return(ast.Name('vals_list', ast.Load()))]
    function.returns = None
    for arg in function.args.args: arg.annotation = None
    code = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    scope = {}
    exec(compile(code, 'ISOLATED_CORE_PREFIX_NO_ODOO_OR_SQL', 'exec'), scope)

    class Probe:
        _log_access = True

        def __init__(self, uid):
            self.env = SimpleNamespace(uid=uid, transaction=SimpleNamespace(),
                                       cr=SimpleNamespace(now=lambda: 'STATIC_ONLY_UTC'))

        def __len__(self): return 1

        def _parent_store_update_prepare(self, values): return None

    merge = scope['_write_multi']
    root = merge(Probe(1), [{'ydental_editor_id': 7}])[0]
    actor = merge(Probe(7), [{'ydental_editor_id': 7}])[0]
    explicit = merge(Probe(1), [{'ydental_editor_id': 7, 'write_uid': 7}])[0]
    assert (root['write_uid'], actor['write_uid'], explicit['write_uid']) == (1, 7, 7)
    relation_source = (c.CORE_ROOT / 'odoo/orm/fields_relational.py').read_text()
    assert 'records = self._filter_not_equal(records, cache_value)' in relation_source
    before = c.read(c.PRIVATE / 'r0-prepare-all-acquire-1-before.json')
    after = c.read(c.PRIVATE / 'r0-prepare-all-acquire-1-after.json')
    doc = next(r for r in after['tables']['ydental_clinical_document'] if r['id'] == 1)
    assert doc['write_uid'] == 1 and doc['ydental_editor_id'] == 7
    gate = document_gate('acquire', 7, 1, doc['ydental_session_id'])
    try: gate(before, after, c.diff(before, after)[0])
    except AssertionError: pass
    else: raise AssertionError('OLD_WRITER_GATE_WAS_RELAXED')
    fixture = copy.deepcopy(after)
    next(r for r in fixture['tables']['ydental_clinical_document'] if r['id'] == 1)['write_uid'] = 7
    gate(before, fixture, c.diff(before, fixture)[0])
    tail = c.read(c.PRIVATE / 'final-tail-RO.json')
    selected = dict(tail, tables={name: tail['tables'][name] for name in before['tables']})
    c.persist('R1-r0-acquire-independent-rollback-proof', before, selected, c.exact)
    result = {'layer': 'ISOLATED_FIXED_CORE_PREFIX_AND_SAVED_R0_EVIDENCE', 'exit_code': 0,
        'core_function_prefix': 'odoo/orm/models.py::_write_multi before SQL grouping',
        'core_source_sha256': c.sha(model_path.read_bytes()),
        'root_flush_default_writer': 1, 'actor_flush_default_writer': 7,
        'explicit_existing_dirty_writer_preserved': True,
        'real_R0_writer1_still_rejected': True, 'synthetic_writer7_fixture_accepted': True,
        'synthetic_fixture_does_not_rewrite_R0': True, 'independent_tail_equals_pre_acquire': True,
        'DB_Odoo_HTTP_Firefox_used': 0, 'scope_of_conclusion': 'collector flush identity defect; no product/core modification'}
    c.save(c.OUT / 'R1-offline-repair-check.json', result)
    print('R1_PURE_FILE_CORE_PREFIX_AND_ROLLBACK_PROOF_PASS')


if __name__ == '__main__':
    main()
