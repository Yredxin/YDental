"""P0-15 file-only audit. Never import addons or execute historical entrypoints.

Generate: python3 scripts/s10_p0_15_static_audit.py --generate
Verify:   python3 scripts/s10_p0_15_static_audit.py --verify
Only Git read commands and files are used. The new batch's GitHub receipts are
inputs to generation; verification can run entirely from the delivered files.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 'a66c9dfd4b65573a27ff3e45733a87103f17bf32'
GAP02 = '0c972e1949191d62d84536f987a40f26dba57e03'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
OUT = ROOT / 'docs/evidence/s10-p0-15'
PRIVATE = ROOT / '.local/s10-p0-15'
PREFIX = 'https://github.com/Yredxin/YDental/blob/' + BASE + '/'
ZERO = dict.fromkeys(('DB_SQL_CONNECTION', 'CREATE', 'ODOO_HTTP', 'FIREFOX',
    'BUSINESS_GET', 'BUSINESS_POST', 'ODOO_SHELL_INSTALL_UPGRADE_INIT_TEST',
    'DIRECT_BUSINESS_ORM', 'FUNDS_FEE_STOCK_ATTACHMENT_PDF_WRITE', 'SUDO',
    'ISSUE_PROJECT_STATE_CHANGE', 'MERGE_DEPLOY_S11'), 0)
SPECS = {
 'clinical': ('ydental_clinical/models/ydental_clinical_service.py',
   '_access _document _content _snapshot _read _audit _operate _eligible_responsible _valid_editor _acquire _held _heartbeat _clear_editor _release _append _save _confirm _correct'),
 'queue': ('ydental_queue/models/ydental_queue_service.py', '_locks _settings _connection _held'),
 'intake': ('ydental_intake/models/ydental_intake_service.py', '_lock _all_locks'),
 'patient': ('ydental_patient/models/ydental_patient_service.py', '_lock'),
 'supply': ('ydental_supply/models/ydental_supply_service.py', '_lock'),
 'access': ('ydental_access/models/ydental_access_service.py', '_scope _membership _levels _check _audit_values _audit'),
 'audit': ('ydental_access/models/ydental_access_audit.py', 'write unlink'),
 'treatment': ('ydental_treatment/models/ydental_treatment_service.py',
   '_operate _serving _medical _quote _price_values _event _bookkeep _settle _correct _return_material _remaining _pharmacy _dispense'),
 'inventory': ('ydental_inventory/models/ydental_inventory_service.py',
   '_lock _operate _event _move _return _verify _source_action'),
 'exam': ('ydental_exam/models/ydental_exam_service.py', '_store _line _editor _version _perform _confirm _correct _operate'),
 'settlement': ('ydental_settlement/models/ydental_settlement_service.py',
   '_access _invoice _bill _bill_correction _close_guard _close_guard_any _refund_execute _report_payload _validate_pdf_scope _pdf'),
 'print': ('ydental_print/models/ydental_print_service.py', '_authorize _job _generate _deliver _operate'),
}
EXTRA = [
 'ydental_clinical/controllers/clinical.py', 'ydental_clinical/static/src/document/document.js',
 'ydental_clinical/views/ydental_clinical_templates.xml',
 'ydental_treatment/controllers/treatment.py', 'ydental_treatment/static/src/workbench/workbench.js',
 'ydental_treatment/views/ydental_treatment_templates.xml', 'ydental_exam/controllers/exam.py',
 'ydental_inventory/controllers/inventory.py', 'ydental_settlement/controllers/settlement.py',
 'ydental_settlement/views/ydental_settlement_templates.xml',
 'ydental_settlement/report/ydental_settlement_reports.xml',
 'ydental_settlement/report/ydental_settlement_templates.xml', 'scripts/s10_e2e_w3_browser.py',
 'ydental_print/models/ydental_print_job.py', 'ydental_print/controllers/printing.py',
 'scripts/s10_e2e_w3_prepare.py', 'ydental_treatment_test/tests/common.py',
 'ydental_treatment_test/tests/treatment_common.py',
 'ydental_access/models/ydental_access_grant.py', 'ydental_access/models/ydental_access_membership.py',
 'ydental_access/security/ir.access.csv', 'ydental_access/security/ydental_access_security.xml',
 'ydental_clinical/security/ir.access.csv', 'ydental_clinical/models/ydental_clinical_version.py',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def git(*args, cwd=ROOT):
    # This helper has no shell and a fixed read-only subcommand allowlist.
    assert args[0] in ('show', 'rev-parse', 'branch', 'diff', 'ls-files', 'status')
    return subprocess.check_output(['git', *args], cwd=cwd)


def read(path):
    data = (ROOT / path).read_bytes()
    assert git('show', BASE + ':' + path) == data, 'fixed source drift: ' + path
    return data


def data(path):
    return json.loads(read(path))


def dump(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def source_contract():
    sources, methods = {}, {}
    for group, (path, names) in SPECS.items():
        raw = read(path)
        text = raw.decode()
        nodes = [n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.FunctionDef)]
        sources[path] = {'sha256': sha(raw), 'fixed_git': BASE, 'url': PREFIX + path}
        for name in names.split():
            matches = [n for n in nodes if n.name == name]
            assert len(matches) == 1, (path, name)
            node = matches[0]
            body = '\n'.join(text.splitlines()[node.lineno - 1:node.end_lineno])
            methods[group + '.' + name] = {'path': path, 'line': node.lineno,
                'end_line': node.end_lineno, 'method_sha256': sha(body.encode()),
                'url': PREFIX + path + '#L' + str(node.lineno), 'source': body}
    for path in EXTRA:
        raw = read(path)
        sources[path] = {'sha256': sha(raw), 'fixed_git': BASE, 'url': PREFIX + path}

    def has(key, *parts):
        body = methods[key]['source']
        assert all(p in body for p in parts), (key, parts)

    # Assertions test concrete source guards. They are STATIC checks, never an
    # emulation of business success, permissions, rendering or native stability.
    has('clinical._append', "kind == 'correct' and doc.state != 'confirmed'", 'expected_version',
        'ydental_previous_id', "'ydental_author_id': self.env.uid", "'ydental_reason': reason")
    has('clinical._correct', "'correct'", 'reason', '_held(')
    has('clinical._acquire', 'ydental_responsible_id', '_eligible_responsible', 'ydental_editor_id')
    has('clinical._held', '_valid_editor', '_connection', 'connection.key_hash', 'digest(editor_token)')
    has('treatment._correct', "('treatment', 'chairside')", 'net < 0', 'delta < 0 and materials')
    has('treatment._event', 'parent.ydental_price_snapshot_id', 'parent.ydental_price_review_id')
    has('treatment._settle', 'parent_fee', "'ydental_quantity': event.ydental_quantity",
        "currency.round(event.ydental_quantity * price['unit_price'])")
    has('treatment._remaining', "('ydental_kind', '=', 'prescription')", "sum(events.mapped('ydental_quantity'))")
    has('inventory._return', "('replenishment', 'prescription')", 'ydental_quarantine_id',
        'ydental_customer_id', 'parent.ydental_quantity')
    has('settlement._bill_correction', "'out_refund'", 'amount_residual', 'actually_refunded')
    has('settlement._bill', 'fee.ydental_amount < 0', '_bill_correction', '_close_guard_any')
    has('settlement._report_payload', "_check('export', 'write')", 'amount_residual', 'received_partials')
    has('settlement._pdf', 'report_pdf_no_attachment=True', '_render_qweb_pdf', "_audit('report_download'")
    has('print._job', 'ydental_expires_at', 'ydental_source_digest', 'self._source(')
    has('print._generate', 'timedelta(minutes=15)', 'ydental_pdf')
    has('print._deliver', 'ydental_pdf', 'ydental_pdf_digest')
    clinical_calls = {}
    for key in ('clinical._correct', 'clinical._append', 'clinical._save', 'clinical._confirm',
                'treatment._return_material', 'exam._correct'):
        tree = ast.parse('class Holder:\n' + '\n'.join('    ' + s for s in methods[key]['source'].splitlines()))
        calls = sorted({n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)})
        clinical_calls[key] = calls
    assert not set(clinical_calls['clinical._correct'] + clinical_calls['clinical._append']) & {
        '_bookkeep', '_settle', '_bill_correction', '_refund_execute', '_move', '_source_action'}
    assert not set(clinical_calls['treatment._return_material']) & {'_settle', '_bill_correction', '_refund_execute'}
    assert not set(clinical_calls['exam._correct']) & {'_event', '_settle', '_bookkeep', '_move'}
    js = read(EXTRA[1]).decode()
    for s in ('900', "state !== 'confirmed'", 'terminalPending', "await action('release'", 'needsReconcile', 'heartbeat'):
        assert s in js
    return {'layer': 'STATIC_REVIEW / READONLY_SOURCE_FROM_FIXED_GIT', 'fixed_git': BASE,
        'methods': methods, 'files': sources, 'direct_call_sets': clinical_calls,
        'limitations': 'AST/literal guards prove fixed source structure only; no dynamic actor, ORM, SQL, HTTP, concurrency or PDF PASS.'}


def generate():
    assert git('branch', '--show-current').decode().strip() == BRANCH
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent).decode().strip() == CORE
    assert not git('diff', '--name-only', cwd=ROOT.parent).strip()
    checkpoint = json.loads((PRIVATE / 'preflight-api-readback.json').read_text())
    body = (PRIVATE / 'preflight-body.txt').read_bytes()
    assert checkpoint['verbatim_equal'] and checkpoint['comment_id'] == 6214014587
    assert sha(body) == checkpoint['body_sha256']
    assert len(body) == checkpoint['utf8_bytes'] and len(body.decode()) == checkpoint['characters']
    dump('preflight-api-readback.json', checkpoint)
    (ROOT / 'docs/s10-p0-15-preflight.md').write_bytes(body)
    authority = {'base': BASE, 'core': CORE, 'branch': BRANCH,
        'authorization': 6213938772, 'P014_ruling': 6213877494, 'issues': {}, 'comments': {}}
    for number in (23, 34, 35):
        issue = json.loads((PRIVATE / f'issue{number}.json').read_text())
        authority['issues'][str(number)] = {'state': issue['state'], 'body_sha256': sha(issue['body'].encode()),
            'url': issue['url'], 'comments': issue['comments']}
    for number, count in ((23, 3), (34, 228)):
        comments = json.loads((PRIVATE / f'comments{number}.json').read_text())
        assert len(comments) == count
        authority['comments'][str(number)] = [{'id': c['id'], 'url': c['url'],
            'characters': len(c['body']), 'body_sha256': sha(c['body'].encode()),
            'updated_at': c['updated_at']} for c in comments]
    for name in ('auth', 'ruling'):
        obj = json.loads((PRIVATE / (name + '.json')).read_text())
        authority[name] = {'id': obj['id'], 'body_sha256': sha(obj['body'].encode()), 'url': obj['html_url']}
    assert json.loads((PRIVATE / 'remote-ref.json').read_text())['object']['sha'] == BASE
    dump('github-start.json', authority)
    contract = source_contract()
    dump('static-action-contract.json', contract)

    coverage_path = 'docs/evidence/s10-p0-10/coverage.json'
    old = data(coverage_path)
    assert git('show', GAP02 + ':' + coverage_path) == read(coverage_path)
    assert len(old['rows']) == 22
    stages = {}
    final_shas = {'11': '0b64b1b143ca99dac0404d202d410a782d08421f',
        '12': 'cf6692c27d48ebabf1b7d4f3ab1ef99ef4cfef74',
        '13': '6c64403f9c015c669e50e750aff6e0e7a2eab3c0', '14': BASE}
    comments = {'11': [6209987413, 6210167613], '12': [6210910862, 6211057301],
        '13': [6211754121, 6211928330], '14': [6212629752, 6213877494]}
    for stage in ('11', '12', '13', '14'):
        path = f'docs/evidence/s10-p0-{stage}/verification.json'
        verification = data(path)
        assert git('show', final_shas[stage] + ':' + path) == read(path)
        stages['P0-' + stage] = {'fixed_commit': final_shas[stage], 'comments': comments[stage],
            'path': path, 'sha256': sha(read(path)), 'historical_verification': verification,
            'business_effect': 'SCOPED_TECH_PASS' if stage == '14' else 'BLOCKED',
            'new_execution_in_P015': 'NOT_RUN'}
    summaries = {
        'F4': 'P0-14只补结清后既存原文确认v2→v3及费库款零变；文字correct/数量/退药/原版/同Firefox全链均未补。',
        'T08': '新增仅原责任人原文确认及同源钱货不变；R3数量更正/退药分别是不同patient/store，不能拼W5全链。',
        'T11': 'P0-11至14没有PDF；P0-14 confirmed3不是票据或历史原版；W5当前paid740/0首份账单仍NOT_RUN。',
        'T12': '只接受P0-14一个确认子动作；W4 metadata STOP/W5 exit1 final_audit NOT_RUN/R3 SIGSEGV UNKNOWN永久保留。',
        'T15': 'P0-14未调价620、未重印；W5 price600旧快照和原版缺失不因新文书v3改变。',
    }
    rows = []
    for row in old['rows']:
        rid = row['id']
        impact = 'SCOPED_TECH_PASS' if rid in ('F4', 'T08') else 'BLOCKED' if rid == 'T12' else 'NOT_RUN'
        rows.append({'id': rid, 'gap02_original_row': row, 'gap02_original_row_sha256': sha(canonical(row)),
            'gap02_status_preserved': row['gap02_row_status'], 'gap03_row_status': row['gap02_row_status'],
            'P011': {'source': 'P0-11', 'impact': 'BLOCKED', 'clinical_business': 'NOT_RUN', 'scope': '旧W5只读资格/643表，仅保全；检查点缺失STOP'},
            'P012': {'source': 'P0-12', 'impact': 'BLOCKED', 'clinical_business': 'NOT_RUN', 'scope': '离线合同冲突；执行预算全0'},
            'P013': {'source': 'P0-13', 'impact': 'BLOCKED', 'clinical_business': 'NOT_RUN', 'scope': '双源只读/单克隆/登录首GET保全，acquire/confirm/release均0'},
            'P014': {'source': 'P0-14', 'impact': impact,
                'accepted_subassertion': 'user7原文确认confirmed3、旧源643及克隆禁写627表全等' if rid in ('F4', 'T08', 'T12') else None,
                'scope': summaries.get(rid, '本行没有新增业务覆盖；旧状态、限定子证据及剩余缺口全部保留。')},
            'policy_impact': 'POLICY_PENDING' if rid in ('F1','F2','F3','F5','T02','T06','T09','T11','T15','T16') else 'NOT_RUN',
            'P015_layer': 'STATIC_REVIEW', 'P015_new_business': 'NOT_RUN'})
    counts = dict(Counter(r['gap03_row_status'] for r in rows))
    assert counts == {'SCOPED_ACCEPTED': 7, 'PARTIAL': 14, 'BLOCKED': 1}
    dump('gap03-delta.json', {'gap02_fixed_commit': GAP02, 'gap02_path': coverage_path,
        'gap02_file_sha256': sha(read(coverage_path)), 'row_count': 22,
        'status_counts': counts, 'FULL_PASS': 0, 'new_sources': stages, 'rows': rows,
        'rule': '原GAP02整行逐字段保留；新增来源列不是整行通过，P0-14裁定直接引用，不重审。'})
    lineage = data('docs/evidence/s10-p0-10/same-source-lineage.json')
    fields = data('docs/evidence/s10-p0-10/field-lineage.json')
    p14clone = data('docs/evidence/s10-p0-14/clone.json')
    p14before = data('docs/evidence/s10-p0-14/source-before.json')
    p14 = stages['P0-14']['historical_verification']
    assert p14clone['source_oid'] == 2100310 and p14clone['oid'] == 2100326
    assert p14clone['all_643_tables_exact'] and p14['source_before_after643_exact']
    assert p14['doc_state'] == 'confirmed' and p14['doc_version'] == 3
    assert p14before['all_table_signatures']['ydental_print_job']['rows'] == 0
    dump('source-lineage.json', {'fixed_git': BASE, 'GAP02_original_lineage': lineage,
        'GAP02_original_field_lineage': fields,
        'W5_to_P014': {'parent_database': 'ydental_s10_test_20261015073500_e50f4a71',
            'parent_oid': 2100310, 'clone_database': p14clone['database'], 'clone_oid': 2100326,
            'cluster': p14before['cluster'], 'config_sha256': p14clone['config_sha256'],
            'marker_sha256': p14clone['marker_sha256'], 'initial643_equal': True,
            'source_before_after643_equal': True, 'clone_locked627_equal': True,
            'proof_paths': ['docs/evidence/s10-p0-14/clone.json', 'docs/evidence/s10-p0-14/verification.json'],
            'GPT_ruling': 6213877494, 'current_source_read_in_P015': False},
        'version_location': {'permanent_W5': 'pending/version2 (固定只读证据，不是本批当前读取)',
            'P014_clone_only': 'confirmed/version3; permanently excluded as future template by current authorization'},
        'identity_rule': 'database+OID+cluster+marker/config+same-source signatures; numeric IDs alone are insufficient',
        'text_correction_source_status': 'NOT_AUTHORIZABLE_PENDING_SOURCE',
        'missing': '独立合法已确认的纯合成父文书及可审核的非医疗更正文案；不得复用P014或重放W5 doc1 confirm',
        'R3_W_independent': True, 'cross_family_business_splicing': False})
    sql = data('docs/evidence/s10-p0-10/read-only-sql.json')['sources']['W5']
    objects = sql['objects']
    grant_projection = objects['ydental_access_grant']
    missing_grant_fields = sorted({'ydental_membership_id','ydental_category','ydental_level'} - set(grant_projection[0]))
    assert missing_grant_fields
    steps_tree = ast.parse(read('scripts/s10_e2e_w3_browser.py'))
    steps = next(n.value for n in steps_tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'STEPS' for t in n.targets))
    step_names = [n.elts[0].value for n in steps.elts]
    assert len(step_names) == 23
    dump('remaining-gaps.json', {
        'clinical_correct': {'status': 'NOT_AUTHORIZABLE_PENDING_SOURCE', 'source_reason': '唯一confirmed3在禁止复用P014克隆；旧W5仍pending2',
            'code_change': 'clinical纯文字correct本身已有；来源准备与合法更正内容未冻结',
            'timer': '900ms autosave只在非confirmed触发；2s heartbeat需单独预算，不能照抄P014 heartbeat0'},
        'quantity_correction': {'status': 'NOT_RUN', 'supported': ['treatment','chairside'],
            'prescription_quantity_edit': '固定_correct拒绝prescription；若需该功能须另行产品授权',
            'future_blockers': '当前serving/本人lease、文书CAS、源kind、原始快照、材料/库存/并发/跨日店会锁须单独核实'},
        'physical_return': {'status': 'NOT_RUN', 'supported_stock_parents': ['replenishment','prescription'],
            'R3_only': 'inventory4→19 patient1/store1；不是R3数量event13→14 patient4/store7，更不是W5',
            'not_automatic': ['fee reduction','cash refund','usable stock release']},
        'original_pdf': {'status': 'NOT_AUTHORIZABLE_PENDING_SOURCE',
            'job_count_all_five_historical_sources': 0, 'P014_source_job_count': 0,
            'W5_existing_clinical_pdf_bytes': sql['existing_clinical_pdf_bytes'],
            'R3_external_pdfs_exist_in_fixed_index': True,
            'R3_external_pdfs_opened_in_P015': False,
            'settlement_pdf': '每次根据当前业务payload渲染；no attachment；无原版取回endpoint',
            'print_job': '临床/处方/consent短期数据库字节15min；不是结算票据或S12永久原件',
            'absence_scope': '只证明已投影的来源/固定索引没有W5同源可用原版，不能推广全系统PDF不存在'},
        'current_bill_candidate': {'status': 'NOT_AUTHORIZABLE_PENDING_SOURCE',
            'actor': 5, 'store': 1, 'company': 1, 'invoice': 1, 'paid': 740, 'residual': 0,
            'actor_membership_historical': [x for x in objects['ydental_access_membership'] if x['ydental_user_id'] == 5 and x['ydental_store_id'] == 1],
            'missing_grant_projection_fields': missing_grant_fields,
            'fixture_intent': ['scripts/s10_e2e_w3_prepare.py:51', 'ydental_treatment_test/tests/common.py:41'],
            'minimal_prerequisite': '先独立授权一个W5严格只读资格/源投影门禁，补store1/user5在职/公司/settlement read与export write展开grant及原生PDF模块/模板已安装的证据；不CREATE/login/render'},
        'T12': {'status': 'BLOCKED', 'complete_same_Firefox23_steps': 'NOT_RUN/PREVIOUSLY_NOT_PASSED',
            'historical23_step_names': step_names, 'step_source': 'scripts/s10_e2e_w3_browser.py:28',
            'preserved_stops': ['W4 metadata 682 write_date rows/dependency loading STOP',
                'W5 browser exit1/browser-complete absent/final_audit NOT_RUN',
                'R3 registry Native SIGSEGV exit-11/other guard-2; root cause UNKNOWN'],
            'missing': ['same-source end-to-end native 23 steps', 'complete S08/S09 real HTTP regressions',
                'text/quantity/physical return/original PDF combined invariant evidence'],
            'P014_effect': '一个确认子断言，不能抵销上述STOP或证明引擎稳定修复'},
        'policy': {'status': 'POLICY_PENDING', 'items': ['生产科目/税/币种配置', '银行或渠道实际到账', 'S12正式税务原件', 'S13最终用户效果验收']},
        'P015_actual_budget': ZERO})


def verify():
    assert git('branch', '--show-current').decode().strip() == BRANCH
    head = git('rev-parse', 'HEAD').decode().strip()
    assert head == BASE or git('rev-parse', 'HEAD^').decode().strip() == BASE
    allowed = ('docs/evidence/s10-p0-15/', 'scripts/s10_p0_15_', 'docs/s10-p0-15-')
    for line in git('status', '--porcelain', '--untracked-files=all').decode().splitlines():
        assert line[:2] in ('??', 'A '), 'unexpected working tree mutation: ' + line
        assert line[3:].startswith(allowed), 'path outside authorization: ' + line
    delta = json.loads((OUT / 'gap03-delta.json').read_text())
    original = data('docs/evidence/s10-p0-10/coverage.json')
    assert len(delta['rows']) == 22 and [r['id'] for r in delta['rows']] == [r['id'] for r in original['rows']]
    for saved, row in zip(delta['rows'], original['rows']):
        assert saved['gap02_original_row'] == row
        assert saved['gap02_original_row_sha256'] == sha(canonical(row))
        assert saved['gap03_row_status'] == row['gap02_row_status']
    assert json.loads((OUT / 'static-action-contract.json').read_text()) == source_contract()
    remaining = json.loads((OUT / 'remaining-gaps.json').read_text())
    package = json.loads((OUT / 'next-work-package.json').read_text())
    assert remaining['T12']['status'] == 'BLOCKED' and len(remaining['T12']['historical23_step_names']) == 23
    assert package['ready_business_count'] == 0 and package['selected_candidate_count'] == 1
    assert package['execution_authorized_by_P015'] is False
    assert len(package['ordered_backups']) <= 2
    assert len(package['selected_candidate']['assertions']) == 4
    files = sorted([p for p in (ROOT / 'docs').glob('s10-p0-15-*.md')] +
        [p for p in (ROOT / 'scripts').glob('s10_p0_15_*.py')] +
        [p for p in OUT.iterdir() if p.is_file() and p.name not in ('sha256-index.json', 'verification.json')])
    checkpoint = json.loads((OUT / 'preflight-api-readback.json').read_text())
    assert sha((ROOT / 'docs/s10-p0-15-preflight.md').read_bytes()) == checkpoint['body_sha256']
    # Compare every pre-existing tracked file to the fixed start. Old reports,
    # addon/ACL/core and every old evidence byte remain outside this change.
    protected = git('ls-files', '-z', '--with-tree=' + BASE).split(b'\0')
    checked = []
    for encoded in protected:
        if not encoded:
            continue
        path = encoded.decode()
        if path.startswith(('docs/evidence/s10-p0-15/', 'scripts/s10_p0_15_', 'docs/s10-p0-15-')):
            continue
        expected = git('show', BASE + ':' + path)
        assert (ROOT / path).read_bytes() == expected, 'old tracked file changed: ' + path
        checked.append({'path': path, 'sha256': sha(expected)})
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent).decode().strip() == CORE
    assert not git('diff', '--name-only', cwd=ROOT.parent).strip()
    result = {'status': 'STATIC_CHECKS_PASS_PENDING_GPT', 'requested_ceiling':
        'S10_P0_15_GAP03_DELTA_AND_NEXT_ACTION_STATIC_TECH_ACCEPTED',
        'base': BASE, 'core': CORE, 'preflight': 6214014587, 'preflight_exact': True,
        '22_original_rows_all_fields_exact': True, 'FULL_PASS': 0,
        'original_status_counts': delta['status_counts'], 'source_AST_and_literal_guards': 'PASS',
        'old_tracked_files_verified': len(checked), 'old_tracked_manifest_sha256': sha(canonical(checked)),
        'budget_actual_and_limit': ZERO, 'current_business_runtime_proof': 'NOT_RUN',
        'source_eligibility_now': 'NOT_RUN', 'new_historical_PDF_bytes': 'NOT_RUN',
        'next_business_READY': False, 'next_minimal_prerequisite': '只读补user5展开grant/公司在职/票据安装态；另行授权，当前不执行',
        'S10_PRODUCTION_T12': 'BLOCKED', 'native_SIGSEGV_root_cause': 'UNKNOWN',
        'codex_static_review_only': True, 'GPT_review_or_P016_authorization': 'NOT_CLAIMED'}
    dump('verification.json', result)
    files.append(OUT / 'verification.json')
    index = {str(p.relative_to(ROOT)): {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in sorted(files)}
    dump('sha256-index.json', {'base': BASE, 'files': index, 'index_self_hash':
        '不递归自哈希；本文件SHA256由正式交付评论固定，包含所有其它新增文件，包括分析脚本。'})
    print(json.dumps({'checks': 'PASS', 'old_files': len(checked), 'indexed_files': len(index),
        'index_sha256': sha((OUT / 'sha256-index.json').read_bytes()), 'execution_budget': ZERO}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    assert args.generate != args.verify, 'select exactly one file-only operation'
    if args.generate:
        generate()
    else:
        verify()
