"""Strict, read-only LC2 log validation and failure lookup; never imports Odoo."""
import argparse
import json
from pathlib import Path

MAX_LINE = 16 * 1024
REQUIRED = {
    'schema_version': str, 'event_id': str, 'event': str, 'pid': int,
    'process_seq': int, 'ts_utc': str, 'monotonic_ns': int,
}
OPTIONAL_TYPES = {
    'run_id': str, 'task_id': str, 'case_id': str, 'attempt': int,
    'trace_id': str, 'request_id': str, 'operation_ref': str,
    'actor_id': int, 'effective_uid': int, 'su_flag': bool,
    'company_id': int, 'store_id': int, 'scope_revision': int,
    'error_code': str, 'error_class': str, 'exception_type': str,
    'root_event_id': str, 'commit_observation': str,
}


def strict_loads(raw, *, parse_float=float):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('DUPLICATE_KEY')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('NONFINITE_NUMBER')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=parse_float)


def validate_jsonl(paths, *, require_end=True):
    """Return usable records AND integrity defects, never pretend partial is valid."""
    records, defects, seen, sequences, runs = [], [], set(), {}, {}
    for candidate in paths:
        path = Path(candidate)
        offset = 0
        with path.open('rb') as stream:
            line_number = 0
            while True:
                raw = stream.readline(MAX_LINE + 1)
                if not raw:
                    break
                line_number += 1
                location = {'path': str(path), 'line': line_number, 'offset': offset}
                offset += len(raw)
                issue = None
                if len(raw) > MAX_LINE:
                    # Consume the remainder without allocating an unbounded line.
                    while raw and not raw.endswith(b'\n'):
                        raw = stream.readline(MAX_LINE + 1)
                        offset += len(raw)
                    issue = 'OVERSIZE_RECORD'
                elif not raw.endswith(b'\n'):
                    issue = 'TRUNCATED_LINE'
                else:
                    try:
                        row = strict_loads(raw.decode('utf-8', errors='strict'))
                        if not isinstance(row, dict):
                            raise ValueError('RECORD_NOT_OBJECT')
                        for key, expected in REQUIRED.items():
                            if key not in row or type(row[key]) is not expected:
                                raise ValueError('INVALID_REQUIRED_FIELD:' + key)
                        if row['schema_version'] != '1.0':
                            raise ValueError('UNSUPPORTED_SCHEMA')
                        for key, expected in OPTIONAL_TYPES.items():
                            if row.get(key) is not None and type(row[key]) is not expected:
                                raise ValueError('INVALID_FIELD_TYPE:' + key)
                        if row['event_id'] in seen:
                            raise ValueError('DUPLICATE_EVENT_ID')
                        process = (row.get('run_id'), row['pid'])
                        previous = sequences.get(process)
                        if previous is not None and row['process_seq'] != previous + 1:
                            raise ValueError('PROCESS_SEQUENCE_GAP_OR_REORDER')
                        sequences[process] = row['process_seq']
                        seen.add(row['event_id'])
                        run = runs.setdefault(row.get('run_id'), set())
                        run.add(row['event'])
                        records.append({'location': location, 'record': row})
                    except (ValueError, UnicodeError) as error:
                        # Parser messages can echo private payload; export only a stable class/code.
                        known = str(error) if type(error) is ValueError else ''
                        issue = known if known.startswith((
                            'DUPLICATE_', 'NONFINITE_', 'INVALID_', 'UNSUPPORTED_',
                            'PROCESS_', 'RECORD_')) else type(error).__name__
                if issue:
                    defects.append(location | {'code': issue})
    if require_end:
        for run_id, events in runs.items():
            if 'run.end' not in events:
                defects.append({'run_id': run_id, 'code': 'MISSING_RUN_END'})
    if not records:
        defects.append({'code': 'NO_VALID_RECORDS'})
    return {'status': 'INVALID' if defects else 'VALID', 'records': records,
            'defects': defects, 'record_count': len(records)}


def query_timeline(validation, **matches):
    return [item for item in validation['records'] if all(
        item['record'].get(key) == value for key, value in matches.items())]


def summarize_failure(validation, **matches):
    timeline = query_timeline(validation, **matches)
    errors = [item for item in timeline if item['record'].get('error_class')]
    primaries = [item for item in errors if not item['record'].get('root_event_id')]
    verified = [item for item in timeline if item['record'].get('commit_observation') == 'VERIFIED_COMMITTED']
    return {
        'integrity': validation['status'], 'defects': validation['defects'],
        'first_exception': primaries[0] if primaries else None,
        'secondary': [item for item in errors if item['record'].get('root_event_id')],
        'last_verified_checkpoint': verified[-1] if verified else None,
        'commit_observation': 'UNKNOWN' if not verified else 'VERIFIED_CHECKPOINT_ONLY',
        'missing_first_exception': not bool(primaries),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+')
    parser.add_argument('--run-id')
    parser.add_argument('--case-id')
    parser.add_argument('--allow-incomplete-run', action='store_true')
    args = parser.parse_args()
    result = validate_jsonl(args.paths, require_end=not args.allow_incomplete_run)
    matches = {key: value for key, value in {'run_id': args.run_id, 'case_id': args.case_id}.items() if value}
    print(json.dumps(summarize_failure(result, **matches), ensure_ascii=True))
    return int(result['status'] != 'VALID')


if __name__ == '__main__':
    raise SystemExit(main())
