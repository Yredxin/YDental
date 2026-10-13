# S08-B定向返工报告

唯一依据[GPT-REVIEW6135903692](https://github.com/Yredxin/YDental/issues/32#issuecomment-6135903692)及#23/#32当前正文和全部3/17条有效评论。继续原分支`codex/s08-b-clinical-pharmacy-r1-20261013`，返工基线`7ccb25cf6a54732caf7007c39498d393b6a96929`，原product/test/final及所有历史证据保留。

固定rework product `0a49fac432bcac0197eeddae9675b8cddb46e631` → test `f887d828da292d0da0513e667469b9df28ee4f05` → final完整SHA固定于#32本次交付评论。product→test仅7个测试/runner文件，产品树相同；test→final仅AGENTS/文档/脱敏证据。原S01—S08-A产品零修改。所有PASS均Codex自测，不是GPT亲测、技术PASS或用户验收。

## 1. 四项问题逐项闭环

|复核项|先行真实负向/反证|最小产品修正|最终正负结果|
|---|---|---|---|
|B1 椅旁品种/数量/批次|原产品空材料及项目2/材料1未抛UserError，真实失败栈保留|新药品事件要求明确本店SKU关联、真实同药lot、原生单位及合计实量；S07派生再次验SKU；无合法native move不确认fee|PASS：空/错SKU/单位/量/不足拒绝零事件费库；已发生空/错报保留pending、原actor/time/报告JSON；原责任人明确核对后追加实际consumption/move/fee；重复恢复只一次|
|B2 关键字段冻结校验|**原“空白可直接issued”未复现**：S05 intake._text封装默认required=True，原空白在draft创建即拒绝；不是没有后端保护|按明确返工要求允许临床文本未完善draft；issue服务端逐行复验SKU/active/方向/单位/数量及规格、用法、频次、疗程；dispense再次验；无医学默认值|PASS：逐字段空串/空白/None、旧形态不全行均拒开立；draft留存，无task/queue/fee/move；完善后合法开立；真实HTTP409/200及Firefox|
|B3 真SKU与S05收费来源|第二真实SKU在同pharmacy mapping下可借第一药10元，原负向真实FAIL|仅price-write有据发布本店SKU/单位↔独立medicine目录/已发布版本；唯一SKU与目录绑定、禁止无政策泛化共价；实际事件仍按S05原时点quote并冻结快照|PASS：同一药房方向两SKU独立10/27元，缺关联新执行拒绝/余量不变；已发生未关联事实pending不用另一药价；后来99不重价；药房单权实际4+2保留；第三43元SKU UI独立发布|
|B4 跨法人来源权限|来源只有A账号授权的合法目标B被新增company_ids条件拒绝|移除额外目标公司硬拦截和UI过滤，继续原S05可信source、目标mapping/open/capacity与事务；不增加目标普通权限|PASS：A-only定时/不定时跨B成功，B普通read/write/RPC/切店拒绝；满额/停接/非法目标回滚，原serving保留；最后名额及不定时幂等真竞争|

先行测试提交`abbe2bc01ddf6dbc6f3cd08a2e1d5206518a9ee0`保持原产品字节，隔离复现库安装3FAIL+2ERROR/67；逐项含义与原栈见[reproduction.json](evidence/s08b-rework/reproduction.json)。未为迎合复核结论删除原保护。

## 2. 真实流程与操作示例

医生medical-write进入真实S06工位→叫号/start→原S08-A打开文书并自动保存→治疗工作台。新椅旁空批次、另一SKU、量不相等分别409并无事件。明确已发生但缺批次创建pending，用原负责人提交真实批次2及核对证据，原事件确认20元及native move2；原空报告仍保留，不把核对时间替代实际时间。

处方草稿先缺规格/用法/频次/疗程，issue409；医生逐项明确填写后冻结同一pharmacy方向的A6、B2、C1。原医生独立保存交还/退出，前台明确报到，药房仅pharmacy-write进入/叫号/start。未关联C拒绝且仍余1；实发A4及B2分别40/54，结束本段，唯一余量待报到。price-write独立有据发布C↔43元目录，后来重新报到/start，实发A2及C1分别20/43，结束无后继。原A累计6，保留两个completed执行、原actor/station/time及lease释放；无第二套队列/库存余额/财务账本。

来源只有A公司范围的医生选择真实B目标，定时占一次预约额、不定时创建不占额；再次定时满额拒绝，目标有权manager明确停接后不定时拒绝，改写本店非法目标拒绝，原来源与两份成功receipt保留。B普通RPC写拒绝；后台模型另验证目标真实接收时占现场、到期/非法/停止和容量恢复。

[committed SQL投影](evidence/s08b-rework/committed-business-projection.json)固定原B项目600、原单4+2及新增多SKU/恢复/跨法人结果：原B处方66，新增处方67，原核对事实99；各fee有SKU、catalog、S05 snapshot/price_version/currency，实际lot/move SKU和数量一致。原responsible/actual_at保留。模型夹具回滚结果不冒充这些实际committed浏览器事实。

## 3. 全量测试与TC追溯

最终同一固定test、同一全新隔离库`ydental_s08b_test_20261013015317_e72d1fca`，OID1287669，专属端口18176，cluster7694897083368259627。Ubuntu26.04.1、Python3.12.15、Odoo20核心`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，PG18.6 Docker127.0.0.1:5432、shm256MiB。只设置本批libpq会话并行0/maintenance16MiB，实测SHOW记录；环境参数、镜像、服务、核心和依赖0修改。

|测试关口|状态/数量|固定证据|
|---|---|---|
|安装/升级/持久业务再次升级|PASS 80/78/78，0FAIL/0ERROR；63模型+15真实HTTP/RPC；保留原49+11，新增14+4；安装额外2原生资产初始化|[final-tests](evidence/s08b-rework/final-tests.json)，逐测试结果和每命令/exit/logSHA|
|真实独立PostgreSQL竞争|PASS A16+B原20+新增5=41；每组首轮不同backend、双barrier，deadlock0，有界serialization重试|final-tests primary_evidence中的两份完整probe JSON|
|Firefox原A、原B及返工|PASS 88+24+23=135项、21+13+14=48图，pageerror0；A10+B1真实响应屏障，默认sandbox|[visual-review](evidence/s08b-rework/visual-review.json)，逐图SHA与人工目视核对|
|实际中文POT/PO及错误前缀|PASS307/307、metadata/遗漏0、稳定前缀完整|[translation](evidence/s08b-rework/translation-ydental_s08b_test_20261013015317_e72d1fca.json)|
|隔离guard|PASS5，无连接/服务变更|[guard](evidence/s08b-rework/guard.json)|
|权限/审计/原生库存/价源/历史|PASS35项SQL全0；模型/HTTP/RPC/export/attachment/角色/撤权/CAS/历史事实实际负向|[最终audit](evidence/s08b-rework/audit-after-business-upgrade.json)、SQL投影、安全自审|
|带committed业务upgrade守恒|PASS24表完整行签名及capacity totals相等|[business-upgrade-signatures](evidence/s08b-rework/business-upgrade-signatures.json)|
|纯文书经济无副作用|PASS13表签名相等，含新medicine.link|[pure-document-economic-signatures](evidence/s08b-rework/pure-document-economic-signatures.json)|
|完整旧源码树迁移/生产回滚|NOT_RUN；明确旧schema默认值夹具+真实-u验证历史不重写，不冒称完整历史源码树演练|test_rework_legacy_confirmed_history...|
|S08-C PDF/签署/打印、S09真实结果、S10真正出账付款退款、S11—S13、50会话生产验证|NOT_RUN|未授权/未启用；财务表NOT_INSTALLED|
|生产部署|BLOCKED|历史S07 SIGSEGV及原B/本轮候选Firefox崩溃根因UNKNOWN|

|原TC|本次固定回归覆盖与结果|
|---|---|
|T01/T02|PASS 原A七文本/52牙/自动保存/CAS/独占/断线终态，A16竞争、A88Firefox，纯文书13经济守恒|
|T03/T04|PASS 真实项目/source/key唯一，缺价/缺料/已发生pending/原价核对，原生故障原子回滚；新增B1/B3|
|T05/T06|PASS 原A交还保存/版本/唯一后继/编辑释放及D1→D2真实项目→D1补文字不重费库|
|T07/T08|PASS 检查草稿/冻结/未做取消/独立追加，真实处方4+2/余量唯一/超量重复拒绝，新增不完整issue及多SKU|
|T09/T10|PASS 真实HTTP权限/RPC/context/export/attachment/旧页/药房单权；原差额更正/退回保留，旧未经SKU核对来源不能新差额|
|T11|NOT_RUN S08-C打印|
|T12/T13|PASS 新库安装/两次升级/中文/安全/队列历史/跨日closed许可/两药师真竞争及账实|
|T14/T15/T16|PASS 定时不定时跨法人来源及失败恢复/容量竞争、牙位状态、原时间/价/批次/操作者/审计；新增B4|

命令按final-tests保存原数组执行：`scripts/s08b.py install/upgrade/probe/probe_a/export/audit/preview/serve --db ... --port 18176`；Firefox分别`s08b_a_browser.py --terminal-races`、`s08b_browser.py`、`s08b_rework_browser.py`；中文`s08b_translation.py --db ...`，guard为`-m unittest scripts/test_s08b_guard.py`。原始日志、配置、口令仅留.local私有目录；GitHub只提交脱敏JSON/失败栈/hash及合成截图。

## 4. 字段、动作与配置

[返工合同](s08b-rework-contracts.md)替代原合同中药品按queue mapping取价、目标公司账号要求及草稿必填三处描述；其余原12动作/锁序/事务沿用，增加`publish_medicine`与`verify_medicine`共14封闭动作。新增link/event/fee字段、单位、必填/未知历史处理见[字段字典](s08b-rework-data-dictionary.md)，角色与状态表见合同。

关联仅审计元数据，不是第二价表；每店catalog↔SKU/unit一一明确。没有发布泛化共价生产政策；合成10/27/43/99/600不是生产批准价。规格/用法/频次/疗程必须医生决定，不自动normal；正式剂量/签发/药物政策、税币种、生产取价策略仍待业务审核。

## 5. 用户效果验证

仅在新隔离合成库按角色走上述真实工作台：price-write核对真实SKU/目录/单位/已发布版本并发布关联；医生选真实批次确认椅旁、缺项处方保存后完善/开立；前台明确报到原处方；药房仅自己的pharmacy-write执行4+2，核对真实批次、费用及唯一余量；源A医生受控转B且无B普通权限。响应不明时按原A/B核对入口保留原页，不自动重放。

所有48张最终图实际逐张打开核验，页面仅合成患者、人员、药品/临床内容。截图各对应真实HTTP和committed SQL；不能用合成药品测试替代正式用药政策审核。可通过visual-review直接定位最终A/B/R图及结果JSON。

## 6. 数据、审计、失败与回滚

35项SQL包括原28及药品SKU/量/单位/费快照catalog/currency/批次move、未核对pending零账、开立字段和发布审计。原生move/line/quant是唯一存货权威，来源费用尚未出账；account_move/account_payment均NOT_INSTALLED。24表升级签名包含原23+medicine.link，13纯文字经济表包含原12+medicine.link。历史旧确认记录不自动补关联、重价、动库；明确旧字段默认夹具验证这一点，新更正无可信关联拒绝。

[完整失败/修正清单](evidence/s08b-rework/attempt-history.json)保留3个本轮新库及全部命令/logSHA/框架frame。包括原产品3FAIL+2ERROR；候选空JSON→False断言及真实目标营业前提；旧取消草稿行混入余量选择器；Firefoxdatetime零秒格式；候选页面导航崩溃。探针真实serialization冲突属于有界竞争记录，不掩盖为无错误运行。最终库首次A Firefox在旧版本保存检查遇patient-mutex serialization耗尽Odoo原生5次重试，返回非JSON HTTP500，11检查/2图FAIL；[独立失败记录](evidence/s08b-rework/original-a-http-retry-exhaustion.json)保留原栈/hash与shutdown。只读35不变量仍0，同固定代码、同参数、新合成UI前提完整重放后才取得下列最终PASS；没有增加重试次数、改变heartbeat、删断言或修改A/core。这是运行失败和生产竞争风险，后续PASS不称根因修复。诊断helper的regex unpack/Decimal JSON编码错误只影响本机只读导出，未改业务数据。

[本轮候选Firefox崩溃诊断](evidence/s08b-rework/rework-candidate-browser-crash.json)：第二次药房start导航报page crashed，已完成21检查；原JSON/14图/日志hash保留。专属预览正常SIGTERM退出0、无Odoo SIGSEGV记录、PG OOM=false均为已记录观察，不证明浏览器崩溃时的allocator/资源根因。测试器关闭已完成角色context以限制资源占用，后续PASS不等于根因修复。原B浏览器候选崩溃、S07历史SIGSEGV及长期DSM根因继续UNKNOWN，生产BLOCKED。

[环境保全](evidence/s08b-rework/environment-preservation.json)：原114库OID/名称完整保留，本轮只新增3个隔离B合成库，无删除/重置；db20与odoo12镜像/启动/卷/cluster/shm不变，原Odoo42433健康，核心字节不变。全部本轮预览只处理自身configSHA/PID。A/R及候选正常停止退出0；最终B浏览器已PASS24/13后外层编排被SIGTERM终止/exit143，子进程退出码UNKNOWN，核查PID与匹配config进程均已不存在，无crash记录，仅移除该失效自有marker后恢复R及升级验证；[独立记录](evidence/s08b-rework/browser-orchestration-interruption.json)保留，不冒称全程exit0。Project初/末各双快照21字段/15项/6视图及字段/7公开workflow深比较一致，0mutation；#32S08/进行中/Todo/OPEN、#31待用户验收、后续待启用。

回退先禁用本批入口或停精确PID/config预览，保留DB/filestore/logs/提交。不可卸载B/删历史或退A运行已完成业务库；代码回退不撤销已发生用药及native move。新增字段/模型为加法，无自动历史补写；正式逆向迁移/生产回滚NOT_RUN，需后续单独保留来源的迁移审核。

## 7. 复核申请与残余风险

仅申请GPT对固定返工product/test/final及所有证据再次独立技术复核。四项本批必测关口已完成；B2原结论部分反证明确说明。Codex自测不代表GPT技术PASS或用户验收。正式药物/字段/剂量/签发/共价/税币种/生产政策、性能/生产稳定性仍未批准或未验证。完整旧源码树迁移与生产回滚未运行，不能扩大宣称。

## 8. GitHub交付与停止

在原独立分支正常推送并读回远端HEAD及产品树、报告/机器证据字节。#32发布`[CODEX] S08-B定向修正交付与再次技术复核申请`，固定全部完整SHA和证据链接；逐字读回后立即停止，等待GPT独立复核。不改Project/Issue状态、不关闭、不标S08整体待验收、不启用C/S09、不合并/强推/生产部署。
