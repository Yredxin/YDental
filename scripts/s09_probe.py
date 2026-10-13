"""One committed synthetic S09 examination path in a guarded new database."""
import json
import os
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key, price, queue_bind, lease_args, handover_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual

run = Path(os.environ['YDENTAL_S09_RUN_DIR'])
assert run.name == env.cr.dbname and re.fullmatch(r'ydental_s09_test_[0-9]{14}_[0-9a-f]{8}', env.cr.dbname)
with env.registry.cursor() as cr:
    f = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(f)
    for user in (f.users['doctor'], f.second, f.users['reader'], f.users['none']):
        user.write({'lang': 'zh_CN'})
    f.admin._grant(f.second.id, f.stores[0].id, {'export': 'write'})
    f.admin._grant(f.users['reader'].id, f.stores[0].id, {'medical': 'read', 'exam': 'read'})
    price(f, 80, catalog=f.catalogs[2])
    f.doctor.env['ydental.exam.service']._operate('bind_template', {
        'catalog_id': f.catalogs[2].id, 'code': 'panorama-demo-1',
        'reason': 'Explicit synthetic clinic template review'}, key())
    f.doctor.env['ydental.exam.service']._operate('bind_template', {
        'catalog_id': f.catalogs[3].id, 'code': 'cbct-demo-1',
        'reason': 'Explicit synthetic clinic template review'}, key())
    with patch.object(type(f.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
        s, clinical, queue, lease, medical, doc, args = opened_actual(f)
    row = lambda n: {'mapping_id': f.mappings[0][n].id, 'quantity': 1, 'uom_id': f.uom.id,
                     'product_id': False, 'specification': '', 'usage': '', 'frequency': '', 'course': ''}
    order = s._operate('order', args | {'kind': 'exam', 'purpose': 'Synthetic independent panorama and CBCT',
                                      'lines': [row(2), row(3)]}, key())
    issued = s._operate('issue', args | {'order_id': order['order_id'], 'version': order['version']}, key())
    clinical._operate('handover', handover_args(doc, lease))
    task = f.root['ydental.intake.task'].browse(issued['task_ids'][0])
    f.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
    examiner = queue_bind(f, f.second)
    ex_lease = examiner._operate('enter', {'station_id': f.stations[0][2].id})
    called = examiner._operate('call', lease_args(ex_lease))
    assert called['task_id'] == task.id
    started = examiner._operate('start', lease_args(ex_lease) | {'entry_id': called['entry_id']})
    exam = examiner.env['ydental.exam.service']
    action = {'line_id': issued['line_ids'][0], 'execution_id': started['execution_id'],
              'lease_id': ex_lease['lease_id'], 'lease_token': ex_lease['token'], 'inline': False}
    draft = exam._operate('draft', action | {'version': 0, 'findings': '合成全景所见待人工阅片',
        'measurements': {}, 'conclusion': ''}, key())
    actual = exam._operate('perform', action | {'reason': '合成全景实际完成', 'materials': []}, key())
    confirmed = exam._operate('confirm', {'line_id': action['line_id'], 'version': draft['version'],
                                          'reason': '合成结果人工复核'}, key())
    pdf, digest = exam._pdf(action['line_id'], confirmed['version'])
    finished = exam._operate('finish', {k: action[k] for k in ('line_id', 'execution_id', 'lease_id', 'lease_token')} |
                            {'reason': '合成检查段完成'}, key())
    print('ACTUAL_DIAGNOSTIC', json.dumps(actual, ensure_ascii=False))
    assert actual['event_state'] == 'confirmed' and actual['state'] == 'confirmed'
    assert actual['result_document_state'] == 'pending' and actual['order_line_state'] == 'done'
    assert actual['fee_source_state'] == 'recorded' and actual['amount'] == 80
    event = f.root['ydental.treatment.event'].browse(actual['event_id'])
    fee = f.root['ydental.treatment.fee'].browse(actual['fee_id'])
    assert event.state == 'confirmed' and fee.ydental_amount == 80
    assert event.ydental_price_snapshot_id.ydental_price_id.ydental_catalog_id == f.catalogs[2]
    assert not actual['inventory_event_ids'] and not actual['move_ids']
    assert f.root['ydental.treatment.line'].browse(issued['line_ids'][1]).state == 'issued'
    assert pdf.startswith(b'%PDF-') and len(pdf) > 1000
    report_name = f'f1-report-{actual["event_id"]}.pdf'
    with (run / report_name).open('xb') as output:
        output.write(pdf)
    access = {'doctor': {'login': f.users['doctor'].login, 'password': 's05-test-password'},
              'examiner': {'login': f.second.login, 'password': 's06a-test-password'},
              'reader': {'login': f.users['reader'].login, 'password': 's05-test-password'},
              'none': {'login': f.users['none'].login, 'password': 's05-test-password'},
              'store_id': f.stores[0].id, 'language': 'zh_CN'}
    access_path = run / 'access.json'
    if not access_path.exists():
        with os.fdopen(os.open(access_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as output:
            json.dump(access, output)
    result = {'result': 'PASS', 'medical_execution': medical.id, 'exam_execution': started['execution_id'],
              'order': issued['order_id'], 'line': action['line_id'], 'other_line': issued['line_ids'][1],
              'event': actual['event_id'], 'event_state': actual['event_state'],
              'result_document_state_after_perform': actual['result_document_state'],
              'order_line_state': actual['order_line_state'],
              'fee_source_state': actual['fee_source_state'],
              'price_version': event.ydental_price_snapshot_id.ydental_price_id.id,
              'price_snapshot': event.ydental_price_snapshot_id.id,
              'fee': actual['fee_id'], 'amount': actual['amount'],
              'result_id': draft['result_id'], 'version': confirmed['version'],
              'pdf_bytes': len(pdf), 'pdf_digest': digest, 'pdf_file': report_name,
              'finished': finished['state']}
    cr.commit()
    with (run / f'f1-result-{actual["event_id"]}.json').open('x') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
