"""Pure-file 22-row exit inventory; does not import Odoo or connect anywhere."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/evidence/s10-p0-20'
p=ROOT/'.local/s10-p0-20'
history=json.loads((ROOT/'docs/evidence/s10-p0-15/gap03-delta.json').read_text())
issue=json.loads((p/'issue34.json').read_text())
text=issue['body']
requirements={}
for line in text.splitlines():
    if line.startswith('S10-F'):
        requirements[line[4:6]]=line
    if line.startswith('|S10-T'):
        fields=line.strip('|').split('|');requirements[fields[0][4:]]=fields[1]+'；'+fields[2]
minimal={
'F1':'复用W3/W5原生740/核销子证据；B新源350+390及幂等，不重收旧500+240。',
'F2':'B新申请100/异人批准/实际执行、驳回50、unknown80核实未付撤销；原额度并发证据按未改财务代码范围复用。',
'F3':'B新日期/渠道日结解锁更正再结；尾审原凭证及零伪退款。',
'F4':'B新同患者治疗/检查/药房真实链、结清后原责任人confirm及文字correct、PDF不变经济；实物退回另核同原药事件。历史原版仍缺。',
'F5':'复用原270+200原生核销子证据；B新同源多账选中/未选+实际普通前台Web支付。',
'F6':'B普通前台工作台及新付款；六岗位真实服务拒绝、跨店/公司/附件原测试范围复用或列缺。',
'T01':'复用原源唯一/幂等与独立双事务证据；B新源bill重试不增来源。',
'T02':'旧500/240只复用；B新350/390真实原生partials及同key重放。',
'T03':'B新负/超额折扣拒绝、零额posted但无资金。',
'T04':'B新请求自批拒绝；原独立审批/额度竞争子证据复用，未验HTTP丢响应仍列缺。',
'T05':'B新unknown核实、取消释放、实际执行；未知平台真实性不当合成门槛，HTTP未知后重放证据仍保留缺口。',
'T06':'B新未收款waive，仅贷项与应收，无现金退款。',
'T07':'B新cash→wechat真实原生更正凭证、解锁重结，无资金往返。',
'T08':'B新数量correct关联原费+贷项、纯文字经济签名全等、同原药event真实退回quarantine且不增领量不减费款。',
'T09':'B全新原生同公司move及跨法人sale/purchase/invoice/bill/lot链；不重跑旧R3链。',
'T10':'B六岗位服务board/pdf/pay拒绝；他店摘要/附件原生矩阵未覆盖项保留。',
'T11':'A真实页面一次paid740/0中文PDF，B新当前bill/receipt/refund及原状态PDF子证据；不称历史原版/多页全通过。',
'T12':'B正常install/S10-only upgrade，真实S08/S09/库存/费/账/款/文书同源链；A完成真实UI；仍缺原版不由当前PDF代替。',
'T13':'B新多账日期/稳定ID/仅新账核销，原账不合并；普通前台Web实际付款。',
'T14':'B前台有权Web和六岗位无权服务；跨店摘要原限定证据。',
'T15':'B已确认600后发布620仍按600出账，confirm/correct/PDF签名全等，驳回无贷项/退款及审计；历史原版存取产品缺口仍BLOCKED待GPT裁定。',
'T16':'B新跨日补录双时间、锁/解锁/再结、单据/审计普通write/unlink拒绝；旧事实不删改。'}
rows=[]
for h in history['rows']:
    old=h['gap02_original_row'];ident=old.get('id') or old.get('row') or old.get('key')
    if ident is None:
        ident=h.get('id') or h.get('row');assert ident is not None,old.keys()
    ident=ident.replace('S10-','')
    assert ident in requirements,(ident,requirements.keys())
    row={'id':ident,'requirement_verbatim_current':requirements[ident],'historical_GAP03_row_unchanged':h,
         'new_effective_sources':{'P016':'21dc2dc / W5 OID2100310 eligibility READONLY; no UI/PDF','P017':'68c9096 / current product static workbench only; no installed claim','P018':'432c06f / BLOCKED; no business PASS','P019':'a2fa26e / reviewed physical metadata gate only; Web/PDF BLOCKED'},
         'missing_specific_assertion':old['old_remaining_gap_verbatim'],
         'minimum_current_test':minimal[ident],'responsible_stage':'S10; formal immutable original snapshots S12 explicitly referred for GPT decision',
         'class':'NECESSARY_EVIDENCE_MISSING'+(';FEATURE_DEPENDENCY_ORIGINAL_PDF' if ident in ['F4','T12','T15'] else ''),
         'S10_exit_blocking_before_test':True,'current_result':'NOT_RUN; preflight inventory only'}
    rows.append(row)
assert len(rows)==22 and len({r['id'] for r in rows})==22
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'exit-table-initial.json').write_text(json.dumps({'historical_source':'docs/evidence/s10-p0-15/gap03-delta.json','historical_sha256':hashlib.sha256((ROOT/'docs/evidence/s10-p0-15/gap03-delta.json').read_bytes()).hexdigest(),'rows':rows,'later_stage':['S12 formal templates/snapshot and tax originals','S13 unified UI/50 sessions/continuous backup + final user acceptance'],'production_pending':['actual accounts/tax/currency/payment platform policy'],'no_unilateral_TC_exemption':True},ensure_ascii=False,indent=2)+'\n')
report=['# S10-P0-20 初始22行退出表','', '旧GAP-02/GAP-03原字节保留。新表不是通过裁定；原历史子证据按来源/版本适用，禁止跨库拼链。P016资格、P017静态、P018失败、P019元数据子证据的结论逐行相同并完整保存在JSON。','', '|行|现行需求原文|最低补测/仍缺断言|责任/退出阻断|','|---|---|---|---|']
for r in rows:report.append('|'+r['id']+'|'+r['requirement_verbatim_current'].replace('|','/')+'|'+r['minimum_current_test']+'|S10 / 是（补测前）；不自行免测|')
report += ['', 'S12完整正式快照、S13美化/50会话/持续备份/统一用户验收与生产审批分别保留；它们不扩成当前测试前置。明确TC里的原版重印没有同源原件，也没有当前S10原版取回接口，不能免测或用重新渲染冒充，最终交GPT裁定。', '', '工具缺陷：原生累计连接≠池容量、正常postgres目录读取、finally-only请求账本。新增执行器修正，旧失败永久保留。']
(ROOT/'docs/s10-p0-20-exit-table-initial.md').write_text('\n'.join(report)+'\n')
print('22 row exit inventory written')
