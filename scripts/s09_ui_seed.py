"""Committed synthetic UI fixture; leaves actual queue and exam actions for Firefox."""
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import patch

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key, price, handover_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual, receive

run = Path(os.environ['YDENTAL_S09_RUN_DIR'])
assert run.name == env.cr.dbname and re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname)
with env.registry.cursor() as cr:
    fixture = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(fixture)
    for user in (fixture.users['doctor'], fixture.users['frontdesk'], fixture.second,
                 fixture.users['reader'], fixture.users['none']):
        user.write({'lang': 'zh_CN'})
    fixture.admin._grant(fixture.users['manager'].id, fixture.stores[0].id, {'exam': 'write'})
    fixture.admin._grant(fixture.second.id, fixture.stores[0].id, {'export': 'write'})
    fixture.admin._grant(fixture.users['reader'].id, fixture.stores[0].id,
                         {'exam': 'read', 'medical': 'read'})
    reviewer = fixture.group.env['ydental.exam.service']
    for index, family, template in ((2, 'panorama', 'panorama-demo-1'),
                                     (3, 'cbct', 'cbct-demo-1')):
        catalog = fixture.catalogs[index]
        reviewer._operate('review_capability', {'capability_id': catalog.ydental_capability_id.id,
            'family': family, 'reason': 'Synthetic UI capability evidence'}, key())
        reviewer._operate('bind_template', {'catalog_id': catalog.id, 'code': template,
            'reason': 'Synthetic UI exact template binding'}, key())
    price(fixture, 80, catalog=fixture.catalogs[2])
    price(fixture, 120, catalog=fixture.catalogs[3])
    receive(fixture, quantity=6)
    with patch.object(type(fixture.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
        treatment, clinical, doctor_queue, doctor_lease, medical, document, args = opened_actual(fixture)
    row = lambda index: {'mapping_id': fixture.mappings[0][index].id, 'quantity': 1,
        'uom_id': fixture.uom.id, 'product_id': False, 'specification': '',
        'usage': '', 'frequency': '', 'course': ''}
    draft = treatment._operate('order', args | {'kind': 'exam',
        'purpose': 'Synthetic real Firefox panorama partial return and CBCT continuation',
        'lines': [row(2), row(3)]}, key())
    issued = treatment._operate('issue', args | {'order_id': draft['order_id'],
        'version': draft['version']}, key())
    today = fixture.group.env['ydental.supply.service']._date(fixture.stores[0])
    fixture.root['ydental.treatment.line'].browse(issued['line_ids'][1])._save({
        'ydental_exam_validated_date': today - timedelta(days=1)})
    returned = clinical._operate('handover', handover_args(document, doctor_lease))
    doctor_queue._exit(doctor_lease['lease_id'], doctor_lease['token'])
    identity = {
        'database': env.cr.dbname,
        'store_id': fixture.stores[0].id,
        'doctor': {'login': fixture.users['doctor'].login, 'password': 's05-test-password'},
        'frontdesk': {'login': fixture.users['frontdesk'].login, 'password': 's05-test-password'},
        'examiner': {'login': fixture.second.login, 'password': 's06a-test-password'},
        'reader': {'login': fixture.users['reader'].login, 'password': 's05-test-password'},
        'none': {'login': fixture.users['none'].login, 'password': 's05-test-password'},
        'medical_execution': medical.id, 'medical_lease': doctor_lease['lease_id'],
        'patient_id': medical.ydental_patient_id.id,
        'panorama_line': issued['line_ids'][0], 'cbct_line': issued['line_ids'][1],
        'panorama_task': issued['task_ids'][0], 'cbct_task': issued['task_ids'][1],
        'continuation_task': returned['continuation_task_id'],
        'panorama_station': fixture.stations[0][2].id, 'cbct_station': fixture.stations[0][3].id,
        'care_station': fixture.stations[0][0].id,
        'material_lot': fixture.lots['material'],
        'care_area': fixture.areas[0][0].id,
    }
    cr.commit()
    destination = run / ('ui-seed-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
    with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as output:
        json.dump(identity, output, ensure_ascii=False, indent=2)
print(json.dumps({key: value for key, value in identity.items() if key not in ('doctor', 'frontdesk', 'examiner')}, ensure_ascii=False))
