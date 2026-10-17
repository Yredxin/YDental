"""File-only closeout of the actual STOP; no runtime entry points."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/evidence/s10-p0-20'
PRIVATE=ROOT/'.local/s10-p0-20'
def read(p):return json.loads(p.read_text())
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base='a2fa26e37d350910668742869764c9ed102641ca'
# New finalizer only operates on captured files; original execution versions remain frozen.
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==base,'Historical finalizer is sealed after delivery commit'
checks=[]
for p in ROOT.glob('scripts/s10_p0_20_*.py'):
 compile(ast.parse(p.read_text()),str(p),'exec')
checks.append('all final scripts parse and compile without loading Odoo')
for fp in ['execution-freeze.json','round1-freeze.json']:
 f=read(OUT/fp)
 for name,h in f['file_sha256'].items():
  if fp=='execution-freeze.json' and name.startswith('scripts/s10_p0_20_'):
   p=OUT/'round0'/(Path(name).name+'.txt');assert sha(p)==h,(fp,name)
  else:assert sha(ROOT/name)==h,(fp,name)
 checks.append(fp+' all frozen bytes match original or archived exact execution source')
for name,h in [('preflight','ff1360ba80761105cd7f256c7f0fb724df21dd3cb52d0a73fb20b8d436c2bfd3'),('round1','b1112a56a19c4cb6c004d13c1a0de0113e44510ff0aa583a231153ece8867f50')]:
 raw=read(PRIVATE/(name+'-api-raw.json'));body=(PRIVATE/('preflight-body.txt' if name=='preflight' else name+'-body.txt')).read_text()
 assert raw['body']==body and hashlib.sha256(body.encode()).hexdigest()==h
 checks.append(name+' REST body exact, initial/increment not overwritten')
assert read(OUT/'source-before.json')['signatures']==read(OUT/'source-after.json')['signatures']
assert read(OUT/'source-final-decision.json')['PASS']
assert read(OUT/'economic-web-verification.json')['old_filestore152_unchanged']
assert read(OUT/'B-final-rollback-verification.json')['all_failed_B_fixture_business_rolled_back']
assert read(OUT/'A-pdf-visual-review.json')['PDF_sha256']==sha(OUT/'A-current-internal-bill.pdf')
assert read(OUT/'http-reconciliation.json')['complete_counter_and_status_equal']
checks.append('actual A HTTP/PDF/economics and W5 final evidence consistent; B rollback capture consistent')
rows=read(OUT/'exit-table-initial.json')['rows']
results={'F1':'A_SCOPED_PASS_EXISTING_PAID_BILL_ONLY; new B economic transaction rolled back',
 'F4':'BLOCKED_B_TEXT_ECONOMIC_SIGNATURE_MISMATCH_NO_FULL_TRANSIENT_DIFF',
 'F6':'A_SCOPED_PASS_LEGAL_READ_EXPORT_ONLY; B role/negative matrix NOT_RUN',
 'T08':'BLOCKED_TEXT_INVARIANT; quantity/physical return scenarios NOT_RUN',
 'T11':'A_SCOPED_PASS_CURRENT_PAID_BILL_PDF_ONE_PAGE_ONLY; other B receipts NOT_RUN',
 'T12':'BLOCKED; native B install exit0 only; business chain rolled back, upgrade NOT_RUN',
 'T15':'BLOCKED; transient old600/new620 step not committed evidence; original reprint unproved'}
next_actions={'F4':'先冻结稳定存储字段比较器；事务内before/after完整快照、全差异和脱敏索引落盘再断言；不能从本次无差异证据认定根因。GPT另行授权后在新合法源完成文字/钱货不变与票据。',
 'T08':'同前先修证据工程；新合成同源文字/数量/实际退回分开核账款与实物。当前失败来源封存，不重放旧W5或已收款。',
 'T12':'保留新B安装PASS子证据与旧全链范围；新合法源补分组联调与S10-only upgrade，不能用A页面或回滚日志替代持久全链。',
 'T15':'在新合法同源链证明旧600调620不重算，取得可追溯原始票据字节后验证原样取回；S12正式快照职责与此原TC是否承接交GPT裁定，不自行免测。'}
for r in rows:
 r['current_result']=results.get(r['id'],'NOT_RUN_IN_P020; compatible historical subassertions retained without expansion')
 r['S10_exit_blocking_after_test']=True
 r['actual_new_evidence']=['A: execution-result.json, default/patient DOM + screenshots, native HTTP/PDF + invariant gates'] if r['id'] in ('F1','F6','T11') else []
 if r['id'] in ('F4','T08','T12','T15'):r['actual_new_evidence']+=['B native install result; R0/R1 failure logs; strict readonly full snapshots and rollback verification; no committed scenario PASS']
 r['minimum_completion_action']=next_actions.get(r['id'],r['minimum_current_test']+'；仅在GPT对新停止条件裁定/授权后执行。')
write(OUT/'exit-table-final.json',{'overall':'S10_TECHNICAL_EXIT_BLOCKED','phase_review_ready':False,'history_22_rows_preserved':True,'new_window_maximum':'A scoped paid bill native UI/current PDF subevidence only','rows':rows,'permanent_original_reprint_gap':'No W5 same-source historical original; no retrospective PDF invention','S12_S13_production':'separate later-stage/production duties; no blanket exemption of S10 TC'})
report=['# S10-P0-20 最终22行退出表','','原GAP-02/GAP-03保留。本表是实际收尾结果，不把回滚中间输出、安装成功或A票据子证据写成整个S10通过。','','|行|现行要求|P0-20实际结果|最低补齐动作 / 责任|','|---|---|---|---|']
for r in rows:report.append('|'+r['id']+'|'+r['requirement_verbatim_current'].replace('|','/')+'|'+r['current_result']+'|'+r['minimum_completion_action']+' / S10；原版职责交GPT裁定|')
(ROOT/'docs/s10-p0-20-exit-table-final.md').write_text('\n'.join(report)+'\n')
A=read(OUT/'execution-result.json');nativeB=read(OUT/'B-native-connections.json')
budget={'source_strict_RO_RR':2,'A_independent_RO_RR':3,'maintenance':{'A':1,'B':1},'CREATE':{'A':1,'B':1},'B_independent_RO_RR_attempts':3,'B_RO_attempt1':'failed guessed table; rollback/close, full snapshot unavailable','A_metadata_process':1,'A_metadata_import':1,'A_metadata_commit':1,'A_HTTP':1,'A_Firefox_context':1,'A_HTTP_and_download_counts':A['browser_counts'],'A_native_cumulative':{'metadata':len(A['native_metadata_backend_pids']),'Web':len(A['native_web_backend_pids'])},'B_native_cumulative':sum(r['count'] for r in nativeB),'native_cumulative_total':len(A['native_metadata_backend_pids'])+len(A['native_web_backend_pids'])+sum(r['count'] for r in nativeB),'explicit_connections_total':10,'all_connections_total':30,'A_native_observed_pool_max':5,'B_native_observed_pool_max':max(r['observed_pool_max'] for r in nativeB),'pool_configured_max':8,'B_normal_install':1,'B_initial_native_chart_and_feature_configuration':'committed; scope-qualified new B only','B_first_scenario_attempts':2,'B_business_commits':0,'B_pay_attempts_in_failed_transaction':2,'B_pay_amounts_transient':[350,390],'B_confirm':1,'B_text_correct':1,'B_PDF':0,'B_other11_scenarios':0,'B_HTTP_Firefox_businessPOST':0,'B_upgrade':0,'fix_rounds_used':1,'remaining_fix_round_used':False,'reason_no_more_retry':'economic invariant unknown and no field diff => mandatory STOP','protected_clone_connections':0,'historical_replay':0,'product_core_old_evidence_AGENTS_changes':0,'sudo_OS_PG_Docker_network_special':0,'Issue_Project_state_changes':0,'merge_deploy_S11':0,'native_SIGSEGV_observed':False,'historical_native_root_cause':'UNKNOWN; not declared repaired'}
write(OUT/'actual-budget.json',budget)
write(OUT/'final-file-verification.json',{'checks':checks,'count':len(checks),'exit_code':0,'runtime_not_reexecuted':True,'scope':'file integrity and consistency, not replacement business PASS'})
print(json.dumps({'file_checks':len(checks),'exit_code':0,'all_connections_total':30,'overall':'BLOCKED'}))
