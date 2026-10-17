"""LC2 fresh-state admission. Importing this module never connects or loads Odoo."""
import argparse
import configparser
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from s10_lc2_evidence import ACCIDENT, Budget, CORE, collect_selection, runtime_gate, save_once
from s10_lc2_logging import strict_loads

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4'
REFERENCE = ROOT / '.local/s10-closeout-v1/r2-A-correct-committed-RO.json'
SIGNATURES = ROOT / 'docs/evidence/s10-closeout-v1/r2-A-correct-committed-RO-signatures.json'


def prepare_selection(directory):
    """Read last valid checkpoint once for schema/facts, never rerun/import its collector."""
    reference = strict_loads(REFERENCE.read_bytes(), parse_float=Decimal)

    signatures = strict_loads(SIGNATURES.read_bytes())
    selections = []
    for table in sorted(signatures['tables']):
        columns = {item['column'] for item in reference['schema'][table]}
        selections.append({'table': table, 'order': ['id'] if 'id' in columns else []})
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    save_once(directory / 'admission-selection.json', {
        'purpose': 'one independent admission inventory, never repeated per business action',
        'reference': str(REFERENCE.relative_to(ROOT)),
        'signatures': str(SIGNATURES.relative_to(ROOT)),
        'tables': selections, 'table_count': len(selections),
        'no_business_writes': True,
        'extra_metadata': ['public_physical_schema_columns', 'installed_ir_module_module', 'ir_access',
                           'only_queue_heartbeat_seconds_and_timeout_seconds'],
        'preserved_v4': {'document_id': 1, 'version': 4, 'write_uid': 7,
                         'confirm_version_id': 9, 'correct_version_id': 10},
    })
    return selections


def verify_metadata(directory, reference, unexplained):
    """Current security metadata uses the valid full initial checkpoint, not bad tail."""
    current_schema = strict_loads((directory / 'schema.json').read_bytes())
    schema_equal = current_schema == reference['schema']
    if not schema_equal:
        unexplained.append('CURRENT_SCHEMA_DIFFERS_FROM_VALID_CHECKPOINT')
    full_initial_path = ROOT / '.local/s10-closeout-v1/clone-initial-RO.json'
    full_initial = strict_loads(full_initial_path.read_bytes(), parse_float=Decimal)
    access_observed = strict_loads((directory / 'native-access.json').read_bytes())['observed_rows']
    access_rows = [strict_loads(row[0], parse_float=Decimal) for row in access_observed]
    expected_access = [{key: value for key, value in row.items() if not key.startswith('__physical_')}
                       for row in full_initial['tables']['ir_access']]
    if access_rows != expected_access:
        unexplained.append('NATIVE_ACCESS_DIFFERS_FROM_VALID_INITIAL_CHECKPOINT')
    modules_observed = strict_loads((directory / 'installed-modules.json').read_bytes())['observed_rows']
    module_rows = [strict_loads(row[0], parse_float=Decimal) for row in modules_observed]
    expected_modules = [{key: value for key, value in row.items() if not key.startswith('__physical_')}
                        for row in full_initial['tables']['ir_module_module'] if row['state'] == 'installed']
    if module_rows != expected_modules:
        unexplained.append('INSTALLED_MODULES_DIFFER_FROM_VALID_INITIAL_CHECKPOINT')
    settings = strict_loads((directory / 'queue-settings.json').read_bytes())['observed_rows']
    expected_settings = sorted([[row['key'], row['value']] for row in full_initial['tables']['ir_config_parameter']
                                if row['key'] in ('ydental_queue.heartbeat_seconds', 'ydental_queue.timeout_seconds')])
    if settings != expected_settings:
        unexplained.append('QUEUE_SETTINGS_DIFFER_FROM_VALID_INITIAL_CHECKPOINT')
    return schema_equal, full_initial_path


def rows_from_capture(directory, table):
    rows = []
    with (Path(directory) / (table + '.rows.jsonl')).open('rb') as stream:
        for raw in stream:
            wrapper = strict_loads(raw)
            rows.append(strict_loads(wrapper['server_json_text'], parse_float=Decimal) |
                        {'__physical_table__': wrapper['physical_table'], '__physical_oid__': wrapper['physical_oid']})
    return rows


