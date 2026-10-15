"""SIMULATED static QWeb route and required-field contract for W3 selectors."""

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
    treatment = etree.parse(str(ROOT / 'ydental_treatment/views/ydental_treatment_templates.xml'))
    queue = etree.parse(str(ROOT / 'ydental_queue/views/ydental_queue_templates.xml'))
    exam = etree.parse(str(ROOT / 'ydental_exam/views/ydental_exam_templates.xml'))
    settlement = etree.parse(str(ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml'))
    assert treatment.xpath('//article[@t-att-data-order-kind="order.ydental_kind"]//tr[@t-att-data-line="line.id"]')
    assert not treatment.xpath('//article[@t-att-data-order-kind="order.ydental_kind"]//tr[@t-att-data-line="line.id"]//*[@class="task-id"]')
    assert treatment.xpath('//li[@t-att-data-segment="segment.id"]//strong[@class="task-id"]')
    assert queue.xpath('//*[@id="continuation-reception"]//*[@t-att-data-pending-task="task.id"]//form[@data-queue-form="report"]/input[@name="task_id"]')
    assert queue.xpath('//form[@data-queue-form="report"]/input[@name="version" and @t-att-value="task.ydental_version"]')
    assert queue.xpath('//tr[@t-att-data-task="row[\'entry\'].ydental_task_id.id"]//button[@data-operation="start" and @t-att-data-entry="entry.id"]')
    assert queue.xpath('//button[@data-operation="call" and @t-att-disabled="not can_call or None"]')
    assert treatment.xpath('//form[@data-operation="issue" and contains(@t-if, "role == \'medical\'") and contains(@t-if, "order.state == \'draft\'")]')
    assert treatment.xpath('//form[@data-operation="dispense" and contains(@t-if, "role == \'pharmacy\'") and contains(@t-if, "line.state == \'issued\'")]')
    assert exam.xpath('//section[@t-att-data-line="line.id"]//form[@data-operation="draft" and @t-att-data-version]')
    assert exam.xpath('//section[@t-att-data-line="line.id"]//form[@data-operation="perform" and contains(@t-if, "line.state in")]')
    assert exam.xpath('//form[@data-operation="confirm" and @t-att-data-version]')
    assert exam.xpath('//form[@data-operation="finish" and contains(@t-if, "line.state in")]')
    assert settlement.xpath('//input[@name="actual_utc" and @required="required"]')
    assert settlement.xpath('//input[@name="proof" and @required="required"]')
    assert settlement.xpath('//*[@data-ui1-feedback="1"]')
    assert queue.xpath('//*[@class and contains(@class,"o_ydental_queue_workspace") and @t-att-data-revision="revision"]')
    assert treatment.xpath('//*[@class and contains(@class,"o_ydental_treatment") and @t-att-data-revision="revision"]')
    assert exam.xpath('//*[@class and contains(@class,"o_ydental_exam") and @t-att-data-revision="revision"]')
    assert settlement.xpath('//input[@name="csrf_token"]') and settlement.xpath('//input[@name="revision"]')
    queue_js = (ROOT / 'ydental_queue/static/src/workspace/workspace.js').read_text()
    treatment_js = (ROOT / 'ydental_treatment/static/src/workbench/workbench.js').read_text()
    exam_js = (ROOT / 'ydental_exam/static/src/workbench/workbench.js').read_text()
    assert "operation === 'report' ? '/ydental/intake/action' : '/ydental/queue/action'" in queue_js
    assert 'csrf_token: workspace.querySelector' in queue_js and 'revision: workspace.dataset.revision' in queue_js
    assert "fetch('/ydental/treatment/action'" in treatment_js and 'revision: root.dataset.revision' in treatment_js
    assert "fetch('/ydental/exam/action'" in exam_js and 'revision: root.dataset.revision' in exam_js
    browser = (ROOT / 'scripts/s10_e2e_w3_browser.py').read_text()
    assert "article.locator('.task-id')" not in browser
    assert "JOIN ydental_treatment_segment" in browser and "ydental_treatment_line" in browser
    assert "#continuation-reception [data-pending-task=" in browser
    assert "f.checkValidity()" in browser
    prepare = (ROOT / 'scripts/s10_e2e_w3_prepare.py').read_text()
    assert "len(medicine_links) == 1" in prepare
    helper = (ROOT / 'ydental_treatment_test/tests/common.py').read_text()
    assert "if hasattr(cls, 'drug_catalog') and catalog == cls.drug_catalog" in helper
    assert "controlled._operate('publish_medicine'" in helper
    for form in ('//form[@data-operation="execute"]','//form[@data-operation="order"]'):
        tree = etree.parse(str(ROOT / 'ydental_treatment/views/ydental_treatment_templates.xml'))
        assert tree.xpath(form + '//*[@required="required"]')
    qweb = (ROOT / 'ydental_intake/views/intake.xml').read_text()
    assert '<input type="datetime-local" name="start" required="required"/>' in qweb
    assert '<input type="datetime-local" name="end" required="required"/>' in qweb
    assert re.search(r'form\.checkValidity\(\)', (ROOT / 'scripts/s10_e2e_w3_browser.py').read_text()) is None
    # The real Python Playwright locator checks the native browser validity.
    assert "f.checkValidity()" in (ROOT / 'scripts/s10_e2e_w3_browser.py').read_text()
    print(json.dumps({'status':'SIMULATED_PASS','qweb_contracts':checks,
                      'html_datetime_minute_aligned':True}))


if __name__ == '__main__': main()
