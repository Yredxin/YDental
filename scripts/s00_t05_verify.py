"""Read-only verification and evidence tables for the two real S00-T05 syncs."""
import json
import sys

from s00_t05_sync import (OUT, DEFINITIONS, FILTER, PROJECT_ID, Sync, canonical,
                          field, identities, save, single_value, utc)


def main():
    snapshots = [json.loads((OUT / ('project-' + n + '.json')).read_text())
                 for n in ('before', 'after', 'second-check')]
    before, after, second = [s['project'] for s in snapshots]
    maps = [identities(p) for p in (before, after, second)]
    first_run, second_run = [json.loads((OUT / ('sync-' + r + '.json')).read_text())
                             for r in ('first', 'second')]
    operations = json.loads((OUT / 'operation-log.json').read_text())
    mutations = [o for o in operations if o['kind'] == 'mutation']
    checks = []

    def check(name, condition):
        checks.append({'assertion': name, 'status': 'PASS' if condition else 'FAIL'})

    check('37 complete unique identities preserved', all(set(m) == set(range(1, 38)) for m in maps)
          and all(maps[0][n]['id'] == maps[1][n]['id'] == maps[2][n]['id'] for n in maps[0]))
    check('22 historical cards archived, both readbacks',
          all(m[n]['isArchived'] for m in maps[1:] for n in range(1, 23)))
    check('15 current-plan cards remain active',
          all(not m[n]['isArchived'] for m in maps for n in range(23, 38)))
    check('all Issue/PR content, states, PR flags and comment counts unchanged',
          all(maps[0][n]['content'] == m[n]['content'] for m in maps[1:] for n in maps[0]))
    check('native Status definition/options unchanged',
          all(field(before, 'Status') == field(p, 'Status') for p in (after, second)))
    check('native Status values unchanged on all 37 cards',
          all(single_value(maps[0][n], 'Status') == single_value(m[n], 'Status')
              for m in maps[1:] for n in maps[0]))
    check('7 workflow enabled/metadata values unchanged', before['workflows']['totalCount'] == 7
          and canonical(before['workflows']) == canonical(after['workflows']) == canonical(second['workflows']))
    check('all 19 existing field definitions unchanged',
          all(f in after['fields']['nodes'] and f in second['fields']['nodes'] for f in before['fields']['nodes']))
    check('only two new custom fields, unique names and exact unique options',
          after['fields']['totalCount'] == second['fields']['totalCount'] == before['fields']['totalCount'] + 2
          and all(field(p, name) for p in (after, second) for name in DEFINITIONS))
    for name in DEFINITIONS:
        check(name + ' values correct on all 15 current cards',
              all(single_value(m[n], name)['name'] ==
                  (('PLAN' if n == 23 else f'S{n - 24:02}') if name == '阶段' else
                   ('进行中' if n == 23 else ('待复核' if n == 24 else '待启用')))
                  for m in maps[1:] for n in range(23, 38)))
    check('5 existing views preserved with fields/filter/layout',
          all(canonical(v) in [canonical(w) for w in p['views']['nodes']]
              for p in (after, second) for v in before['views']['nodes']))
    views = [v for v in second['views']['nodes'] if v['name'] == '当前计划']
    check('one current-plan table view with exact filter', len(views) == 1
          and views[0]['filter'] == FILTER and views[0]['layout'] == 'TABLE_LAYOUT')
    check('canary archived alone with exact expected full readback',
          mutations[0]['action'] == 'archiveProjectV2Item' and mutations[0]['expected_state_match']
          and sum(i['isArchived'] for i in json.loads((OUT / 'check-001.json').read_text())['project']['items']['nodes']) == 1)
    check('each mutation has immediate full readback and exact expected-state match',
          all(o.get('expected_state_match') is True and (OUT / o['immediate_readback']).exists() for o in mutations))
    check('first live sync succeeded', first_run['status'] == 'PASS' and first_run['exit_code'] == 0)
    check('second identical sync succeeded with 0 mutations', second_run['status'] == 'PASS'
          and second_run['exit_code'] == 0 and second_run['mutation_count'] == 0
          and not any(o['kind'] == 'mutation' and o['round'] == 'second' for o in operations))
    check('first and second final full snapshots semantically identical', canonical(after) == canonical(second))
    check('all real synchronization API calls exited 0', all(o['exit_code'] == 0 for o in operations))
    runner = Sync('second')
    query = ('query($filter:String!) { node(id:"' + PROJECT_ID + '") { ... on ProjectV2 { '
             'items(first:100,archivedStates:[NOT_ARCHIVED],query:$filter) { totalCount '
             'pageInfo { hasNextPage endCursor } nodes { id content { ... on Issue { number } } } } } } }')
    data, entry = runner.api(query, {'filter': FILTER})
    entry['action'] = 'read-only server-side current-plan filter verification'
    save('operation-log.json', runner.log)
    filtered = data['node']['items']
    save('view-filter-readback.json', {'utc': utc(), 'query': query, 'variables': {'filter': FILTER},
                                    'exit_code': entry['exit_code'], 'data': filtered})
    check('server filter returns exactly #23-37, no historical cards', filtered['totalCount'] == 15
          and not filtered['pageInfo']['hasNextPage']
          and sorted(i['content']['number'] for i in filtered['nodes']) == list(range(23, 38)))
    save('field-definition.json', {'before': before['fields'], 'after': after['fields'], 'second': second['fields']})
    save('workflow-metadata-before-after.json', {
        'internal_trigger_filter_action_target': 'UNKNOWN; not exposed by API, not a precondition under decision 6107161042',
        'workflow_mutations': 0, 'before': before['workflows'], 'after': after['workflows'], 'second': second['workflows']})
    rows = ['# S00-T05 identity / three readbacks', '',
            '|Entity|Project item ID|Archived before→after→second|Stage after/second|Execution after/second|Entity state before→after→second|Native Status before→after→second|Comments before→after→second|',
            '|---|---|---|---|---|---|---|---|']
    for n in range(1, 38):
        values = [m[n] for m in maps]
        stage = single_value(values[2], '阶段')
        state = single_value(values[2], '执行状态')
        rows.append('|'+('PR' if n == 13 else 'Issue')+f' #{n}|`'+values[0]['id']+'`|'
                    +'→'.join(str(i['isArchived']).lower() for i in values)+'|'
                    +(stage['name'] if stage else '—')+'|'+(state['name'] if state else '—')+'|'
                    +'→'.join(i['content']['state'] for i in values)+'|'
                    +'→'.join(single_value(i, 'Status')['name'] for i in values)+'|'
                    +'→'.join(str(i['content']['comments']['totalCount']) for i in values)+'|')
    (OUT / 'identity-table.md').write_text('\n'.join(rows)+'\n')
    result = {'utc': utc(), 'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
              'assertion_count': len(checks), 'checks': checks, 'sync_first_mutations': first_run['mutation_count'],
              'sync_second_mutations': second_run['mutation_count'], 'automatic_repair': False}
    save('verification.json', result)
    print(result['status'], len(checks), 'assertions; first/second mutations:',
          first_run['mutation_count'], second_run['mutation_count'])
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
