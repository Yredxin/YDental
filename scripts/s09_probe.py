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
    f.admin._grant(f.second.id, f.stores[0].id, {'export': 'write'})
    price(f, 80, catalog=f.catalogs[2])
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
    assert actual['state'] == 'confirmed' and actual['amount'] == 80
    assert f.root['ydental.treatment.line'].browse(issued['line_ids'][1]).state == 'issued'
    assert pdf.startswith(b'%PDF-') and len(pdf) > 1000
    result = {'result': 'PASS', 'medical_execution': medical.id, 'exam_execution': started['execution_id'],
              'order': issued['order_id'], 'line': action['line_id'], 'other_line': issued['line_ids'][1],
              'event': actual['event_id'], 'fee': actual['fee_id'], 'amount': actual['amount'],
              'result_id': draft['result_id'], 'version': confirmed['version'],
              'pdf_bytes': len(pdf), 'pdf_digest': digest, 'finished': finished['state']}
    cr.commit()
print(json.dumps(result, ensure_ascii=False))
