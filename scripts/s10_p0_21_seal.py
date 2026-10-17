"""Offline delivery indexes only: no Odoo import, database, HTTP or business action.

Run after the final independent snapshot. Historical rows and failed decisions
are retained. This does not turn a verifier success into a business PASS.
"""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/s10-p0-21'
PRIVATE = ROOT / '.local/s10-p0-21'
RUN = ROOT / '.local/ydental_s10_test_20261017050000_21b0cafe'


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    final = read(PRIVATE / 'final-RO-rows.json')
    tables = final['tables']
    chain = read(RUN / 'b-chain.json')
    multi = read(RUN / 'b-multi.json')
    native = [read(p) for p in sorted(OUT.glob('r*-result.json'))]
    events = [json.loads(line) for line in (OUT / 'transaction-events.jsonl').read_text().splitlines()]
    checkpoints = {p.name: read(p) for p in sorted(OUT.glob('*-committed-checkpoint.json'))}
    facts = []
    for result in native:
        log = RUN / ('r%s-%s.log' % (result['round'], result['action']))
        raw = log.read_bytes()
        assert digest(raw) == result['log_sha256']
        for line in raw.decode(errors='replace').splitlines():
            if not line.startswith('S10_'):
                continue
            label, _, payload = line.partition(' ')
            try:
                value = json.loads(payload)
            except json.JSONDecodeError:
                value = {'private_line_sha256': digest(line.encode()), 'unparsed': True}
            facts.append({'label': label, 'process': result['action'], 'native_exit_code': result['exit_code'],
                          'values': value, 'not_commit_proof_by_itself': True})
    save('native-scenario-output-index.json', facts)
    requests = []
    if (RUN / 'http.log').exists():
        for line in (RUN / 'http.log').read_text().splitlines():
            match = re.search(r'"(GET|POST|HEAD) ([^ ]+) HTTP/[^\"]+" (\d+)', line)
            if match:
                method, path, status = match.groups()
                requests.append({'method': method, 'path': path.split('?')[0], 'status': int(status)})
    save('native-HTTP-request-index.json', {'requests': requests, 'count': len(requests),
         'includes_redirect_GET_and_API_negatives': True, 'cap': 350})
    counts = {name: len(tables.get(name, [])) for name in (
        'res_users', 'ydental_access_store', 'ydental_patient', 'ydental_treatment_fee',
        'ydental_settlement_payment', 'ydental_settlement_refund', 'stock_move',
        'ydental_settlement_bill_original', 'ydental_access_audit')}
    save('actual-budget.json', {
        'maintenance_connections': sum(e['event'] == 'maintenance_intent' for e in events),
        'CREATE': sum(e['event'] == 'CREATE_returned' for e in events),
        'explicit_RO_RR_connections': sum(e['event'] == 'readonly_intent' for e in events),
        'explicit_RO_RR_cap': 32, 'native_processes': native,
        'native_cumulative_backend_creations': sum(r['native_cumulative'] for r in native),
        'native_observed_pool_max': max(r['observed_pool_max'] for r in native), 'pool_cap': 8,
        'old_business_connections': 0, 'A_replay': 0, 'targeted_fix_rounds': 2,
        'commit_returned_events': sum(e['event'] == 'commit_returned' for e in events),
        'durable_event_counts': dict(Counter(e['event'] for e in events)),
        'final_native_table_counts': counts, 'native_HTTP_requests': len(requests),
        'HTTP_and_browser': read(OUT / 'Web-result.json') if (OUT / 'Web-result.json').exists() else 'NOT_RUN',
        'per_PID_DSN': 'UNKNOWN where native creation log does not identify DSN; observed DSNs retained per process',
        'HTTP_backend_cumulative_not_in_control_results': True,
    })
    invoice = next(row for row in tables['account_move'] if row['id'] == chain['invoice_id'])
    payments = [row for row in tables['ydental_settlement_payment'] if row['id'] in
                (chain['payment_first_id'], chain['payment_second_id'])]
    originals = [row for row in tables['ydental_settlement_bill_original'] if row['invoice_id'] == invoice['id']]
    summary = {'database': final['database'], 'oid': final['oid'], 'cluster': final['cluster'],
               'chain': {key: chain[key] for key in ('patient_id', 'store_id', 'execution_id', 'document_id', 'invoice_id', 'fee_ids', 'drug_event_ids', 'drug_move_ids')},
               'invoice': {key: invoice[key] for key in ('id', 'company_id', 'partner_id', 'state', 'move_type', 'amount_total', 'amount_residual', 'currency_id', 'payment_state')},
               'payment_amounts': [row['ydental_amount'] for row in payments],
               'originals': [{key: row[key] for key in ('id', 'invoice_id', 'patient_id', 'store_id', 'company_id', 'actor_id', 'version', 'previous_id', 'attachment_id', 'pdf_sha256', 'source_sha256', 'template_sha256')} for row in originals],
               'checkpoints': checkpoints, 'all_tables_captured': len(tables),
               'multi_patient_id': multi['patient_id'], 'no_cross_patient_chain_stitching': True,
               'overall': 'S10_TECHNICAL_EXIT_BLOCKED', 'document_completion': 'NOT_RUN_AFTER_ACQUIRE_GATE_FAIL',
               'general_audit_integrity_scenario': 'STATIC_BLOCKED_NOT_RUN',
               'not_an_independent_GPT_ruling': True}
    assert Decimal(str(invoice['amount_total'])) == Decimal('740')
    assert Decimal(str(invoice['amount_residual'])) == 0
    assert invoice['state'] == 'posted' and invoice['move_type'] == 'out_invoice'
    assert sorted(Decimal(str(row['ydental_amount'])) for row in payments) == [Decimal('350'), Decimal('390')]
    assert sum(e['event'] == 'readonly_intent' for e in events) <= 32
    assert len(requests) <= 350
    save('final-facts-summary.json', summary)
    print(json.dumps({'offline_seal_exit': 0, 'overall': summary['overall'], 'native_processes': len(native),
                      'committed_checkpoints': len(checkpoints), 'native_HTTP_requests': len(requests)}))


if __name__ == '__main__':
    main()
