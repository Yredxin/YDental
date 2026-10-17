# S10-P0-20 最终22行退出表

原GAP-02/GAP-03保留。本表是实际收尾结果，不把回滚中间输出、安装成功或A票据子证据写成整个S10通过。

|行|现行要求|P0-20实际结果|最低补齐动作 / 责任|
|---|---|---|---|
|F1|S10-F1（独立合成数据）：治疗600+检查80+发药6×10=740，出账740→实收500欠240→补240结清。重复请求不再收款/出账。|A_SCOPED_PASS_EXISTING_PAID_BILL_ONLY; new B economic transaction rolled back|复用W3/W5原生740/核销子证据；B新源350+390及幂等，不重收旧500+240。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|F2|S10-F2：已收740→申请退100→他人批准，在途100/实退0→确认真实退100，累计已退100/净收640。拒绝另一申请须原因且不产生退款。|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新申请100/异人批准/实际执行、驳回50、unknown80核实未付撤销；原额度并发证据按未改财务代码范围复用。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|F3|S10-F3：实际微信录成现金且已日结→财务审批解锁留原因→更正登记→再日结，没有真实资金往返；实物退药另进待核查。|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新日期/渠道日结解锁更正再结；尾审原凭证及零伪退款。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|F4|S10-F4：真实诊疗/检查/发药、批次扣减→结算→补旧文书/重印票据，费库款不再变化，调价也不改原已确认费用。|BLOCKED_B_TEXT_ECONOMIC_SIGNATURE_MISMATCH_NO_FULL_TRANSIENT_DIFF|先冻结稳定存储字段比较器；事务内before/after完整快照、全差异和脱敏索引落盘再断言；不能从本次无差异证据认定根因。GPT另行授权后在新合法源完成文字/钱货不变与票据。 / S10；原版职责交GPT裁定|
|F5|S10-F5（另一个独立场景）：旧账270、新账200，均选中，实收300→先核旧270，再核新30→旧账0、新账欠170，保留两张账单和一笔300收款。仅选新账时不得擅自核旧账。|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|复用原270+200原生核销子证据；B新同源多账选中/未选+实际普通前台Web支付。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|F6|S10-F6：前台小李有A结算权可从前台收款，无结算权者只能看到获准摘要。B看到A欠270仅只读；不能在B收A款，A权限且上下文合法时到A处理。|A_SCOPED_PASS_LEGAL_READ_EXPORT_ONLY; B role/negative matrix NOT_RUN|B普通前台工作台及新付款；六岗位真实服务拒绝、跨店/公司/附件原测试范围复用或列缺。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T01|740重复/并发出账；来源有效出账一次|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|复用原源唯一/幂等与独立双事务证据；B新源bill重试不增来源。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T02|740收500补240及重试；应收240→0，原生核销和实收一致|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|旧500/240只复用；B新350/390真实原生partials及同key重放。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T03|负/超额折扣、明确免单；非法拒绝，原因齐，零账无假收款|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新负/超额折扣拒绝、零额posted但无资金。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T04|退款自批与并发批准；自批拒绝，在途+已退不超允许额|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新请求自批拒绝；原独立审批/额度竞争子证据复用，未验HTTP丢响应仍列缺。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T05|退款失败/未知/实际完成/重试；不伪已退、不重复资金记录|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新unknown核实、取消释放、实际执行；未知平台真实性不当合成门槛，HTTP未知后重放证据仍保留缺口。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T06|未收款减免；只调应收，不记实退|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新未收款waive，仅贷项与应收，无现金退款。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T07|日结后改支付方式；财务解锁/原因/再确认，无伪退款|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新cash→wechat真实原生更正凭证、解锁重结，无资金往返。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T08|已出账数量更正、文字更正和实物退回；反向来源正确，文字不动费库，未退不回库|BLOCKED_TEXT_INVARIANT; quantity/physical return scenarios NOT_RUN|同前先修证据工程；新合成同源文字/数量/实际退回分开核账款与实物。当前失败来源封存，不重放旧W5或已收款。 / S10；原版职责交GPT裁定|
|T09|同法人调拨与跨法人交易；实际收发/凭证对应、公司店铺隔离|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B全新原生同公司move及跨法人sale/purchase/invoice/bill/lot链；不重跑旧R3链。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T10|他店代收/无权医疗全文或票据；越权拒绝，摘要与全文分离|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B六岗位服务board/pdf/pay拒绝；他店摘要/附件原生矩阵未覆盖项保留。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T11|中文票据及部分收退款；实收/欠款/在途/已退准确，法人门店正确|A_SCOPED_PASS_CURRENT_PAID_BILL_PDF_ONE_PAGE_ONLY; other B receipts NOT_RUN|A真实页面一次paid740/0中文PDF，B新当前bill/receipt/refund及原状态PDF子证据；不称历史原版/多页全通过。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T12|安装升级及F4真实全链；事件、价格、批次、费账款一一对应|BLOCKED; native B install exit0 only; business chain rolled back, upgrade NOT_RUN|保留新B安装PASS子证据与旧全链范围；新合法源补分组联调与S10-only upgrade，不能用A页面或回滚日志替代持久全链。 / S10；原版职责交GPT裁定|
|T13|F5旧270新200收300及仅选新账；核销270+30、欠170，未合并账单；未选不核|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新多账日期/稳定ID/仅新账核销，原账不合并；普通前台Web实际付款。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T14|F6前台有/无billing权及跨店摘要；同一结算服务鉴权，无按岗位默认放开，无跨店代收|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B前台有权Web和六岗位无权服务；跨店摘要原限定证据。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
|T15|已确认600调价620后结算/重印；退款驳回；仍取600快照；驳回原因和审计齐、不生贷项/退款|BLOCKED; transient old600/new620 step not committed evidence; original reprint unproved|在新合法同源链证明旧600调620不重算，取得可追溯原始票据字节后验证原样取回；S12正式快照职责与此原TC是否承接交GPT裁定，不自行免测。 / S10；原版职责交GPT裁定|
|T16|日结锁后补录、解锁更正、删除/篡改审计；锁覆盖新增/更正，合法补录双时间可查，单据日志不可普通删改|NOT_RUN_IN_P020; compatible historical subassertions retained without expansion|B新跨日补录双时间、锁/解锁/再结、单据/审计普通write/unlink拒绝；旧事实不删改。；仅在GPT对新停止条件裁定/授权后执行。 / S10；原版职责交GPT裁定|
