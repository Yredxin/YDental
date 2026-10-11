"""Read-only, paginated snapshot of Yredxin Project #4 for S00-T05.

Uses the existing authenticated gh CLI without reading/exporting credentials.
This tool has no mutation, workflow-disable, item-delete or database operation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/evidence/s00-t05'
PROJECT_ID = 'PVT_kwHOA3_tu84BmcLJ'
PAGE = 'totalCount pageInfo { hasNextPage endCursor }'
FIELD_VALUE = '''__typename
... on ProjectV2ItemFieldSingleSelectValue { name optionId field { ... on ProjectV2SingleSelectField { id name } } }
... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2Field { id name } } }
... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2Field { id name } } }
... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2Field { id name } } }
... on ProjectV2ItemFieldIterationValue { iterationId title field { ... on ProjectV2IterationField { id name } } }
... on ProjectV2ItemFieldRepositoryValue { repository { nameWithOwner } field { ... on ProjectV2Field { id name } } }
... on ProjectV2ItemFieldMilestoneValue { milestone { title } field { ... on ProjectV2Field { id name } } }
'''
VALUE_CONNECTION = PAGE + ' nodes { ' + FIELD_VALUE + ' }'
SELECTIONS = {
    'fields': '''__typename ... on ProjectV2Field { id name dataType }
        ... on ProjectV2SingleSelectField { id name dataType options { id name color description } }
        ... on ProjectV2IterationField { id name dataType configuration { duration startDay
          iterations { id title startDate duration } completedIterations { id title startDate duration } } }''',
    'items': '''id isArchived type content { __typename
        ... on Issue { id number title url state repository { nameWithOwner } }
        ... on PullRequest { id number title url state isDraft merged autoMergeRequest { enabledAt mergeMethod }
          repository { nameWithOwner } }
        ... on DraftIssue { id title } }
        fieldValues(first:100) { ''' + VALUE_CONNECTION + ' }',
    'views': 'id name number layout filter',
    'workflows': 'id name number enabled createdAt updatedAt',
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', choices=['before', 'after', 'second-check'], required=True)
    args = parser.parse_args()
    EVIDENCE.mkdir(exist_ok=True, parents=True)
    operations = []

    def query(text, variables=None):
        if not text.lstrip().startswith('query') or 'mutation' in text.lower():
            raise RuntimeError('Read-only query required')
        started = utc()
        result = subprocess.run(['gh', 'api', 'graphql', '--input', '-'],
                                input=json.dumps({'query': text, 'variables': variables or {}}),
                                text=True, capture_output=True, timeout=60)
        entry = {'operation': 'authenticated GraphQL query', 'query_sha256': hashlib.sha256(text.encode()).hexdigest(),
                 'started_utc': started, 'finished_utc': utc(), 'exit_code': result.returncode}
        operations.append(entry)
        # Do not publish raw CLI auth errors, headers, tokens or credentials.
        if result.returncode:
            entry['status'] = 'FAIL'
            raise RuntimeError('GraphQL query failed; no write attempted')
        payload = json.loads(result.stdout)
        if payload.get('errors'):
            entry['status'] = 'FAIL'
            raise RuntimeError('GraphQL returned errors; no write attempted')
        entry['status'] = 'PASS'
        return payload['data']

    def connection(fetch):
        cursor = None
        nodes = []
        pages = []
        expected = None
        while True:
            page = fetch(cursor)
            if expected is None:
                expected = page['totalCount']
            if page['totalCount'] != expected:
                raise RuntimeError('Connection changed during pagination')
            nodes.extend(page['nodes'])
            info = page['pageInfo']
            pages.append({'count': len(page['nodes']), 'pageInfo': info})
            if not info['hasNextPage']:
                break
            if not info['endCursor'] or info['endCursor'] == cursor:
                raise RuntimeError('Pagination cursor did not advance')
            cursor = info['endCursor']
        if len(nodes) != expected:
            raise RuntimeError('Incomplete connection snapshot')
        return {'totalCount': expected, 'nodes': nodes, 'pages': pages, 'complete': True}

    started = utc()
    try:
        data = query('query { viewer { login } user(login:"Yredxin") { projectV2(number:4) { '
                     'id title url closed viewerCanUpdate shortDescription readme } } }')
        project = data['user']['projectV2']
        if project['id'] != PROJECT_ID:
            raise RuntimeError('Project identity mismatch')
        for name, selection in SELECTIONS.items():
            gql = ('query($cursor:String) { node(id:"' + PROJECT_ID + '") { ... on ProjectV2 { '
                   + name + '(first:100,after:$cursor) { ' + PAGE + ' nodes { ' + selection + ' } } } } }')
            project[name] = connection(lambda cursor, q=gql, key=name: query(q, {'cursor': cursor})['node'][key])
        for item in project['items']['nodes']:
            first = item['fieldValues']
            if first['pageInfo']['hasNextPage']:
                gql = ('query($cursor:String) { node(id:"' + item['id'] + '") { ... on ProjectV2Item { '
                       'fieldValues(first:100,after:$cursor) { ' + VALUE_CONNECTION + ' } } } }')
                item['fieldValues'] = connection(lambda cursor, q=gql: query(q, {'cursor': cursor})['node']['fieldValues'])
            else:
                if len(first['nodes']) != first['totalCount']:
                    raise RuntimeError('Incomplete field values')
                first['complete'] = True
        output = {'scope': 'S00-T05 Project #4 read-only snapshot', 'snapshot': args.snapshot,
                  'started_utc': started, 'finished_utc': utc(), 'viewer': data['viewer']['login'],
                  'code_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                  'project': project, 'read_exit_code': 0, 'project_mutation_count': 0,
                  'synchronization': 'NOT_RUN: automation details must be verified before writes',
                  'operations': operations}
        (EVIDENCE / ('project-' + args.snapshot + '.json')).write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
        print('Read-only snapshot:', args.snapshot, '; items/fields/views/workflows:',
              '/'.join(str(project[k]['totalCount']) for k in ('items','fields','views','workflows')), '; exit 0')
        return 0
    finally:
        (EVIDENCE / ('read-operations-' + args.snapshot + '.json')).write_text(json.dumps(operations, indent=2) + '\n')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Snapshot stopped safely:', type(error).__name__)
        sys.exit(1)
