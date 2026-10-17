# YD-N1 R1 — S10-CLOSEOUT-PLAN-v1.1

本文件保存用户已审阅的五组收尾计划的完整执行范围及 v1.1 两项修订。
来源为“用户直接批准的 S10 收尾计划”；不是 GitHub P0-25 授权。用户先要求
PLAN_ONLY，随后提出 v1.1，最后明确回复 `Implement the plan.` 选择完整实施。
原始确认与修订保存在 evidence/s10-closeout-v1/user-approval.json。

## 1. 当前起点与状态

仓库 Yredxin/YDental，origin https://github.com/Yredxin/YDental.git；目录
/home/redxin/code/odoo/odoo-sd/code/sd-addons；分支
codex/s10-settlement-finance-r1-20261013；父 HEAD
7d52d9e342d49837f3b81a7da3b6e7794a5cde01；core 只读
f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。
规划时及实施接管时本地/远端匹配、工作树干净；#23 OPEN/3，#34 OPEN/273，
#35 OPEN/0。原 #34 270 条正文未变，只有 P024 预检、交付和裁定新增。

已采成果：P020 A 真工作台与当前 PDF；P021 已提交财务、临床库存来源、
内部 bill 原件和限定权限子证据。尚缺：A同源文书及旧原件、B普通单据审计、
C新原件附件权限、D剩余恢复/丢响应、E带业务升级。历史风险：v→6、无效 JSON、
P020 未保存瞬时差异及历史 Native SIGSEGV 均 UNKNOWN，旧 FAIL 不改判。

正式依据：

- P021：https://github.com/Yredxin/YDental/issues/34#issuecomment-6230102263
- P022：https://github.com/Yredxin/YDental/issues/34#issuecomment-6230526897
- P023：https://github.com/Yredxin/YDental/issues/34#issuecomment-6230830175
- P024：https://github.com/Yredxin/YDental/issues/34#issuecomment-6231120531
- 五组需求参考（不恢复旧窗口）：https://github.com/Yredxin/YDental/issues/34#issuecomment-6230134070
- 顺序技术复核/最终统一验收：https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328

P023/P024 单字段诊断已收口，无新异常不重复哈希、模板字符或客户端诊断。

## 2. 设计、源码及修复范围

A 使用 ydental_clinical/models/ydental_clinical_service.py 的 _operate、_acquire、
_held、_append、_confirm、_correct、_release；queue._locks 经 intake._all_locks
及其 queue 扩展，按 patient→supply→intake→queue 顺序各更新固定 mutex revision。
每个文书动作四锁各+1。release 仅返回 document_id，不猜返回版本。
原生 clinical JS 在 confirm/correct 后自动 release 和跳转，因此本包四动作
明确 MODEL_NATIVE_COMMITTED；原件链接、网络权限和 D 为真实 Firefox/HTTP/RPC，
不把模型调用称浏览器链。

A/C 使用 ydental_settlement/models/ydental_settlement_original_service.py 的
_original_invoice、_bill_original_bytes、_workbench；controllers/bill_original.py
受控取回；models/ir_attachment_original.py 在 core limited-field token 之前挡原件。
每次重新检查 live settlement read + export write、公司、门店、患者family和真实费源。
取回验证保存字节 SHA，不调用渲染。原件模型无普通 ACL、记录及附件不可普通改删。

B 使用 ydental_settlement_record.py::write/unlink 和 ydental_access_audit.py::write/unlink，
目标为 settlement.source、settlement.payment、access.audit；模型六项与网络六项分别标记。
C 使用 access._bind/_scope/_check/_grant/_switch 和 patient._patient/family 链。
D 使用 settlement._operate/_refund_uncertain/_refund_recover/_refund_execute/
_refund_capacity 及 action controller；E 使用当前 manifest/data/views/report 和正常模块加载。

