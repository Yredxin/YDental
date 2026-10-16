"""File-only P0-16 freeze, deterministic gate tests, and redacted delivery."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import re
import sys

import s10_p0_16_contract as c
from s10_p0_16_readonly import check_grants, group_closure


def authority():
    result = {'authorization':c.AUTH,'previous_GPT_ruling':6214578731,'base':c.BASE,'core':c.CORE,
        'issues':{},'comments':{},'read_method':'GitHub API full body/all comments; full old bodies compared to prior complete reads'}
    assert c.read(c.PRIVATE/'ref.json')['object']['sha']==c.BASE
    for number in (23,34,35):
        issue = c.read(c.PRIVATE/f'issue{number}.json')
        comments = c.read(c.PRIVATE/f'comments{number}.json')
        assert len(comments)=={23:3,34:232,35:0}[number]
        result['issues'][str(number)]={'body_sha256':c.sha(issue['body'].encode()),'state':issue['state'],
            'body_characters':len(issue['body']),'comments':len(comments),'url':issue['url']}
        result['comments'][str(number)]=[{'id':r['id'],'url':r['url'],'updated_at':r['updated_at'],
            'characters':len(r['body']),'body_sha256':c.sha(r['body'].encode())} for r in comments]
    comments=c.read(c.PRIVATE/'comments34.json')
    assert comments[-1]['id']==c.AUTH
    assert not any('P0-16' in r['body'].split('\n')[0] and '[CODEX]' in r['body'].split('\n')[0] for r in comments)
    return result


def static_tests(plan):
    checks=[]
    def passed(label,condition):
        assert condition,label
        checks.append(label)
    passed('643_schema_matches_public_P011',len(plan['schema'])==643)
    passed('all643_fixed_signatures_available',len(c.read(c.ROOT/c.BASELINE)['all_table_signatures'])==643)
    functions={'count','encode','sha256','convert_to','coalesce','string_agg','to_jsonb',
        'current_database','pg_backend_pid','pg_control_system','format_type','in'}
    aliases={}
    for entry in plan['queries']:
        sql=entry['sql']
        passed('read_only_literal:'+entry['label'],sql.startswith(('SELECT ','SHOW ')) and ';' not in sql
            and not re.search(r'\b(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|CALL|COPY|DO|GRANT|REVOKE|INTO|LOCK)\b',sql,re.I)
            and not re.search(r'\b(FOR\s+(UPDATE|SHARE)|pg_advisory|pg_read_file|dblink|lo_export|set_config)\b',sql,re.I))
        passed('fixed_parameter_arity:'+entry['label'],sql.count('%s')==len(entry['params']))
        for name in re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*\(',sql):
            passed('side_effect_free_function:'+entry['label']+':'+name,name.lower() in functions or name.upper() in ('SELECT','WHERE','OR','AND'))
        aliases.clear()
        for table,alias in re.findall(r'\b(?:FROM|JOIN)\s+public\."?([a-z_0-9]+)"?(?:\s+(?!WHERE\b|ORDER\b|ON\b|JOIN\b)([a-z_0-9]+))?',sql,re.I):
            passed('frozen_table:'+entry['label']+':'+table,table in plan['schema'])
            aliases[alias or table]=table
        for alias,column in re.findall(r'\b([a-z_0-9]+)\."?([a-z_0-9]+)"?',sql,re.I):
            if alias in aliases:
                passed('frozen_column:'+entry['label']+':'+alias+'.'+column,column in plan['schema'][aliases[alias]])
        if len(aliases)==1 and ' JOIN ' not in sql and entry['label'] not in ('catalog','identity','other_connections') and not entry['label'].startswith('hash:'):
            selected=sql.removeprefix('SELECT ').split(' FROM ')[0]
            for column in selected.split(','):
                column=column.strip()
                if re.fullmatch('[a-z_0-9]+',column):
                    passed('unqualified_projection:'+entry['label']+':'+column,column in plan['schema'][next(iter(aliases.values()))])
    passed('every643_hash_uses_matching_order_and_LF',len([q for q in plan['queries'] if q['label'].startswith('hash:')])==643
        and all("||E'\\n'" in q['sql'] and 'pg_catalog.sha256' in q['sql'] for q in plan['queries'] if q['label'].startswith('hash:')))
    passed('empty_table_LF_matches_old_algorithm',hashlib.sha256(b'\n').hexdigest()==c.read(c.ROOT/c.BASELINE)['all_table_signatures']['ydental_print_job']['sha256'])
    tree=ast.parse((c.ROOT/c.SCRIPTS[1]).read_text())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
        and isinstance(n.func.value,ast.Name) and n.func.value.id=='psycopg2' and n.func.attr=='connect']
    passed('exactly_one_physical_connect_call',len(calls)==1)
    passed('driver_import_not_offline',all(not isinstance(n,(ast.Import,ast.ImportFrom)) or
        not any(x.name.startswith(('psycopg2','odoo','requests','playwright')) for x in getattr(n,'names',[])) for n in tree.body))
    passed('only_one_controlled_cursor_execute_call',len([n for n in ast.walk(tree) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Attribute) and n.func.attr=='execute'])==1)
    good=[{'ydental_membership_id':1,'ydental_category':k,'ydental_level':v} for k,v in [('settlement','read'),('export','write')]]
    passed('minimum_actual_read_write_grants_pass',check_grants(good,1,{})=={'settlement':'read','export':'write'})
    for label,bad in [('grant_count_cannot_replace_missing_export',good[:1]),
        ('export_read_rejected',[good[0],dict(good[1],ydental_level='read')]),
        ('other_membership_rejected',[dict(good[0],ydental_membership_id=2),good[1]]),
        ('unknown_rank_rejected',[dict(good[0],ydental_level='administrator'),good[1]])]:
        try:
            check_grants(bad,1,{})
        except AssertionError:
            checks.append(label)
        else:
            raise AssertionError(label)
    passed('native_group_transitive_cycles_terminate',group_closure([1],[{'gid':1,'hid':2},{'gid':2,'hid':1},{'gid':2,'hid':3}])=={1,2,3})
    expected=c.expected_template('ydental_settlement/report/ydental_settlement_templates.xml','ydental_settlement_pdf')
    passed('Chinese_bill_template_present','内部结算账单' in json.dumps(expected,ensure_ascii=False))
    service=c.fixed('ydental_settlement/models/ydental_settlement_service.py').decode()
    passed('paid_invoice_UI_limitation_proved',"'amount_residual', '>', 0" in service
        and "'report_pdf_no_attachment'" not in service and 'report_pdf_no_attachment=True' in service)
    passed('native_report_name_lookup_supported',"('report_name', '=', report_ref)" in c.fixed('odoo/addons/base/models/ir_actions_report.py',core=True).decode())
    return {'layer':'STATIC_REVIEW_ONLY','PASS_count':len(checks),'checks':checks,'SQL_connections':0,
        'CREATE_HTTP_Firefox_business_PDF_sudo':0,'runtime_SQL_parser_and_PDF_engine_proven':False}


def freeze():
    c.repo_gate()
    p=c.plan()
    checks=static_tests(p)
    seal,_=c.files_gate()
    c.save(c.OUT/'sql-contract.json',p,exclusive=False)
    c.save(c.OUT/'offline-checks.json',checks,exclusive=False)
    c.save(c.OUT/'github-start.json',authority(),exclusive=False)
    source={path:{'sha256':c.sha(c.fixed(path)),'git':c.BASE} for path in c.SOURCE_FILES}
    source.update({'CORE/'+path:{'sha256':c.sha(c.fixed(path,core=True)),'git':c.CORE} for path in c.CORE_FILES})
    c.save(c.OUT/'static-source.json',{'files':source,'rank':c.rank_contract(),
        'report_action_XMLID':'ydental_settlement.ydental_settlement_pdf_report',
        'report_name_template_XMLID':'ydental_settlement.ydental_settlement_pdf',
        'paid_invoice_workbench_button':'absent due to residual>0 domain; endpoint separately protected; no UI request made',
        'translated_template_compare':'core convert.py template→t/full t-name; compare structure preserving attributes/text; zh_CN falls back to en_US for already-Chinese literal template'},exclusive=False)
    c.save(c.OUT/'execution-freeze.json',{'authorization':c.AUTH,'base':c.BASE,'core':c.CORE,'database':c.NAME,
        'created_at':datetime.now(timezone.utc).isoformat(),
        'script_sha256':{path:c.sha((c.ROOT/path).read_bytes()) for path in c.SCRIPTS},
        'sql_contract_sha256':c.sha((c.OUT/'sql-contract.json').read_bytes()),
        'source_SHA_manifest':source,'filesystem_seal':seal,
        'maximum_connections':1,'maximum_statements':p['maximum_statements'],'maximum_seconds':150,
        'transaction':'READ ONLY / REPEATABLE READ','zero_budget':c.ZERO,
        'SQL_actual_now':0,'connection_after_REST_readback_only':True,'runtime_retry':False},exclusive=False)
    print(json.dumps({'offline_checks':checks['PASS_count'],'scripts':c.read(c.OUT/'execution-freeze.json')['script_sha256'],
        'statements':p['maximum_statements'],'sql_contract_sha256':c.sha((c.OUT/'sql-contract.json').read_bytes()),
        'execution_freeze_sha256':c.sha((c.OUT/'execution-freeze.json').read_bytes()),'SQL_actual':0},ensure_ascii=False))


def finalize():
    c.repo_gate(execution=False)
    result=c.read(c.OUT/'readonly-result.json')
    frozen=c.read(c.OUT/'execution-freeze.json')
    assert all(c.sha((c.ROOT/k).read_bytes())==v for k,v in frozen['script_sha256'].items())
    private=c.read(c.PRIVATE/'projections.json')
    # No plaintext usernames, credentials, patient content, template arch or
    # attachment paths are copied to public results.
    public={k:v for k,v in private.items() if k in ('user','companies','store','memberships','grants',
        'group_xmlids','invoice','sources','fees','snapshots','invoice_lines','payments','partials',
        'settlement_payments','patient','patient_relation','modules','report_xmlids','report_action','report_groups','paperformat','languages')}
    views=[]
    for row in private.get('report_views',[]):
        item={k:v for k,v in row.items() if k!='arch_db'}
        item['arch_SHA256']={lang:c.sha(arch.encode()) for lang,arch in row['arch_db'].items()}
        views.append(item)
    public['report_views_hash_only']=views
    c.save(c.OUT/'eligibility-projection.json',public,exclusive=False)
    c.save(c.OUT/'statement-trace.json',c.read(c.PRIVATE/'statement-trace.json'),exclusive=False)
    c.save(c.OUT/'preflight-api-readback.json',c.read(c.PRIVATE/'preflight-api-readback.json'),exclusive=False)
    (c.ROOT/'docs/s10-p0-16-preflight.md').write_bytes((c.PRIVATE/'preflight-body.txt').read_bytes())
    old=[]
    for encoded in c.git('ls-tree','-r','--name-only','-z',c.BASE).split(b'\0'):
        if encoded:
            path=encoded.decode()
            expected=c.git('show',c.BASE+':'+path)
            assert (c.ROOT/path).read_bytes()==expected,'OLD_FILE_DRIFT:'+path
            old.append((path,c.sha(expected)))
    budget=dict(c.ZERO,W5_SQL_CONNECTION=result['actual_connections'])
    c.save(c.OUT/'verification.json',{'status':result['status'],'authorization':c.AUTH,'base':c.BASE,'core':c.CORE,
        'old_tracked_files_exact':len(old),'old_tracked_SHA_manifest':c.sha(json.dumps(old).encode()),
        'actual_budget':budget,'preflight_comment':c.read(c.PRIVATE/'preflight-api-readback.json')['comment_id'],
        'source643_exact':result['source643_exact'],'rolled_back':result['rolled_back'],'closed':result['closed'],
        'readonly_snapshot_count':1 if result['actual_connections'] else 0,
        'post_business_independent_second_source_measurement':'NOT_RUN / NOT_CLAIMED',
        'PDF_business_and_renderer':'NOT_RUN','native_paid_invoice_button_visible':False,
        'GAP03_modified':False,'GPT_or_stage_PASS_claimed':False,
        'requested_ceiling':'S10_P0_16_W5_USER5_SETTLEMENT_EXPORT_AND_BILL_SOURCE_READONLY_ELIGIBILITY_SCOPED_TECH_ACCEPTED',
        'S10_PRODUCTION_T12':'BLOCKED','R3_SIGSEGV_root_cause':'UNKNOWN','P017_authorized':False},exclusive=False)
    report=f'''# S10-P0-16 W5收费员5及内部账单来源严格只读准入报告

仅申请 `S10_P0_16_W5_USER5_SETTLEMENT_EXPORT_AND_BILL_SOURCE_READONLY_ELIGIBILITY_SCOPED_TECH_ACCEPTED`，由GPT独立复核决定。Codex本机结果 **{result['status']}**；不是PDF/Web业务PASS，不授权下一批。S10技术/生产及T12仍BLOCKED。

唯一授权 [6214616229](https://github.com/Yredxin/YDental/issues/34#issuecomment-6214616229)，上批裁定 [6214578731](https://github.com/Yredxin/YDental/issues/34#issuecomment-6214578731)作为生效历史引用，不重审或改GAP-03。原分支 `{c.BRANCH}`，固定父 `{c.BASE}`，core `{c.CORE}`；最终子提交由交付评论固定。

开工API完整读取#23正文/3评论、#34正文/232有效评论、#35 OPEN/0，远端及本地HEAD一致。旧#34前228条全文与此前完整读取逐字相等，后四条含P0-15预检/交付/新裁定/本次授权；没有已有P0-16预检或并行授权。[逐条正文SHA索引](evidence/s10-p0-16/github-start.json)。正式预检在任何SQL前发表并REST body逐字相等，原文见[预检](s10-p0-16-preflight.md)、[读回/时间与冻结SHA](evidence/s10-p0-16/preflight-api-readback.json)。

本批离线冻结3份执行/分析脚本的SHA、全部643表/列白名单、所有字面SQL与参数、首SHOW顺序、数据身份、权限/报表规则及预算。[execution-freeze.json](evidence/s10-p0-16/execution-freeze.json)和[完整SQL合同](evidence/s10-p0-16/sql-contract.json)固定每一条将执行的SELECT/SHOW；脚本没有导入Odoo或调用旧批入口。仅调用一次psycopg2.connect；先READ ONLY/REPEATABLE READ，再SHOW on/repeatable read，首业务SELECT前门禁生效；无行锁/advisory/DML/DDL/ORM。只读连接实际 {result['actual_connections']}，语句 {result['statement_count']}，耗时{result['duration_seconds']}秒，rollback={result['rolled_back']}、closed={result['closed']}；[逐语句证据](evidence/s10-p0-16/statement-trace.json)。失败原因 `{result.get('blocker','无')}`，无重试。

## 来源与643表

W5 `{c.NAME}` / OID2100310 / cluster7694897083368259627；config SHA `{c.CONFIG_SHA}`、marker SHA `{c.MARKER_SHA}`。文件封存152份manifest和164附件指针、92已安装模块与固定源后证据比较；具体检查成功/失败逐项见[只读结果](evidence/s10-p0-16/readonly-result.json)。全部643表本次同一只读快照与P0-14旧源后签名全等：**{result['source643_exact']}**，保护47/稳定31有独立子集门禁，不只按OID认资格。

643表内容SHA在服务器用明确pg_catalog无副作用内置函数计算：按id排序（无id按JSONB文本排序）的PG `to_jsonb(t)::text`，行间LF并保留尾LF，空表也为一LF；与历史Python逐行算法相同。只返回计数/hash，病历或password等全行不出服务器。客户只读取冻结的user/company/employment/grant、单据/报表安装元数据；私有原投影只在新700目录，公开字段有固定白名单、模板arch只公布SHA，不公布附件路径、姓名、登录、密码、医疗原文。

这是**一条连接的一次只读快照**，没有新业务、没有源后第二SQL连接，不能称业务前后独立全表实测。未运行字段/门禁以缺失或NOT_RUN处理。P0-13/P0-14克隆未连接/未复用；永久W5仍pending2，P0-14 confirmed3仅在那座克隆成立。

## user5本店实际权限与经济来源

实际最小[投影](evidence/s10-p0-16/eligibility-projection.json)显示user.active/share/company_id、allowed cid、store/company active，唯一membership及employee/resource的active/user/company关联；原生internal和YDental基础组按实际group关系及传递implied闭包判断，而非岗位名或管理员豁免。grant逐行含membership/category/level，按固定RANK none0/read1/write2验证settlement>=read、export=write。缺失、错关联或不满足即STOP，未补grant、换账号或登录。实际levels：`{json.dumps(result.get('actual_levels',{}),ensure_ascii=False,sort_keys=True)}`。既存medical权限仅作为原权限元数据保留，没有读取医疗全文或扩大授权；源643表相等亦约束权限未改，当前会话scope/revision尚未创建或实证。

invoice1需company1/store1、posted/paid740/residual0；source1→fee4/20、2→fee3/40、3→fee2/80、4→fee1/600，原qty1/1/4/2与S05价600/80/10/10快照、原生invoice line对应。原payment1/2为500/240、move posted/reconciled、两条partial回原invoice，总740；S10登记cashier5本店cash一致。患者仅校验canonical ID/partner/本店关系，不读取姓名病历。全部检查状态依`readonly-result.checks`，静态预期不冒称实际PASS。库存/价目/所有费源/款项表本次只有签名/必要只读投影，无新收款、退款、费用或退库。

## 报表安装态、真实入口与可执行边界

固定XML的report action XMLID是 **ydental_settlement.ydental_settlement_pdf_report**，其report_name与QWeb模板XMLID为 **ydental_settlement.ydental_settlement_pdf**；原生 `_get_report`允许按report_name查找。核实际ir_model_data、ir_act_report_xml、res_groups_report_rel、QWeb两个视图及paperformat、locale、92模块和base_report_wkhtmltox等依赖安装态；不把模板XMLID误认action XMLID。模型ydental.settlement.receipt、类型qweb-pdf-wkhtmltopdf、A4/96dpi/12-16-14-14边距、原YDental组和no attachment行为按固定源码逐字段比较。

`ydental_settlement/controllers/settlement.py:135` PDF GET端点及service `_report_payload:1077`/`_pdf:1159`、report abstract model与manifest引用均只读源码。report模板及workbench模板按Odoo core convert.py template→t/full t-name变换后逐结构比较，保留属性和文本，忽略XML格式缩进；zh_CN缺专属arch时按原生en_US回退，中文源文字本身仍须匹配。字段hash/实际视图ID与check结果公开，未动态编译或渲染QWeb，也未验证wkhtmltopdf可执行文件、字体或浏览器表现。

**新增的静态入口限制**：service `_workbench:1015–1019` 仅列amount_residual>0账单；`views/ydental_settlement_templates.xml:81`“下载中文 PDF”链接在该invoices循环内。所以paid/residual0的invoice1在当前工作台没有这个按钮。即使本批只读权限/action/template门禁成立，也只能支持受控端点的来源资格，不能宣称“现有页面能点击invoice1按钮”或直接启动下一批。后续若要求本人原生按钮，须GPT决定合法入口及必要最小产品差异；本批不改addon、不临时构造按钮、不借新收款/改余额显示旧单。服务 `_invoice:313`本身可读取已过账本店paid单，这是与页面列表不同的静态范围。

S10 `_pdf`为当前动态内部账单并写report_download审计，no attachment，不是历史字节重印。print_job历史0不等于所有PDF不存在，W5同源历史原版仍缺；R3外部PDF是不同来源。S12正式税务原件、生产科目/税/币种/银行渠道实际到账政策仍待批准。实际PDF生成、report_download、业务GET/POST均NOT_RUN/0。

## 离线验证、预算与交付

[离线检查](evidence/s10-p0-16/offline-checks.json)验证SQL字面/参数/表列、内置函数白名单、一处连接/受控execute、源SHA，及缺export、export只读、错membership、未知RANK、group传递闭包等确定性负例；没有模拟成功业务来替代现场证据。旧{len(old)}份tracked文件逐字节不变，core未改，[verification.json](evidence/s10-p0-16/verification.json)记录本批边界。

除W5最多一条严格只读连接外，其它数据库/maintenance/CREATE/Odoo HTTP/Firefox/业务GET或POST/PDF生成/文书价格资金库存附件写/Odoo CLI/直接ORM/sudo/OS-PG-Docker-防火墙-IPv6专项均0。不改旧库、证据、产品/ACL/core/AGENTS、Issue/Project状态，不合并部署或启S11。原GAP-03 22行及P0-14已接受事实不改写；W4元数据STOP、旧W5 browser exit1/final_audit NOT_RUN、R3 Native SIGSEGV UNKNOWN永久保留。

仅正常线性提交/推送许可新增文件，[SHA索引](evidence/s10-p0-16/sha256-index.json)覆盖全部新增文件（索引自身SHA由正式回执固定）。正式Codex回执REST逐字读回后立即STOP等待GPT；不自行授权P0-17、CREATE或执行下一批PDF。
'''
    (c.ROOT/'docs/s10-p0-16-readonly-eligibility-report.md').write_text(report)
    index()


def index():
    paths=sorted([p for p in c.OUT.iterdir() if p.is_file() and p.name!='sha256-index.json']+
        list((c.ROOT/'docs').glob('s10-p0-16-*.md'))+[c.ROOT/p for p in c.SCRIPTS])
    c.save(c.OUT/'sha256-index.json',{'base':c.BASE,'files':{str(p.relative_to(c.ROOT)):{'bytes':p.stat().st_size,
        'sha256':c.sha(p.read_bytes())} for p in paths},'self_hash':'fixed by final Codex GitHub delivery receipt; no recursive self-hash'},exclusive=False)
    print(json.dumps({'indexed_files':len(paths),'index_sha256':c.sha((c.OUT/'sha256-index.json').read_bytes())}))


if __name__=='__main__':
    assert len(sys.argv)==2
    if sys.argv[1]=='--freeze':
        freeze()
    elif sys.argv[1]=='--finalize':
        finalize()
    elif sys.argv[1]=='--index':
        index()
    else:
        raise AssertionError('unknown file-only operation')
