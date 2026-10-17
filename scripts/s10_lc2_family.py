"""C-family HTTP fixture confined to two newly created synthetic identities.

Actors and callbacks are supplied by the single tester. No login, database,
browser or network is started at import. Native HTTP/ORM permission checks are
always exercised; the client scope is only an additional tool safety boundary.
"""
import asyncio
from html.parser import HTMLParser
import sys
import uuid

from s10_lc2_evidence import save_once
from s10_lc2_http import (
    FAMILY_CLINICAL_VALUES, FAMILY_PATIENT_VALUES, _FamilyWriteScope,
    _private_directory,
)
from s10_lc2_supervisor import save_primary


class _FamilyWorkbenchFacts(HTMLParser):
    """Inspect only fixed section headings and record container presence."""
    titles = frozenset({'今日未出账费用', '历史未出账费用', '待核对，禁止出账',
                        '已出账未付清', '已结清本店账单', '线下付款与退款'})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_section = False
        self.in_heading = False
        self.heading_parts = []
        self.title = ''
        self.seen = set()
        self.records = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'section':
            self.in_section, self.title = True, ''
        elif tag == 'h2' and self.in_section:
            self.in_heading, self.heading_parts = True, []
        elif self.title in self.titles and (tag == 'table' or self.title == '线下付款与退款' and tag == 'div'):
            self.records += 1

    def handle_data(self, data):
        if self.in_heading:
            self.heading_parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'h2' and self.in_heading:
            self.title = ''.join(self.heading_parts).strip()
            self.in_heading = False
            if self.title in self.titles:
                self.seen.add(self.title)
        elif tag == 'section':
            self.in_section, self.title = False, ''


def _empty_family_workbench(body):
    facts = _FamilyWorkbenchFacts()
    facts.feed(body.decode('utf-8', errors='strict'))
    if facts.seen != facts.titles or facts.records:
        raise AssertionError('CONTROLLED_FAMILY_WORKBENCH_NOT_OBSERVED_EMPTY')
    return {'checked_family_sections': len(facts.seen), 'rendered_family_record_containers': facts.records,
            'store_wide_dayclose_section_excluded_from_family_empty_assertion': True}


def _rpc(actor, model, method, args):
    response, envelope = actor.rpc(model, method, args, case='C-SCOPE')
    response.require_status(200)
    if type(envelope) is not dict or 'error' in envelope or 'result' not in envelope:
        raise RuntimeError('FAMILY_NATIVE_READ_RPC_FAILED')
    return envelope['result']


def _many2one(value):
    if type(value) is list and len(value) == 2 and type(value[0]) is int:
        return value[0]
    if type(value) is int:
        return value
    raise RuntimeError('FAMILY_MANY2ONE_IDENTITY_NOT_OBSERVED')


def _ids(actor, model):
    values = _rpc(actor, model, 'search', [[]])
    if type(values) is not list or len(values) > 1000 or any(type(item) is not int or item <= 0 for item in values):
        raise RuntimeError('FAMILY_BASELINE_IDENTITIES_UNBOUNDED_OR_INVALID')
    return values


def _action(actor, scope):
    client, operation, payload = scope.expected()
    if actor.client is not client:
        raise ValueError('FAMILY_SEQUENCE_ACTOR_MISMATCH')
    with client._family_request(scope, operation, payload):
        result = actor.action('patients', operation, payload, case='C-SCOPE', key=uuid.uuid4().hex)
    scope.accept(operation, result)
    return result