默认只新增 scripts/s10_closeout_v1_*.py、docs/s10-closeout-v1-*.md、
docs/evidence/s10-closeout-v1/*。不改产品、旧脚本/报告/证据、AGENTS、S01—S09 或 core。
已知测试工程问题用新执行器解决：真实返回值、金额与来源交接、先存后判、独立提交核验、
停 Web 后升级。若确有产品缺陷，最小候选限 original_service、ir_attachment_original、
controllers/bill_original。其他文件/退款/业务锁变更先说明具体待批准差异。
不削弱权限、锁或不可变规则，不开发完整 S12 或 S13 专项。

初次执行+最多2轮定向修复，每轮新固定版本/预检；只继续核清已提交/已回滚后的未执行步骤。
未知经济结果、泄露、身份漂移、证据损坏或 Native 崩溃直接停止，不使用修复额度盲重试。
唯一升级失败不追加第二次升级。

## 3. 测试环境、保护与预算

唯一旧库例外是 P021 ydental_s10_test_20261017050000_21b0cafe，OID2122140，
cluster7694897083368259627，仅复制前/最终各一次 RO/RR，ROLLBACK/CLOSE；
核有效最终645表/schema、业务、原件、权限、198份filestore，前后不变。
不在源上运行 Odoo/Web 或业务。无活动连接阻碍安全复制；不终止他人连接。
关闭首次源连接后，维护1次/CREATE1次，从该源 TEMPLATE 到唯一新副本，独立OID/config/
loopback端口/data_dir；filestore真实复制无硬链接/共享回写。新库名按
ydental_s10_test_<UTC14位>_<8位十六进制串> 一次生成并冻结，不改名绕过失败。
初始完整核对通过才执行业务；不修 P022 无效 JSON 作为基线。

W5、R3、P013/14/18/19/20、P022/24 及其他旧库均0连接/复用/修改。
P024 两次一致不证明全库可用；当前新基线另取，风险保留。

继承但不重放：patient1/execution1/doc1/责任人7，fee1—4=600+80+40+20，
invoice1 posted/paid740 residual0，付款350+390；原件1/附件161，原件2/附件630 previous1；
既存退款、日结、数量、实物、跨法人和前台付款子例。裸ID不足，必须核完整来源关系。

|预算|全包上限|
|---|---:|
|源只读连接|2|
|维护/CREATE|各1|
|显式独立RO/RR（含源和停止尾审）|28|
|Odoo进程|6|
|native pool|8|
|升级前/后HTTP及Firefox|各最多1窗口，不同时运行两座Web|
|浏览器context同时|6|
|HTTP含重定向/资源/RPC|600|
|受控原件GET含拒绝|12|
|原件生成/旧件重渲染|0/0|
|D退款凭据渲染|2|
|C授权类别变化含恢复|8|
|新增S01审计（另逐事件/对象校验）|500|
|S10-only升级|1|
|D独立来源费用/账单/入款/退款申请/实退|6/6/6/2/最多2|
|丢响应/先查证后同键重试|各1|
|其他历史资金库存重放|0|

## 4. 五组最小用例及验收

### A 同源文书与原件

前置核医疗write、员工公司门店、来源资格、执行状态、pending/v2、无有效editor。
serving/reserved/verify 需要现场租约却不满足则停止，不强抢/清状态。
原责任人7合法scope/connection acquire→confirm→纯文字correct→release。
acquire返回token/content/version，confirm以返回版本CAS创建v3/author7/previous真实v2；
correct只改预先固定一个合成说明字段，原因齐，创建v4/author7/previous v3。
release后独立读回confirmed/v4，编辑字段全清。每步完整存储差异、COMMIT及独立核验后交接。
固定四mutex每动作+1，文书/版本/审计按字段列明，不影响价费账款库存。
必要普通编辑心跳最多3次，沿真实API，仍四锁各+1，只延长过期时间，不改配置、无新版本。

合法账号从真工作台点已有v1链接，字节/记录/附件不变；SHA必须
05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4。
核下载actor/store/invoice/original/version/SHA审计；不调用生成接口。
资格/版本/锁/经济/原件不符或提交未知立即停止。

### B 六项不可改删

按已提交marker/fee→source→invoice、payment和精确target_model/target_id的pay审计绑定对象；
从来源读金额/币种，实际首款350，不复制500常量。普通账号三个对象各write/unlink，
MODEL六项；再真实 /web/dataset/call_kw RPC 六项。每项保存完整原行/存在性/异常与差异。
MODEL意外成功先存证再回滚停止，RPC意外成功立即停后续动作并保全。
原件模型其他19项不能替代这六项；不重新收款。

### C 原件与附件权限

最小矩阵：合法UI保存字节；read缺失/export存在、read存在/export缺失各拒绝；撤权旧页/旧Binding；
错误店、跨公司真实存在来源且先证目的店read/export前提；错患者family、同公司混店投影反例；
患者服务合法create/request_merge/confirm的回滚历史别名正例。投影不改已过账原单/旧原件，
明确MODEL_WITH_FIXTURE，回滚后行集完全相同，不冒充已提交原生业务。
合法管理员在副本内真实授权服务操作，末尾恢复初始权限；前提不足则BLOCKED，不sudo绕过。

普通账号和匿名的native content、image、image-download及适用RPC最小代表请求；
原件source_facts/附件raw真实RPC读，以及私有方法RPC限制。按固定core misc.py构造并验签
limited_field_access_token(attachment,'raw',scope='binary')，不改attachment.access_token。
每次保存真实body/MIME/长度/SHA。图片200须解码确认等于固定原生占位图/尺寸变换像素，
且无原件内容；不能只改状态白名单或仅检查不以%PDF开头。download拒绝，秘密不进Git。
泄露、夹具未回滚、权限未恢复、拒绝原因无法区分或响应体无法判定即STOP。

### D 失败恢复与丢响应防重

复用P021 unknown80取消/done100/rejected50和FC2无核实拒绝、failed/unknown恢复释放、
done终态和同键幂等，仅在原裁定/方法兼容范围。不访问旧库，不重退旧款。
仅一个CLOSEOUT-T05新患者/非药品项目/价源/真实受理接诊/一次新事件，无材料药品或库存。
一张6单位账单、一次6入款，2退款申请，异人finance_approval write批准。
通过真实 refund_uncertain(outcome='failed') 记录受控合成未出款；零贷项/outbound、额度保护。
独立财务 verified_not_paid=True +原因 recover回approved，不计实退。
真实浏览器HTTP一次execute；受控截获服务端完成响应、只丢客户端交付一次，客户端unknown，
不得写成业务failed或未付款。独立新RO核唯一done/付款/贷项/partial/receipt后，才一次同actor/
store/key/完整payload重试，already_accepted、无第二资金或execute审计。实际仅新入6/出2/净4。
一张新账应唯一2贷项、2outbound及对应partial；角色/公司/门店/时间/渠道均核实。
外部平台未接入，只称合成线下确认和受控客户端丢响应。未知经济结果即停，不换源重试。

### E 带业务升级

A—D通过且权限恢复后保存完整基线，停止本包HTTP/Firefox并确认退出，再唯一一次正常
-u ydental_settlement；不全模块升级/安装/旧测试入口。前后完整stored业务/schema/权限/
临床库存/原件附件/filestore保全。metadata按实际物理来源+复合身份逐记录/字段解释，
继承投影不按仅ID覆盖、不整表豁免。升级后一次独立Web窗口，只回归工作台、同SHA原件、
读取/导出拒绝和native附件保护；不新收退款。最终完整尾审。
升级异常、未知语义metadata或保护事实漂移即停，不追加升级。

## 5. 静态预检、证据及失败处理

任何DB前检查所有变量/参数/返回值/分支/来源交接；A token/version/previous/release返回；
B精确审计模型/ID/真实金额；D异人、actor幂等及不变payload；scope默认店/revision/
撤权/提交路径；正常/异常/COMMIT未知/独立读回失败/子进程提前退出整段控制流。
新原件生成预算0，旧经济来源不在可派发集合。纯文件正反例包含金额、数量、患者/公司/
混源、重复ID/继承、删行、错误锁增量、无效JSON、保存/读回失败和伪成功marker。
静态PASS不等于业务PASS。

全量节点仅source前后、clone初始、升级前后、最终尾审。小动作完整采集所有相关stored
业务/身份/权限/附件，不机械扫全库；展示字段另列，Decimal精确值不只汇总。
服务器原返回文本及服务器摘要、客户端解析、序列化及落盘读回分层保存。
完整私有值/全差异先存再判；公开逐表行列脱敏索引；未知经济变化保留字段级事实。
同一对象多保存副本不是独立测量。新口径仅适用新批准测试，不修旧FAIL/无效文件。

intent→派发→返回/未知→flush和差异保存→COMMIT→新RO/RR读回→成功marker。
无独立读回不交接；已知提交不重交；未知提交只用预留只读预算尾审/封存。

## 6. 22行退出映射

H21=f58d920，产品be1d12a；H20A=7a4bdb9；V为本包最终冻结产品/脚本版本，当前不虚构SHA。
历史复用需方法、依赖、权限和数据语义兼容，保留原来源/裁定，不拼不同库业务为同一次全链。
保留原22行对象，逐行新增本包证据和最终版本。下表是目标，不是本包已通过声明。

|行|需求/已有证据及复用理由|待补/最终版本和退出判据|
|---|---|---|
|F1|740主链/部分付清/防重；H21四费及350+390核销，W旧500+240另列|E保全；H21→V兼容，不重收|
|F2|异人审批/实际退/驳回；H21退100拒50unknown80取消已提交|D缺口+E；H21+V，无伪实退/重款|
|F3|日结解锁更正重结无伪往返；H21重分类和实物分列|E；H21→V，不重演|
|F4|费库款后补文书/旧原件；H21链和原件已提交但pending/v2|A+E；V文书v4、零经济变化、同SHA|
|F5|270+200选300核270+30、仅新账；H21原生+Web子例|E；H21→V，独立来源/后续余额不混写|
|F6|有权前台/无权/他店摘要；H21和旧限定Web/摘要|C+E；历史兼容+V，无跨店原件泄露|
|T01|重复/并发唯一出账；H21幂等+历史C双backend；R3崩溃不算竞态|兼容/E；历史+H21→V，不重演竞态|
|T02|部分付款/重试/原生核销；W500+240和H21 350+390分别有效|E；各原来源→V，不拼付款链|
|T03|负/超折扣拒绝、零账无款；H21已采|E；H21→V，零付款|
|T04|异人/并发控额；H21自批拒及C/FC1/FC2限定竞争|D身份/E；历史+V，不声称新并发|
|T05|failed/unknown/完成/重试；H21+FC2受控恢复/终态|D+E；V实际HTTP/独立提交，唯一出款贷项回执|
|T06|未收款减免只调应收；H21减80仅贷项|E；H21→V，不算现金退款|
|T07|锁后改渠道须解锁重结；H21已采|E；H21→V，不重放close9|
|T08|数量/文字/实物分离；H21独立数量与主链退药quarantine|A+E；H21+V，三子例不拼患者|
|T09|同法人调拨/跨法人原生交易；H21已采|E；H21→V，不新增交易|
|T10|他店/无权全文票据拒绝；旧服务/Web及H21模型；图片缺口|C+E；V原件附件token/RPC实证分层|
|T11|中文票据金额状态法人门店；H20A/H21/历史指定票面|C/D凭据≤2/E；历史+V，新页逐张目视，非税票到账|
|T12|安装升级/F4全链；H21安装和已提交临床库存费款/H20A页面|A+E；V同源文书及带业务升级均过|
|T13|选账270+30、不合并/不核未选；H21已采|E；H21→V，不新付款|
|T14|服务鉴权/岗位不默认放开；H21+旧摘要旧页|C+E；历史+V，read/export/撤权/错店分验|
|T15|旧600调620不重价/原件/驳回；H21价源及原件previous链|A后同SHA+E；H21+V，不生成替代件|
|T16|补录双时间/锁/不可改删；H21日结子项已提交|B+E；V六项MODEL/RPC分列，旧行不变|

必要项仍FAIL/BLOCKED/NOT_RUN必须给具体功能/证据和最低补齐，不能用检查器/安装成功顶替。

## 7. 顺序、交付、回滚与终点

准备：批准记录→完整离线门禁→冻结代码/脚本/SQL/预算/身份→预检→来源/副本准入。
A+B：四文书动作/旧件链接/六项负向，已提交独立读回后交接。
C+D：权限/图片/token/RPC及一个独立新T05来源，无泄露、权限恢复、唯一结果明确。
E：停Web→一次升级→受影响回归→最终尾审→22行退出表。

交付固定SHA、逐文件SHA256、真实命令/退出码/预算、血缘/源保全/提交检查点、文书版本链、
旧件真实下载/图片及RPC字节证据、D唯一资金链、升级差异、22行历史新增层、未运行和风险、
5—10步效果回看入口。截图/PDF/响应先核合成脱敏，凭据/完整私有临床值不入Git。
正常线性提交推送、不reset/clean/force、不改Issue/Project状态、不合并部署。
回滚只停自有进程保全库/附件/原件/日志，不DROP/删事实；代码必要时新逆向提交，
不卸载抹原件。无生产部署/生产回滚。

五组及22行必要缺口通过、独立读回、旧事实保全、无未知经济结果或越权，才申请GPT技术复核。
正式交付后STOP，等待GPT；技术PASS后按6110178328顺序S11—S13、最终统一用户验收，
执行者不自行启S11，生产另批。P020 A/P021已采成果和旧500+240/退款14/close9/退款13分页/
旧文书/单字段诊断不重做。

## v1.1 仅两项修订（覆盖上文相应流程，不扩大其他范围）

1. 以用户明确批准v1.1为依据，保存完整计划、确认、固定版本、身份、预算、预检和停止条件。
   GitHub同步单列：成功保存真实评论/REST全文读回；未成功保留未同步状态，不伪造记录、
   不算业务FAIL。即使未同步，最终须完整本地报告/固定提交/索引/实际Git推送状态供独立复核。
   此调整不覆盖任何工具安全拒绝；不得换工具/身份/入口重试被明确拒绝的操作。
2. D任何新上游执行/费用/出账/收款前，冻结执行人、不同审批人、公司门店、真实日期/渠道、
   有效权限与日结状态。_bill::_close_guard_any检查全部渠道，换渠道不能规避；_pay/
   _refund_request/_refund_execute各自日期渠道约束仍验。不默认账号当天开放，不解锁/
   改旧日结，不伪造时间、不关校验、不管理员绕资格。需要新身份或扩权先列待批准差异，
   不现场扩权。随机尾码为既有guard的8位十六进制串。

实际执行精确名称、版本及动作分配见预检和 execution-contract.json；它们只能细化本计划，
不能增大预算或放宽停止条件。本文件不将未来用例标为已执行。
