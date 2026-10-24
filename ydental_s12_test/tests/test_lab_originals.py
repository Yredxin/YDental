"""MODEL regression for the label semantic/encoder snapshot boundary.

Authorization and the order are explicit local seams here. Normal-role source
authorization and actual PDF generation are verified by the persistent HTTP loop.
"""
import base64
import copy
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.ydental_print.models.ydental_print_service import normalized, digest


@tagged('post_install', '-at_install')
class TestLaboratoryOriginalEncoding(TransactionCase):
    def order(self):
        return SimpleNamespace(id=47, ydental_version=2, state='draft',
            _fields={'state': SimpleNamespace(_description_selection=lambda env: [('draft', 'Synthetic draft')])},
            ydental_store_id=SimpleNamespace(name='Synthetic store'),
            ydental_internal_code='S12-SYNTHETIC-LABEL-47', ydental_package_code=False,
            ydental_rework_no=0, ydental_parent_order_id=SimpleNamespace(id=False),
            ydental_teeth=[16], ydental_material='Synthetic material', ydental_shade=False,
            ydental_quantity=1, ydental_responsible_id=SimpleNamespace(name='Synthetic responsible person'),
            ydental_planned_at='2026-10-24 00:00:00',
            ydental_patient_id=SimpleNamespace(id=48, ydental_number='SYNTHETIC-P48'),
            ydental_instructions='Synthetic source-only instructions',
            ydental_source_event_id=SimpleNamespace(id=49))

    def test_source_digest_never_depends_on_volatile_png_and_tracks_actual_code(self):
        printing = self.env['ydental.print.service']
        order = self.order()
        with (
            patch.object(type(printing), '_original_authorize', return_value=(printing, order, False, 'medical')),
            patch.object(type(self.env['ydental.patient.service']), '_patient', return_value=order.ydental_patient_id),
            patch.object(type(self.env['ir.actions.report']), 'barcode', side_effect=AssertionError('Encoder must not enter source facts')),
        ):
            first = printing._original_source('lab_label', order.id, 2)
            second = printing._original_source('lab_label', order.id, 2)
            self.assertEqual(first[3], second[3])
            self.assertEqual(first[4], second[4])
            self.assertEqual(first[3]['barcode'], {'format': 'QR', 'value': order.ydental_internal_code, 'width': 180, 'height': 180})
            self.assertEqual(first[4], digest(normalized(first[3])))
            order.ydental_internal_code = 'S12-CHANGED-SYNTHETIC-CODE'
            changed = printing._original_source('lab_label', order.id, 2)
            self.assertNotEqual(changed[4], first[4])

    def test_typed_render_freezes_actual_png_without_mutating_reviewed_source(self):
        printing = self.env['ydental.print.service']
        order = self.order()
        with (
            patch.object(type(printing), '_original_authorize', return_value=(printing, order, False, 'medical')),
            patch.object(type(self.env['ydental.patient.service']), '_patient', return_value=order.ydental_patient_id),
        ):
            _service, _order, _category, payload, signature = printing._original_source('lab_label', order.id, 2)
        original = copy.deepcopy(payload)
        # Deliberately different encoder byte results for the same semantics.
        # This seam is not a claim that these fixture bytes are real PNG files.
        outputs = (b'controlled-encoder-result-one', b'controlled-encoder-result-two')
        with (
            patch.object(type(self.env['ydental.access.service']), '_scope', return_value=SimpleNamespace(id=51, ydental_revision=3)),
            patch.object(type(self.env['ir.actions.report']), 'barcode', side_effect=outputs) as encoder,
        ):
            scopes = [printing._original_scope(payload, signature, None) for _index in range(2)]
        self.assertEqual(encoder.call_count, 2)
        for scope, raw in zip(scopes, outputs):
            facts = json.loads(scope.payload)
            self.assertTrue(scope.original)
            self.assertEqual(scope.content_digest, digest(scope.payload))
            self.assertEqual(facts['source_digest'], signature)
            self.assertEqual(base64.b64decode(facts['barcode']['png']), raw)
            self.assertEqual(facts['barcode']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(json.loads(scopes[0].payload)['barcode']['sha256'], json.loads(scopes[1].payload)['barcode']['sha256'])
        self.assertEqual(payload, original)
        self.assertEqual(digest(normalized(payload)), signature)
        self.assertNotIn('png', payload['barcode'])
        self.assertNotIn('sha256', payload['barcode'])
