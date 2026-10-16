"""One sealed W5 connection only, after exact REST checkpoint; no business API."""
from datetime import datetime, timezone
from decimal import Decimal
import json
import sys
import time
import xml.etree.ElementTree as ET

import s10_p0_16_contract as c


def require(condition, code, checks):
    checks[code] = bool(condition)
    if not condition:
        raise AssertionError(code)


def one(rows):
    assert len(rows) == 1, 'EXPECTED_ONE_SOURCE_ROW'
    return rows[0]


def group_closure(direct, edges):
    result = set(direct)
    while True:
        next_ids = result | {r['hid'] for r in edges if r['gid'] in result}
        if next_ids == result:
            return result
        result = next_ids


def check_grants(rows, membership, checks):
    levels = {}
    for row in rows:
        require(row['ydental_membership_id'] == membership, 'grant_bound_membership', checks)
        require(row['ydental_category'] not in levels, 'grant_category_unique', checks)
        levels[row['ydental_category']] = row['ydental_level']
    rank = c.rank_contract()
    require(all(v in rank for v in levels.values()), 'grant_levels_native_RANK', checks)
    require(rank[levels.get('settlement','none')] >= rank['read'], 'settlement_read', checks)
    require(levels.get('export','none') == 'write', 'export_write', checks)
    return levels


