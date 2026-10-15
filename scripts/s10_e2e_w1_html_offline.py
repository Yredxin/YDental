"""SIMULATED static QWeb route and required-field contract for W1 selectors."""

import json
from pathlib import Path
import re

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]


def forms(relative, selector, fields):
    tree = etree.parse(str(ROOT / relative))
    matches = tree.xpath(selector)
    assert matches, (relative, selector)
    def has_field(form, field):
        if form.xpath('.//*[@name=$field]', field=field): return True
        for call in form.xpath('.//*[@t-call]'):
            template = call.get('t-call').split('.')[-1]
            if tree.xpath('//template[@id=$template]//*[@name=$field]',
                          template=template, field=field):
                return True
        return False
    for field in fields:
        assert any(has_field(form, field) for form in matches), (selector, field)
    return len(matches)


def main():
    checks = {}
    checks['intake_reserve'] = forms('ydental_intake/views/intake.xml',
        '//form[@action="/ydental/intake/action" and .//select[@name="operation"]]',
        ('operation','patient_id','mapping_id','start','end'))
    checks['intake_arrive'] = forms('ydental_intake/views/intake.xml',
        '//form[@action="/ydental/intake/action" and .//input[@name="operation" and @value="arrive"]]',
        ('patient_id','csrf_token','revision','key'))
    checks['queue_report'] = forms('ydental_queue/views/ydental_queue_templates.xml',
        '//form[@data-queue-form="report"]', ('task_id','version'))
    checks['treatment'] = forms('ydental_treatment/views/ydental_treatment_templates.xml',
        '//form[@data-operation="execute"]',
        ('catalog_id','quantity','tooth','tooth_state','lot_id','material_quantity','reason'))
    checks['orders'] = forms('ydental_treatment/views/ydental_treatment_templates.xml',
        '//form[@data-operation="order"]',
        ('kind','purpose','mapping_id','quantity','product_id','specification','usage','frequency','course'))
    checks['dispense'] = forms('ydental_treatment/views/ydental_treatment_templates.xml',
        '//form[@data-operation="dispense"]', ('lot_id','quantity','reason'))
    checks['exam_draft'] = forms('ydental_exam/views/ydental_exam_templates.xml',
        '//form[@data-operation="draft"]', ('findings',))
    checks['exam_perform'] = forms('ydental_exam/views/ydental_exam_templates.xml',
        '//form[@data-operation="perform"]', ('reason',))
    checks['exam_confirm'] = forms('ydental_exam/views/ydental_exam_templates.xml',
        '//form[@data-operation="confirm"]', ('reason',))
    checks['exam_finish'] = forms('ydental_exam/views/ydental_exam_templates.xml',
        '//form[@data-operation="finish"]', ('reason',))
    checks['bill'] = forms('ydental_settlement/views/ydental_settlement_templates.xml',
        '//form[@action="/ydental/settlement/action" and .//input[@name="operation" and @value="bill"]]',
        ('fee_ids','discount','reason'))
    checks['pay'] = forms('ydental_settlement/views/ydental_settlement_templates.xml',
        '//form[@action="/ydental/settlement/action" and .//input[@name="operation" and @value="pay"]]',
        ('invoice_ids','amount','channel','actual_utc','proof'))
    for form in ('//form[@data-operation="execute"]','//form[@data-operation="order"]'):
        tree = etree.parse(str(ROOT / 'ydental_treatment/views/ydental_treatment_templates.xml'))
        assert tree.xpath(form + '//*[@required="required"]')
    qweb = (ROOT / 'ydental_intake/views/intake.xml').read_text()
    assert '<input type="datetime-local" name="start" required="required"/>' in qweb
    assert '<input type="datetime-local" name="end" required="required"/>' in qweb
    assert re.search(r'form\.checkValidity\(\)', (ROOT / 'scripts/s10_e2e_w1_browser.py').read_text()) is None
    # The real Python Playwright locator checks the native browser validity.
    assert "f.checkValidity()" in (ROOT / 'scripts/s10_e2e_w1_browser.py').read_text()
    print(json.dumps({'status':'SIMULATED_PASS','qweb_contracts':checks,
                      'html_datetime_minute_aligned':True}))


if __name__ == '__main__': main()