def verify_admission(directory):
    """Compare with stored historical signatures only after new connection is closed."""
    directory = Path(directory)
    index = strict_loads((directory / 'sealed-index.json').read_bytes())
    signatures = strict_loads(SIGNATURES.read_bytes())['tables']
    observed = {item['path'].removesuffix('.rows.jsonl'): item for item in index['files']}
    changed = [table for table in sorted(signatures) if
               table not in observed or observed[table]['rows'] != signatures[table]['rows'] or
               observed[table]['legacy_canonical_sha256'] != signatures[table]['sha256']]
    # Release may have rolled back, committed, or left legitimate editor/audit changes.
    # Only these exact tables receive field-level inspection; never waive economics.
    editor_tables = {'ydental_clinical_document', 'ydental_access_audit', 'ydental_patient_mutex',
                     'ydental_supply_mutex', 'ydental_intake_mutex', 'ydental_queue_mutex'}
    unexplained = sorted(set(changed) - editor_tables)
    reference = strict_loads(REFERENCE.read_bytes(), parse_float=Decimal)
    schema_equal, full_initial_path = verify_metadata(directory, reference, unexplained)
    docs = rows_from_capture(directory, 'ydental_clinical_document')
    versions = rows_from_capture(directory, 'ydental_clinical_version')
    doc = next(row for row in docs if row['id'] == 1)
    if (doc['state'], doc['ydental_version'], doc['write_uid']) != ('confirmed', 4, 7):
        unexplained.append('DOCUMENT_VERSION_OR_ACTOR_DRIFT')
    expected_versions = [(9, 'confirm', 3, 7, 2), (10, 'correct', 4, 7, 9)]
    for ident, kind, number, author, previous in expected_versions:
        version = next((row for row in versions if row['id'] == ident), {})
        if tuple(version.get(key) for key in ['ydental_kind', 'ydental_number', 'ydental_author_id', 'ydental_previous_id']) != (kind, number, author, previous):
            unexplained.append('VERSION_ANCESTRY_DRIFT')
    allowed_document_fields = {'ydental_editor_id', 'ydental_session_id', 'ydental_session_revision',
                               'ydental_connection_hash', 'ydental_editor_hash', 'ydental_editor_expires',
                               'ydental_editor_lease_id', 'write_uid', 'write_date'}
    document_differences = []
    old_docs = {row['id']: row for row in reference['tables']['ydental_clinical_document']}
    if set(old_docs) != {row['id'] for row in docs}:
        unexplained.append('DOCUMENT_SET_DRIFT')
    for row in docs:
        old = old_docs.get(row['id'], {})
        fields = sorted(key for key in old.keys() | row.keys() if old.get(key) != row.get(key))
        document_differences.append({'id': row['id'], 'fields': fields})
        if fields and (row['id'] != 1 or set(fields) - allowed_document_fields):
            unexplained.append('DOCUMENT_CONTENT_DRIFT')
    # Audit and mutex variation is reported but not yet blessed; exact delta review is mandatory.
    pending_editor_delta_review = sorted(set(changed) & editor_tables)
    originals = rows_from_capture(directory, 'ydental_settlement_bill_original')
    original = next(row for row in originals if row['id'] == 1)
    if original['pdf_sha256'] != ORIGINAL_SHA:
        unexplained.append('OLD_ORIGINAL_SHA_METADATA_DRIFT')
    attachments = rows_from_capture(directory, 'ir_attachment')
    attachment = next(row for row in attachments if row['id'] == original['attachment_id'])
    original_bytes_verified = False
    if attachment.get('store_fname'):
        fname = attachment['store_fname']
        if not re.fullmatch(r'[0-9a-f]{2}/[0-9a-f]{40}', fname):
            unexplained.append('ORIGINAL_UNEXPECTED_FILESTORE_PATH')
        else:
            source_run = ROOT / '.local' / ACCIDENT
            source_marker = strict_loads((source_run / 'database.json').read_bytes())
            config_path = source_run / 'odoo.conf'
            if (config_path.is_symlink() or source_marker.get('database') != ACCIDENT
                    or source_marker.get('oid') != 2144127 or source_marker.get('core') != CORE
                    or source_marker.get('config_sha256') != hashlib.sha256(config_path.read_bytes()).hexdigest()):
                raise RuntimeError('SOURCE_CONFIG_OR_MARKER_DRIFT')
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(config_path)
            data_dir = Path(parser['options']['data_dir']).resolve()
            filestore = data_dir / 'filestore' / ACCIDENT
            original_path = filestore / fname
            if (original_path.is_symlink() or not original_path.is_file()
                    or not original_path.resolve().is_relative_to(filestore.resolve())):
                unexplained.append('ORIGINAL_FILESTORE_NOT_VERIFIABLE')
            else:
                digest = hashlib.sha256()
                with original_path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(65536), b''):
                        digest.update(chunk)
                original_bytes_verified = digest.hexdigest() == ORIGINAL_SHA
                if not original_bytes_verified:
                    unexplained.append('ORIGINAL_ACTUAL_BYTES_DRIFT')
    else:
        unexplained.append('ORIGINAL_FILESTORE_SOURCE_UNAVAILABLE')
    other_connections = strict_loads((directory / 'other-connections.json').read_bytes())['connections']
    if other_connections:
        unexplained.append('ACCIDENT_HAS_OTHER_CONNECTIONS')
    result = {'status': 'BLOCKED' if unexplained else ('EDITOR_DELTA_REVIEW_REQUIRED' if pending_editor_delta_review else 'ADMISSION_CANDIDATE'),
              'unexplained_tables_or_rules': unexplained, 'changed_tables': changed,
              'pending_editor_delta_review': pending_editor_delta_review,
              'document_differences': document_differences,
              'v4_and_ancestry_observed': 'DOCUMENT_VERSION_OR_ACTOR_DRIFT' not in unexplained and 'VERSION_ANCESTRY_DRIFT' not in unexplained,
              'current_editor_id': doc.get('ydental_editor_id'),
              'editor_expiry': doc.get('ydental_editor_expires'),
              'old_original_sha_metadata': original['pdf_sha256'],
              'actual_original_bytes_verified': original_bytes_verified,
              'other_connection_count': len(other_connections),
              'schema_equal_valid_checkpoint': schema_equal,
              'native_security_and_module_reference': str(full_initial_path.relative_to(ROOT)),
              'native_security_model': 'ir.access (fixed core20, no ir.rule/ir.model.access tables)',
              'copy_admission': not unexplained and not pending_editor_delta_review and original_bytes_verified}
    save_once(directory / 'admission-decision.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'capture', 'verify'])
    parser.add_argument('--directory', required=True)
    parser.add_argument('--approval')
    parser.add_argument('--product-commit')
    parser.add_argument('--test-commit')
    parser.add_argument('--budget-directory')
    args = parser.parse_args()
    directory = Path(args.directory).resolve()
    if args.mode == 'prepare':
        selections = prepare_selection(directory)
        print(json.dumps({'prepared_tables': len(selections), 'database_connections': 0}))
    elif args.mode == 'verify':
        print(json.dumps(verify_admission(directory), ensure_ascii=True))
    else:
        runtime_gate(args.approval, product_commit=args.product_commit, test_commit=args.test_commit)
        selections = strict_loads((directory / 'admission-selection.json').read_bytes())['tables']
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT.parent / 'odoo.conf')
        options = config['options']
        connection_args = {'host': options['db_host'], 'port': options['db_port'],
                           'user': options['db_user'], 'password': options['db_password'],
                           'application_name': 'ydental_s10_lc2_admission'}
        import psycopg2
        index = collect_selection(psycopg2.connect, connection_args, database=ACCIDENT,
                                  expected_oid=2144127, selections=selections,
                                  directory=directory / 'capture', budget=Budget(args.budget_directory))
        print(json.dumps({'captured_tables': len(index), 'closed_before_validation': True}))


if __name__ == '__main__':
    main()