def execute():
    conn = None
    started = time.monotonic()
    result = {'authorization':c.AUTH,'base':c.BASE,'status':'BLOCKED_PREFLIGHT',
        'database':c.NAME,'actual_connections':0,'statement_count':0,'checks':{},
        'started_at':datetime.now(timezone.utc).isoformat(),'rolled_back':False,'closed':False,
        'zero_budget':c.ZERO,'post_business_source_second_connection':'NOT_RUN/NOT_AUTHORIZED',
        'new_PDF_bytes':'NOT_RUN','new_session_binding':'NOT_RUN','runtime_renderer':'NOT_RUN'}
    checks, projections, signatures, trace = result['checks'], {}, {}, []
    try:
        c.repo_gate()
        freeze = c.read(c.OUT / 'execution-freeze.json')
        contract = c.read(c.OUT / 'sql-contract.json')
        require(contract == c.plan(), 'frozen_SQL_plan_exact', checks)
        for path, digest in freeze['script_sha256'].items():
            require(c.sha((c.ROOT / path).read_bytes()) == digest, 'frozen_script:' + path, checks)
        require(c.sha((c.OUT / 'sql-contract.json').read_bytes()) == freeze['sql_contract_sha256'], 'frozen_SQL_SHA', checks)
        receipt = c.read(c.PRIVATE / 'preflight-api-readback.json')
        raw = c.read(c.PRIVATE / 'preflight-api-raw.json')
        body = (c.PRIVATE / 'preflight-body.txt').read_text()
        require(raw['body'] == body and c.sha(body.encode()) == receipt['body_sha256']
            and receipt['verbatim_equal'] and raw['id'] == receipt['comment_id'], 'REST_checkpoint_verbatim', checks)
        require(receipt['execution_freeze_sha256'] == c.sha((c.OUT / 'execution-freeze.json').read_bytes()), 'checkpoint_binds_frozen_scripts_SQL_budget', checks)
        require(c.read(c.PRIVATE / 'execution-ready.json')['remote_sha'] == c.BASE, 'current_API_ref_before_connection', checks)
        seal, sha1s = c.files_gate()
        result['seal'] = seal
        expected = c.read(c.ROOT / c.BASELINE)['all_table_signatures']
        require(len(expected) == 643, '643_fixed_baseline', checks)
        import psycopg2
        from psycopg2.extras import RealDictCursor
        c.save(c.PRIVATE / 'connection-intent.json', {'attempt':1,'database':c.NAME,
            'preflight_comment':receipt['comment_id'],'utc':datetime.now(timezone.utc).isoformat(),
            'readonly':True,'isolation':'REPEATABLE READ'})
        result['connect_attempts'] = 1
        conn = psycopg2.connect(dbname=c.NAME,connect_timeout=5,application_name='s10-p0-16-readonly',
            options=c.OPTIONS,**c.credentials())
        result['actual_connections'] = 1
        conn.set_session(readonly=True,isolation_level='REPEATABLE READ',autocommit=False)
        require(conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE, 'initial_IDLE', checks)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for entry in contract['queries']:
                require(time.monotonic() - started < 150, 'bounded_wall_time', checks)
                label = entry['label']
                result['last_statement'] = label
                cur.execute(entry['sql'],tuple(entry['params']))
                result['statement_count'] += 1
                rows = [dict(row) for row in cur.fetchall()]
                trace.append({'number':result['statement_count'],'label':label,'sql_sha256':c.sha(entry['sql'].encode()),
                    'params':entry['params'],'rows':len(rows)})
                if label == 'read_only':
                    require(one(rows)['transaction_read_only'] == 'on','first_SHOW_read_only_on',checks)
                elif label == 'isolation':
                    require(one(rows)['transaction_isolation'] == 'repeatable read','second_SHOW_repeatable_read',checks)
                elif label == 'identity':
                    row = one(rows)
                    require((row['database'],row['oid'],row['cluster']) == (c.NAME,c.OID,c.CLUSTER),'live_source_identity',checks)
                    result['identity'] = row
                elif label == 'other_connections':
                    require(not rows,'no_other_W5_connections',checks)
                elif label == 'catalog':
                    columns, types = {}, {}
                    for row in rows:
                        columns.setdefault(row['relname'],[]).append(row['attname'])
                        types.setdefault(row['relname'],{})[row['attname']] = row['data_type']
                    require(columns == contract['schema'],'live643_table_column_catalog_exact',checks)
                    result['catalog_sha256'] = c.sha(json.dumps(columns,sort_keys=True).encode())
                    c.save(c.PRIVATE / 'catalog-types.json',types)
                elif label.startswith('hash:'):
                    table = label[5:]
                    signatures[table] = one(rows)
                    require(signatures[table] == expected[table],'table:' + table,checks)
                    if len(signatures) == 643:
                        protected = c.read(c.ROOT/'docs/evidence/s10-p0-10/read-only-sql.json')['sources']['W5']['table_signatures']
                        stable = c.read(c.ROOT/'docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json')['target']['stable_31_sha256']
                        require(len(protected)==47 and all(signatures[t]==v for t,v in protected.items()),'protected47_exact',checks)
                        require(len(stable)==31 and all(signatures[t]==v for t,v in stable.items()),'stable31_exact',checks)
                else:
                    # Only frozen minimal metadata/account fields are fetched.
                    projections[label] = rows
                    if label == 'user':
                        require(one(rows)['id']==5 and one(rows)['active'] and not one(rows)['share'] and one(rows)['company_id']==1,'user5_active_internal_candidate_company1',checks)
                    elif label == 'companies':
                        require(1 in [r['cid'] for r in rows] and all(r['user_id']==5 for r in rows),'user5_allowed_company1',checks)
                    elif label == 'store':
                        store = one(rows)
                        require(store['id']==1 and store['active'] and store['company_active'] and store['company_id']==1,'store1_active_company1',checks)
                    elif label == 'memberships':
                        member = one(rows)
                        require(member['active'] and member['ydental_user_id']==member['employee_user_id']==member['resource_user_id']==5
                            and member['ydental_store_id']==1 and member['employee_active'] and member['resource_active']
                            and member['employee_company_id']==member['resource_company_id']==1
                            and member['ydental_employee_id']==member['employee_id'],'user5_unique_active_employment_store1',checks)
                    elif label == 'grants':
                        result['actual_levels'] = check_grants(rows,member['id'],checks)
                    elif label == 'implied_groups':
                        groups = group_closure([r['gid'] for r in projections['user_groups']],rows)
                        xmlgroups = {r['module']+'.'+r['name']:r['res_id'] for r in projections['group_xmlids']}
                        require(set(xmlgroups)=={'base.group_user','ydental_base.ydental_base_group_user'}
                            and set(xmlgroups.values())<=groups,'user5_actual_internal_and_YDental_groups_transitive',checks)
                        result['effective_required_groups'] = xmlgroups
                    elif label == 'invoice':
                        inv = one(rows)
                        require(inv['id']==1 and inv['state']=='posted' and inv['payment_state']=='paid'
                            and inv['move_type']=='out_invoice' and inv['company_id']==1 and inv['currency_id']==store['currency_id']
                            and Decimal(str(inv['amount_total']))==740 and Decimal(str(inv['amount_residual']))==0,'invoice1_posted_paid740_residual0',checks)
                    elif label == 'sources':
                        wanted = [(1,4,20),(2,3,40),(3,2,80),(4,1,600)]
                        require([(r['id'],r['ydental_fee_id'],Decimal(str(r['ydental_original_amount']))) for r in rows]==wanted
                            and all(r['ydental_store_id']==r['ydental_patient_id']==r['ydental_invoice_id']==1
                                and r['ydental_currency_id']==inv['currency_id'] and Decimal(str(r['ydental_discount']))==0 for r in rows),
                            'original_four_source_fee_links_20_40_80_600',checks)
                    elif label == 'fees':
                        require([Decimal(str(r['ydental_amount'])) for r in rows]==[600,80,40,20]
                            and [Decimal(str(r['ydental_quantity'])) for r in rows]==[1,1,4,2]
                            and all(r['ydental_store_id']==r['ydental_patient_id']==1 and r['id']==r['ydental_event_id']==r['ydental_price_snapshot_id']
                                and not r['ydental_parent_id'] and not r['ydental_price_review_id'] for r in rows),'original_four_fees_frozen_quantity_price_snapshot',checks)
                    elif label == 'snapshots':
                        require([r['ydental_price_id'] for r in rows]==[1,2,3,3]
                            and [Decimal(str(r['ydental_unit_price'])) for r in rows]==[600,80,10,10]
                            and all(r['ydental_store_id']==1 and r['ydental_currency_id']==inv['currency_id'] for r in rows),'S05_original_price_snapshots',checks)
                    elif label == 'invoice_lines':
                        lines = {r['id']:r for r in rows}
                        fees = {r['id']:r for r in projections['fees']}
                        require(all(s['ydental_line_id'] in lines and lines[s['ydental_line_id']]['move_id']==1
                            and Decimal(str(lines[s['ydental_line_id']]['price_subtotal']))==Decimal(str(s['ydental_original_amount']))
                            and Decimal(str(lines[s['ydental_line_id']]['price_unit']))==Decimal(str(fees[s['ydental_fee_id']]['ydental_unit_price']))
                            and Decimal(str(lines[s['ydental_line_id']]['quantity']))==Decimal(str(fees[s['ydental_fee_id']]['ydental_quantity']))
                            and s['ydental_price_version']=='S05:'+str({r['id']:r for r in projections['snapshots']}[fees[s['ydental_fee_id']]['ydental_price_snapshot_id']]['ydental_price_id'])
                            for s in projections['sources']),'native_source_lines_match_original_price_and_quantity',checks)
                    elif label == 'payments':
                        require([Decimal(str(r['amount'])) for r in rows]==[500,240]
                            and all(r['state']=='reconciled' and r['move_state']=='posted' and r['id']==r['origin_payment_id']
                                and r['company_id']==1 and r['currency_id']==inv['currency_id'] and r['partner_id']==inv['partner_id']
                                and r['payment_type']=='inbound' and r['partner_type']=='customer' for r in rows),'original_two_native_reconciled_payments500_240',checks)
                    elif label == 'partials':
                        payments = {r['id']:r for r in projections['payments']}
                        require(len(rows)==2 and [Decimal(str(r['amount'])) for r in rows]==[500,240]
                            and all(r['debit_invoice']==r['company_id']==1 and r['origin_payment_id'] in payments
                                and r['credit_move']==payments[r['origin_payment_id']]['move_id'] for r in rows),'original_two_native_partials740',checks)
                    elif label == 'settlement_payments':
                        require(len(rows)==2 and [Decimal(str(r['ydental_amount'])) for r in rows]==[500,240]
                            and all(r['ydental_store_id']==r['ydental_patient_id']==1 and r['ydental_cashier_id']==5
                                and r['ydental_payment_id']==r['id'] and r['ydental_channel']=='cash' for r in rows),'original_S10_cashier5_cash500_240',checks)
                    elif label == 'patient':
                        require(one(rows)['active'] and one(rows)['ydental_partner_id']==inv['partner_id'] and not one(rows)['ydental_merged_into_id'],'source_patient1_canonical_partner',checks)
                    elif label == 'patient_relation':
                        require(len(rows)==1 and not rows[0]['ydental_superseded_by_id'],'patient1_store1_current_relation',checks)
                    elif label == 'modules':
                        installed = {r['name']:r for r in rows}
                        deps = {'ydental_settlement','ydental_exam','ydental_print','ydental_treatment','account','sale_stock','purchase_stock','base_report_wkhtmltox'}
                        require(len(rows)==92 and deps<=set(installed),'92_modules_and_PDF_dependencies_installed',checks)
                        for module in ('ydental_settlement','ydental_print'):
                            manifest = __import__('ast').literal_eval(c.fixed(module+'/__manifest__.py').decode())
                            require(installed[module]['latest_version']==manifest['version'],'installed_version:'+module,checks)
                    elif label == 'report_action':
                        report = one(rows)
                        xmlids = {r['module']+'.'+r['name']:r for r in projections['report_xmlids']}
                        require(xmlids['ydental_settlement.ydental_settlement_pdf_report']['model']=='ir.actions.report'
                            and report['id']==xmlids['ydental_settlement.ydental_settlement_pdf_report']['res_id']
                            and report['model']=='ydental.settlement.receipt' and report['report_type']=='qweb-pdf-wkhtmltopdf'
                            and report['paperformat_id']==xmlids['ydental_print.ydental_pdf_a4']['res_id']
                            and not report['attachment'] and not report['attachment_use'] and not report['save_as_attachment'],
                            'installed_native_report_action_exact_fixed_XML',checks)
                    elif label == 'report_groups':
                        require(len(rows)==1 and rows[0]['report_id']==report['id']
                            and rows[0]['gid']==result['effective_required_groups']['ydental_base.ydental_base_group_user'],
                            'installed_report_group_actual_user5_has_group',checks)
                    elif label == 'report_views':
                        require(len(rows)==2,'exactly_two_expected_QWeb_views',checks)
                        for view in rows:
                            identifier = view['key'].split('.')[1]
                            path = 'ydental_settlement/' + ('report/ydental_settlement_templates.xml' if identifier=='ydental_settlement_pdf' else 'views/ydental_settlement_templates.xml')
                            require(view['id']==xmlids[view['key']]['res_id'] and xmlids[view['key']]['model']=='ir.ui.view'
                                and view['active'] and view['type']=='qweb' and not view['inherit_id'],'installed_QWeb_identity:'+identifier,checks)
                            arches = view['arch_db']
                            require(isinstance(arches,dict) and 'en_US' in arches,'QWeb_base_arch:'+identifier,checks)
                            expected_tree = c.expected_template(path,identifier)
                            for lang in ('en_US','zh_CN'):
                                # Native translated field fallback, never writes a translation.
                                arch = arches.get(lang,arches['en_US'])
                                require(c.xml_tree(ET.fromstring(arch))==expected_tree,'QWeb_structural_fixed_source:'+identifier+':'+lang,checks)
                    elif label == 'paperformat':
                        paper = one(rows)
                        require(paper['id']==report['paperformat_id'] and paper['format']=='A4' and paper['orientation']=='Portrait'
                            and [float(paper[k]) for k in ('margin_top','margin_bottom','margin_left','margin_right')]==[12,16,14,14]
                            and paper['dpi']==96 and paper['disable_shrinking'],'installed_A4_paperformat_exact_XML',checks)
                    elif label == 'languages':
                        require({r['code'] for r in rows if r['active']}=={'en_US','zh_CN'},'installed_active_Chinese_locale',checks)
                    elif label == 'attachment_pointers':
                        pointers = [(r['store_fname'],r['checksum']) for r in rows]
                        reference = c.read(c.ROOT / c.BASELINE)
                        require(len(pointers)==164 and all(sha1s.get(f)==v for f,v in pointers)
                            and c.sha(json.dumps(pointers).encode())==reference['attachment_pointer_sha256'],
                            '164_attachment_pointers_and152_filestore_exact',checks)
                        result['attachment_pointer_count']=164
        require(result['statement_count']==contract['maximum_statements'],'all_frozen_statements_once',checks)
        result['status']='READONLY_ELIGIBILITY_COMPLETE_PENDING_GPT'
    except BaseException as error:
        result['status']='BLOCKED'
        result['exception_type']=type(error).__name__
        result['blocker']=str(error) if isinstance(error,AssertionError) else 'EXCEPTION_NO_RETRY'
        result['sqlstate']=getattr(error,'pgcode',None)
    finally:
        if conn is not None:
            try:
                conn.rollback()
                result['rolled_back']=True
            except BaseException as error:
                result['status']='BLOCKED'
                result['rollback_error_type']=type(error).__name__
            finally:
                conn.close()
                result['closed']=bool(conn.closed)
        result['finished_at']=datetime.now(timezone.utc).isoformat()
        result['duration_seconds']=round(time.monotonic()-started,3)
        result['all_table_signatures']=signatures
        result['source643_exact']=len(signatures)==643 and all(signatures[k]==v for k,v in c.read(c.ROOT/c.BASELINE)['all_table_signatures'].items())
        result['source_after_second_snapshot_claimed']=False
        result['native_paid_invoice_workbench_button']='NOT_AVAILABLE_BY_FIXED_residual_gt_zero_DOMAIN'
        c.save(c.PRIVATE/'projections.json',projections)
        c.save(c.PRIVATE/'statement-trace.json',trace)
        c.save(c.OUT/'readonly-result.json',result)
    print(json.dumps({k:result.get(k) for k in ('status','blocker','actual_connections','statement_count','source643_exact','rolled_back','closed','duration_seconds')},ensure_ascii=False))
    return result['status']=='READONLY_ELIGIBILITY_COMPLETE_PENDING_GPT'


if __name__=='__main__':
    assert sys.argv[1:]==['--execute'],'only explicit --execute after frozen REST gate'
    sys.exit(0 if execute() else 1)