def run_family(reader_actor, manager_actor, grant_callback, restore_callback, *, directory,
               protected_patient_ids):
    """Run six exact patient actions and a limited family read matrix.

    grant_callback(levels) and restore_callback() are synchronous normal S01
    grants for the existing new C reader only. The caller independently verifies
    actual commits, old-state preservation and full baseline grant restoration.
    protected_patient_ids comes from the already collected complete main
    baseline; an ordinary user's visible search is not that complete baseline.
    Never call this again after an unknown action outcome to create a new pair.
    """
    directory = _private_directory(directory)
    summary = {'case_id': 'C-SCOPE', 'subcase': 'C-FAMILY',
               'evidence_layer': 'HTTP_RPC_SYNTHETIC_FIXTURE',
               'persistent_verification': 'INDEPENDENT_RO_REQUIRED',
               'financial_positive_scope': 'EMPTY_FAMILY_SCOPE',
               'nonempty_family_financial_positive': 'NOT_RUN',
               'economic_write_operation_dispatched': False,
               'economic_state_verified_unchanged': 'INDEPENDENT_RO_REQUIRED',
               'queue_or_business_upstream_called': False}
    primary_ref = None
    try:
        grant_callback({'patient': 'write', 'medical': 'write', 'settlement': 'none', 'export': 'none'})
        # Read existing IDs before allowing any create/merge. Names or clinical
        # values of pre-existing patients are never requested or retained.
        existing_patients = _ids(reader_actor, 'ydental.patient')
        existing_merges = _ids(reader_actor, 'ydental.patient.merge')
        scope = _FamilyWriteScope(reader_actor.client, manager_actor.client,
            reader_uid=reader_actor.uid, manager_uid=manager_actor.uid,
            existing_patients=existing_patients, existing_merges=existing_merges,
            protected_patient_ids=protected_patient_ids)
        for _ in range(5):
            _action(reader_actor, scope)
        _action(manager_actor, scope)
        alias, canonical = scope.patient_ids
        summary.update(patient_ids=list(scope.patient_ids), clinical_ids=list(scope.clinical_ids),
                       merge_request_id=scope.merge_id, exact_mutation_count=scope.step)

        detail = reader_actor.client.request('GET', '/ydental/patients/%s' % canonical, case_id='C-SCOPE')
        detail.require_status(200)
        if FAMILY_PATIENT_VALUES[1]['name'].encode() not in detail.body:
            raise AssertionError('FAMILY_CANONICAL_DETAIL_NOT_OBSERVED')
        history = reader_actor.client.request('GET', '/ydental/patients/%s/clinical?purpose=history_review' % canonical,
                                             case_id='C-SCOPE')
        history.require_status(200)
        markers = [value.encode() for values in FAMILY_CLINICAL_VALUES for value in values.values()]
        if not all(marker in history.body for marker in markers):
            raise AssertionError('FAMILY_MERGED_HISTORY_HTTP_CONTENT_MISSING')
        rows = _rpc(reader_actor, 'ydental.patient.clinical', 'read', [scope.clinical_ids, [
            'id', 'ydental_patient_id', 'ydental_origin_patient_id', 'ydental_allergies',
            'ydental_prior_history', 'ydental_medication', 'ydental_identity_snapshot']])
        if type(rows) is not list or {row.get('id') for row in rows} != set(scope.clinical_ids):
            raise AssertionError('FAMILY_NATIVE_CLINICAL_ROWS_NOT_EXACT')
        by_id = {row['id']: row for row in rows}
        for index, row_id in enumerate(scope.clinical_ids):
            row = by_id[row_id]
            snapshot = row.get('ydental_identity_snapshot')
            if (_many2one(row['ydental_patient_id']) != canonical
                    or _many2one(row['ydental_origin_patient_id']) != scope.patient_ids[index]
                    or type(snapshot) is not dict or snapshot.get('patient_id') != scope.patient_ids[index]
                    or snapshot.get('name') != FAMILY_PATIENT_VALUES[index]['name']
                    or any(row['ydental_' + name] != value for name, value in FAMILY_CLINICAL_VALUES[index].items())):
                raise AssertionError('FAMILY_ORIGIN_SNAPSHOT_OR_CANONICAL_RPC_MISMATCH')
        summary.update(canonical_detail_http=True, both_histories_http=True,
                       both_histories_native_rpc=True, original_patient_references_preserved=True,
                       original_identity_snapshots_preserved=True, alias_clinical_entry='NOT_RUN')

        denied = reader_actor.client.request('GET', '/ydental/settlement?patient_id=%s' % canonical, case_id='C-SCOPE')
        denied.require_status(403)
        response, envelope = reader_actor.rpc('ydental.settlement.payment', 'read', [[1], ['id', 'ydental_amount']], case='C-SCOPE')
        response.require_status(200)
        name = envelope.get('error', {}).get('data', {}).get('name') if type(envelope) is dict else None
        if name != 'odoo.exceptions.AccessError':
            raise AssertionError('MEDICAL_FAMILY_PERMISSION_AUTOMATICALLY_EXPOSED_EXISTING_FINANCE')
        summary['medical_permission_does_not_authorize_existing_financial_object'] = True
        summary['medical_only_family_workbench_denied'] = True

        # These new identities have no economic source. A genuine allowed read
        # may therefore establish only EMPTY_FAMILY_SCOPE, not a nonempty case.
        allowed = manager_actor.client.request('GET', '/ydental/settlement?patient_id=%s' % canonical, case_id='C-SCOPE')
        allowed.require_status(200)
        summary['controlled_empty_family_facts'] = _empty_family_workbench(allowed.body)
        domain = [['ydental_patient_id', 'in', [alias, canonical]]]
        for model in ('ydental.settlement.source', 'ydental.settlement.payment'):
            response, envelope = manager_actor.rpc(model, 'search_read', [domain, ['id']], case='C-SCOPE')
            response.require_status(200)
            name = envelope.get('error', {}).get('data', {}).get('name') if type(envelope) is dict else None
            if name != 'odoo.exceptions.AccessError':
                raise AssertionError('FAMILY_NATIVE_FINANCIAL_MODEL_ACL_GUARD_CHANGED')
        summary['authorized_empty_family_workbench_http'] = True
        summary['native_financial_model_rpc_guard_denied'] = True
        summary['financial_empty_scope_verification'] = 'CONTROLLED_WORKBENCH_AND_INDEPENDENT_RO_REQUIRED'
        save_once(directory / (uuid.uuid4().hex + '.family-observation.json'), summary)
        return summary
    except BaseException as primary:
        primary_ref = save_primary(directory, primary, stage='family.fixture')
        raise
    finally:
        original = sys.exc_info()[1]
        try:
            restore_callback()
        except BaseException as secondary:
            save_primary(directory, secondary, stage='family.permissions_restore.secondary',
                         root_event_id=primary_ref['event_id'] if primary_ref else None)
            if original is None:
                raise RuntimeError('FAMILY_PERMISSION_RESTORE_FAILED_INDEPENDENT_VERIFICATION_REQUIRED') from None


async def async_run_family(*args, **kwargs):
    """Await one serial synchronous fixture; no concurrent business writes."""
    return await asyncio.to_thread(run_family, *args, **kwargs)
