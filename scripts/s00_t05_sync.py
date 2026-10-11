"""S00-T05 minimal Project #4 sync under decision 6107161042.

Only archive allowlisted historical items, create two custom fields, set their
current-plan values, and create/filter a new view. Every single mutation is
followed by a complete read and exact semantic comparison before continuing.
No workflow, native Status, Issue/PR, item-add or delete mutation is available.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from s00_t05_project_snapshot import PAGE, PROJECT_ID, ROOT, SELECTIONS, VALUE_CONNECTION, utc

OUT = ROOT / 'docs/evidence/s00-t05-minimal'
STAGES = ['PLAN'] + [f'S{i:02}' for i in range(14)]
STATES = ['待启用', '进行中', '待复核', '待用户验收', '返工', '阻塞', '已验收']
DEFINITIONS = {'阶段': STAGES, '执行状态': STATES}
FILTER = 'repo:Yredxin/YDental is:issue 阶段:' + ','.join(STAGES)
SELECT = dict(SELECTIONS)
SELECT['items'] = SELECT['items'].replace(
    'url state', 'url state comments(last:1) { totalCount nodes { id createdAt } }')
SELECT['views'] += (' fields(first:100) { ' + PAGE
                    + ' nodes { ... on ProjectV2Field { id }'
                    + ' ... on ProjectV2SingleSelectField { id }'
                    + ' ... on ProjectV2IterationField { id } } }')
FIELD_SELECT = '__typename ... on ProjectV2SingleSelectField { id name dataType options { id name color description } }'
VIEW_SELECT = SELECT['views']


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def canonical(value):
    """Ignore only pagination bookkeeping and connection ordering."""
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in sorted(value.items())
                if k not in ('pageInfo', 'pages', 'complete')}
    if isinstance(value, list):
        return sorted((canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    return value


def identities(project):
    result = {}
    for item in project['items']['nodes']:
        content = item['content']
        if not content or content.get('repository', {}).get('nameWithOwner') != 'Yredxin/YDental':
            raise RuntimeError('Unexpected or inaccessible item identity')
        number = content['number']
        if number in result:
            raise RuntimeError('Duplicate item identity')
        expected_type = 'PullRequest' if number == 13 else 'Issue'
        if content['__typename'] != expected_type:
            raise RuntimeError('Issue/PR type mismatch')
        result[number] = item
    if set(result) != set(range(1, 38)):
        raise RuntimeError('Unexpected current or missing item')
    return result


def field(project, name):
    matches = [f for f in project['fields']['nodes'] if f['name'] == name]
    if len(matches) > 1:
        raise RuntimeError('Duplicate field name')
    if not matches:
        return None
    value = matches[0]
    if name in DEFINITIONS:
        if value['__typename'] != 'ProjectV2SingleSelectField':
            raise RuntimeError('Wrong custom field type')
        options = value['options']
        if sorted(o['name'] for o in options) != sorted(DEFINITIONS[name]):
            raise RuntimeError('Unexpected, missing or duplicate options')
        if len({o['id'] for o in options}) != len(options):
            raise RuntimeError('Duplicate option ID')
    return value


def single_value(item, name):
    values = [v for v in item['fieldValues']['nodes'] if v.get('field', {}).get('name') == name]
    if len(values) > 1:
        raise RuntimeError('Duplicate item field value')
    return values[0] if values else None


class Sync:
    def __init__(self, round_name):
        self.round = round_name
        self.log = json.loads((OUT / 'operation-log.json').read_text()) if round_name == 'second' else []
        self.project = None
        self.mutations = 0

    def api(self, query, variables=None, action=None):
        entry = {'sequence': len(self.log) + 1, 'round': self.round,
                 'kind': 'mutation' if action else 'query', 'action': action or 'full read / schema',
                 'query_sha256': hashlib.sha256(query.encode()).hexdigest(),
                 'variables': variables or {}, 'started_utc': utc()}
        self.log.append(entry)
        save('operation-log.json', self.log)  # write-ahead record; never retry uncertain writes
        try:
            response = subprocess.run(['gh', 'api', 'graphql', '--input', '-'],
                                      input=json.dumps({'query': query, 'variables': variables or {}}),
                                      text=True, capture_output=True, timeout=60)
            entry.update(exit_code=response.returncode, finished_utc=utc())
            if response.returncode:
                # Only API error messages, never raw CLI authentication output.
                try:
                    entry['api_errors'] = [e['message'] for e in json.loads(response.stdout).get('errors', [])]
                except (ValueError, KeyError):
                    entry['error'] = 'CLI failure; raw authentication output omitted'
                raise RuntimeError('GraphQL request failed; stop without retry')
            payload = json.loads(response.stdout)
            if payload.get('errors'):
                entry['api_errors'] = [e['message'] for e in payload['errors']]
                raise RuntimeError('GraphQL errors; stop without retry')
            entry['status'] = 'PASS'
            return payload['data'], entry
        finally:
            entry.setdefault('finished_utc', utc())
            entry.setdefault('status', 'FAIL')
            save('operation-log.json', self.log)

    def read(self, label):
        started = utc()
        parts = [name + '(first:100' + (',archivedStates:[ARCHIVED,NOT_ARCHIVED]' if name == 'items' else '')
                 + ') { ' + PAGE + ' nodes { ' + selection + ' } }'
                 for name, selection in SELECT.items()]
        query = ('query { viewer { login } node(id:"' + PROJECT_ID + '") { ... on ProjectV2 { '
                 'id title url closed viewerCanUpdate shortDescription readme ' + ' '.join(parts) + ' } } }')
        data, entry = self.api(query)
        project = data['node']
        if project['id'] != PROJECT_ID or not project['viewerCanUpdate'] or data['viewer']['login'] != 'Yredxin':
            raise RuntimeError('Project / authenticated identity / permission mismatch')
        for name, selection in SELECT.items():
            connection = project[name]
            cursor = connection['pageInfo']['endCursor']
            while connection['pageInfo']['hasNextPage']:
                query = ('query($cursor:String) { node(id:"' + PROJECT_ID + '") { ... on ProjectV2 { '
                         + name + '(first:100,after:$cursor'
                         + (',archivedStates:[ARCHIVED,NOT_ARCHIVED]' if name == 'items' else '')
                         + ') { ' + PAGE + ' nodes { ' + selection + ' } } } } }')
                more, _ = self.api(query, {'cursor': cursor})
                page = more['node'][name]
                if page['totalCount'] != connection['totalCount']:
                    raise RuntimeError('Connection changed during read')
                connection['nodes'].extend(page['nodes'])
                connection['pageInfo'] = page['pageInfo']
                if connection['pageInfo']['hasNextPage'] and connection['pageInfo']['endCursor'] == cursor:
                    raise RuntimeError('Pagination did not advance')
                cursor = connection['pageInfo']['endCursor']
            if len(connection['nodes']) != connection['totalCount']:
                raise RuntimeError('Incomplete connection')
            connection['complete'] = True
        for item in project['items']['nodes']:
            values = item['fieldValues']
            if values['pageInfo']['hasNextPage'] or len(values['nodes']) != values['totalCount']:
                raise RuntimeError('Item fields incomplete; stop before further mutation')
        for view in project['views']['nodes']:
            values = view['fields']
            if values['pageInfo']['hasNextPage'] or len(values['nodes']) != values['totalCount']:
                raise RuntimeError('View fields incomplete')
        identities(project)
        save(label + '.json', {'scope': 'S00-T05 decision 6107161042', 'snapshot': label,
                              'started_utc': started, 'finished_utc': utc(),
                              'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                              'viewer': data['viewer']['login'], 'read_exit_code': 0, 'project': project})
        entry['snapshot'] = label + '.json'
        save('operation-log.json', self.log)
        return project

    def change(self, operation, inputs, selection, transform):
        if self.round == 'second':
            raise RuntimeError('Second sync would mutate; idempotence failed, no write attempted')
        expected = copy.deepcopy(self.project)
        query = ('mutation($input:' + operation[0].upper() + operation[1:] + 'Input!) { '
                 + operation + '(input:$input) { ' + selection + ' } }')
        data, entry = self.api(query, {'input': inputs}, operation)
        self.mutations += 1
        # No next mutation until complete readback and exact expected-state check.
        actual = self.read(f'check-{self.mutations:03}')
        transform(expected, data[operation])
        entry['immediate_readback'] = f'check-{self.mutations:03}.json'
        entry['expected_state_match'] = canonical(expected) == canonical(actual)
        save('operation-log.json', self.log)
        if not entry['expected_state_match']:
            save('unexpected-state.json', {'expected': expected, 'actual': actual, 'operation': entry})
            raise RuntimeError('Unexpected change: stop without automatic repair')
        self.project = actual
        print(f'{self.round}: mutation {self.mutations} {operation}; immediate full readback PASS', flush=True)

    def sync(self):
        # Identical desired-state synchronization in both executions.
        for number in range(1, 23):
            item = identities(self.project)[number]
            if not item['isArchived']:
                item_id = item['id']
                self.change('archiveProjectV2Item', {'projectId': PROJECT_ID, 'itemId': item_id},
                            'clientMutationId',
                            lambda p, _: identities(p)[number].update(isArchived=True))
                # #1 is the canary, individually verified before #2 is attempted.
        for name, names in DEFINITIONS.items():
            if not field(self.project, name):
                options = [{'name': n, 'color': 'GRAY', 'description': ''} for n in names]

                def add_field(project, response):
                    created = response['projectV2Field']
                    project['fields']['nodes'].append(created)
                    project['fields']['totalCount'] += 1
                    field(project, name)

                self.change('createProjectV2Field', {'projectId': PROJECT_ID, 'name': name,
                            'dataType': 'SINGLE_SELECT', 'singleSelectOptions': options},
                            'projectV2Field { ' + FIELD_SELECT + ' }', add_field)
        for number in range(23, 38):
            desired = {'阶段': 'PLAN' if number == 23 else f'S{number - 24:02}',
                       '执行状态': '进行中' if number == 23 else ('待复核' if number == 24 else '待启用')}
            for name, value in desired.items():
                item = identities(self.project)[number]
                definition = field(self.project, name)
                option_id = next(o['id'] for o in definition['options'] if o['name'] == value)
                current = single_value(item, name)
                if current and current['optionId'] == option_id:
                    continue

                def update_value(project, _):
                    values = identities(project)[number]['fieldValues']
                    old = single_value(identities(project)[number], name)
                    if old:
                        values['nodes'].remove(old)
                    else:
                        values['totalCount'] += 1
                    values['nodes'].append({'__typename': 'ProjectV2ItemFieldSingleSelectValue',
                                            'name': value, 'optionId': option_id,
                                            'field': {'id': definition['id'], 'name': name}})

                self.change('updateProjectV2ItemFieldValue', {'projectId': PROJECT_ID, 'itemId': item['id'],
                            'fieldId': definition['id'], 'value': {'singleSelectOptionId': option_id}},
                            'clientMutationId', update_value)
        views = [v for v in self.project['views']['nodes'] if v['name'] == '当前计划']
        if len(views) > 1:
            raise RuntimeError('Duplicate current-plan views')
        if not views:
            visible = [field(self.project, n)['id'] for n in ('Title', '阶段', '执行状态')]

            def add_view(project, response):
                created = response['projectV2View']
                if created['name'] != '当前计划' or created['layout'] != 'TABLE_LAYOUT':
                    raise RuntimeError('Unexpected created view')
                if sorted(v['id'] for v in created['fields']['nodes']) != sorted(visible):
                    raise RuntimeError('Unexpected visible fields')
                project['views']['nodes'].append(created)
                project['views']['totalCount'] += 1

            self.change('createProjectV2View', {'projectId': PROJECT_ID, 'name': '当前计划',
                        'layout': 'TABLE_LAYOUT', 'configuration': {'visibleFieldIds': visible}},
                        'projectV2View { ' + VIEW_SELECT + ' }', add_view)
            views = [v for v in self.project['views']['nodes'] if v['name'] == '当前计划']
        if views[0]['filter'] != FILTER:
            view_id = views[0]['id']
            self.change('updateProjectV2View', {'viewId': view_id, 'filter': FILTER}, 'clientMutationId',
                        lambda p, _: next(v for v in p['views']['nodes'] if v['id'] == view_id).update(filter=FILTER))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', choices=['first', 'second'], required=True)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.round == 'first' and (OUT / 'project-before.json').exists():
        raise RuntimeError('Preserve first-run evidence; do not restart automatically')
    runner = Sync(args.round)
    start = utc()
    try:
        runner.project = runner.read('project-before' if args.round == 'first' else 'second-start')
        if args.round == 'first':
            for n, item in identities(runner.project).items():
                content = item['content']
                if n < 23 and n != 13 and content['state'] != 'CLOSED':
                    raise RuntimeError('Historical Issue no longer CLOSED')
                if n == 13 and (content['state'] != 'OPEN' or not content['isDraft'] or content['merged']
                                or content['autoMergeRequest'] is not None):
                    raise RuntimeError('Historical PR state changed from approved identity')
                if n >= 23 and (content['state'] != 'OPEN' or item['isArchived']):
                    raise RuntimeError('Current plan state changed')
        else:
            first = json.loads((OUT / 'project-after.json').read_text())['project']
            if canonical(first) != canonical(runner.project):
                raise RuntimeError('State changed between rounds; stop')
        runner.sync()
        final = runner.read('project-after' if args.round == 'first' else 'project-second-check')
        if canonical(final) != canonical(runner.project):
            raise RuntimeError('Final readback changed unexpectedly')
        save('sync-' + args.round + '.json', {'status': 'PASS', 'started_utc': start, 'finished_utc': utc(),
                                           'exit_code': 0, 'mutation_count': runner.mutations,
                                           'same_sync_logic': True, 'final_readback_match': True})
        print(f'{args.round} synchronization PASS; mutations={runner.mutations}', flush=True)
    except Exception as error:
        save('sync-' + args.round + '.json', {'status': 'FAIL', 'started_utc': start, 'finished_utc': utc(),
                                           'exit_code': 1, 'mutation_count': runner.mutations,
                                           'error': str(error), 'automatic_repair': False})
        print('STOP:', type(error).__name__, str(error), flush=True)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
