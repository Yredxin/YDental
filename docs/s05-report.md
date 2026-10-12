# S05交付报告｜YD-N1 R1

发起来源：用户当前明确启用Yredxin/YDental #29/S05。当前需求#23 R1正文/有效评论、#29正文及全部有效评论、GPT-ACTIVATE6115298923；#28最终技术复核6115295633及状态同步6115318214。开工检查6115339128已写回逐字读回。首次完整读取#23/#29于2026-10-11 23:56 UTC，收口再次核对当前来源。没有回读撤销旧计划、旧四份文档或上一Codex聊天补规则。

本报告是Codex技术自测交付申请；不是GPT复核通过、用户验收或生产上线批准。#28/#29保持OPEN，Project未写，不进入S06。

## 固定版本和环境

- 基线S04：`174a70df2cf8de515d0e781c59e6ce3825146313`。
- 分支：`codex/s05-intake-r1-20261011`，origin Yredxin/YDental；开工工作区干净。
- 产品：6818bc35c35e030976df71558b188844d4de1082。
- 测试：90d1a41f8559542aed36f4fc0ff22897c17fb392；product→test仅新增只读价格角色禁止确认演示快照的HTTP回归，不改变产品tree。
- final：本报告和证据所属最终commit，完整SHA固定于#29交付申请；test→final仅AGENTS/文档/脱敏证据。
- 核心锁定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明20.0 fork；使用核心`.venv/bin/python`，没有冒称已比对同SHA官方上游。
- 最终库：`ydental_s05_test_20261012003654_1b657de3`；127.0.0.1:5432/odoo、cluster 7694897083368259627，独立配置/data_dir/日志/精确dbfilter、HTTP18115、0 cron、SMTP禁用且进程只允许本库端点和本预览端口。创建OID和哈希见isolation evidence。
- 没有修改核心、odoo-12、业务库、历史库、既有服务、系统依赖、Project或认证安全控制。只终止过本会话由S05 runner创建并核对PID/config的临时预览。

## 完成范围

|需求/功能|完成情况|实现|
|---|---|---|
|R01原生复用/工程契约|完成|product/pricelist/UoM/currency，source binding、字典、动作、zh_CN及审计；不引入OCA|
|R21集团目录/本店价目/版本/快照|完成S05基础|catalog/mapping/price/snapshot；正价、区间、审核发布、原生旁路保护；无费用/收费/退款|
|R08区域预约与定时/不定时转诊|完成S05受理|S03 claim复用；定时目标预约额，不定时有效期内目标现场额；来源医生无目标任意写权|
|R09资格/到店/任务分离/返额/改期|完成|entitlement/arrival/task；S04真实首次到店、S03取消与新占+旧取消事务|
|R10换区/作废号契约|完成S05前置|S05唯一active受理位置，固定queue hooks，合成waiting/calling验证；非正式队列|
|R15停接基础|完成S05竞争边界|报到和S03营业共用supply锁；派生任务不绕目标停接|
|R22 S04真实联动|完成|canonical/current relation/_business_patient、真实活动merge冲突/迁移，保留origin/快照/arrival|
|正式锁价/承诺价政策|待业务发布|仅demo_confirmation；缺有效价失败，演示快照不是费用|
|S06真实队列/叫号/租约|NOT_RUN|固定私有hook及合成适配；未启用|
|S08/S09/S10真实临床/检查/费款|NOT_RUN|当前契约与合成验证不冒充真实联调|

模块：`ydental_intake`；测试模块：`ydental_intake_test`，业务库pre_init拒绝。没有未来空模块或平行容量账本。完整字段、状态、权限及恢复见[s05-data-dictionary.md](s05-data-dictionary.md)、[s05-contracts.md](s05-contracts.md)；自复核见[s05-security-review.md](s05-security-review.md)。

## 实际流程回放

|场景|合成前提/操作|结果与证据|
|---|---|---|
|F1跨区两项服务|同患者洁牙和种植各取得claim/任务，先报洁牙，再报种植|成功才撤旧位置、原任务pending、原资格保留；Firefox实际表单和T01/T03|
|F2先登记/已有资格零余额|现场登记仅有资格/任务，显式到店后明确报到；预约余额耗尽仍用原claim早到|无重复到店/任务/扣额，保留原时段；T02及HTTP|
|F3失败换区/双前台|目标draining拒绝；两独立RR连接报不同区|旧位置保持，最多一个active位置和一个合成waiting；T03/T04/T05真实竞争|
|F4转诊双分支|来源医生A受控转B，定时先占B预约；不定时合成7天，到B受理占现场；过期拒绝|目标无额不建半转诊、不改来源；模型/HTTP/并发T11|
|F5价格历史|A600、B650；同来源600快照后发布620；另一来源取新版本|旧快照600，B650；缺价拒绝，不默认0；并发发布/快照一致，Firefox真实审核发布|
|作废/取消区别|作废位置后原资格再报；显式取消资格才返额|过号次数保持；开始后的consume不能返；T12及Firefox|
|merge与新业务|真实S05预约/登记活动和S04确认竞争，两种先后|双方活动冲突blocked；先merge迁移canonical后新业务合法，origin和快照不重写；T09真实竞争|

实际没有创建S08医嘱/S09检查/S10费用；“医嘱不删/不退费”验证当前动作没有相关副作用和固定hook契约，不把不存在的真实业务当端到端完成。

## S05-T01—T13

|TC|结果|实际覆盖|
|---|---|---|
|T01|PASS|独立两区域资格/任务，数据结构无医生/工位绑定|
|T02|PASS|早到原槽、重复key和重复任务、零余量已有资格、到店唯一|
|T03|PASS|成功换区、目标停接拒绝保原位置/资格、明确任务|
|T04|PASS|两真实连接异区报到；一个位置+合成队列一个waiting|
|T05|PASS|report先/stop先均真实连接；walkin_report队列失败整笔回滚|
|T06|PASS|重复取消竞争、取消vsconsume两交错、S03返池时间分支、目标末额抢占后改期失败保原claim/position|
|T07|PASS|只读/撤权/旧revision/跨店、批量状态write、伪token/context和来源权限负向|
|T08|PASS|全景无额即失败，CBCT余额不动，不自动改服务|
|T09|PASS|新库安装/升级、配置与原生API；S04真实merge冲突/迁移，真实下游NOT_RUN明示|
|T10|PASS|集团/门店目录价目权限、A600/B650、发布冲突/缺价、历史快照、原生CRUD/复制保护|
|T11|PASS|模型及真实HTTP双分支、过期/缺额、定时目标末额双连接、来源不能任意目标写|
|T12|PASS|仅作废位置/同时取消资格、复用/拒已取消、过号不清零、已开始不返|
|T13|PASS|显式demo策略、生产策略拒绝、真实并发发布/冻结、来源恢复旧快照、不随新价改|

## 命令与数量

所有命令在sd-addons根执行，DB取上方最终库；实际退出码和日志SHA见[evidence/s05/isolation-attempts](evidence/s05/isolation-attempts)，原始日志只保留私有run，不上传。

|验证|命令|最终结果|
|---|---|---|
|安装|`../.venv/bin/python scripts/s05.py install --db DB --port 18115`|PASS：0 fail / 0 error / 27，exit0|
|升级|`../.venv/bin/python scripts/s05.py upgrade --db DB --port 18115`|PASS：0 fail / 0 error / 25，exit0|
|并发|`../.venv/bin/python scripts/s05.py probe --db DB --port 18115`|PASS：13组真实双连接竞争；deadlock0，exit0|
|Firefox|在guarded serve后，使用已有进程本地Playwright/Firefox/GTK资产运行scripts/s05_browser.py|PASS：Firefox 155.0，24/24；8张截图，exit0|
|隔离负向|`../.venv/bin/python scripts/test_s05_guard.py`|5/5 PASS，exit0|
|翻译|S05 runner export + 原生POT与zh_CN逐词比对|PASS：266/266，missing0，exit0|
|静态|compileall与git diff --check|PASS，exit0|

安装数含2项Odoo原生加载检查；真正S05业务是17模型+8真实HTTP=25项。并发探针另外13组，不拿单线程测试或合成队列冒充真实连接/真实S06。

## 参数与失败链

测试容量policy显式demo 1:2、floor、phone→reservation、cutoff0，只用于合成运行；S03生产发布参数没有由本轮演示自动批准。不定时转诊7天仅合成值，模型要求明确有效期而不默认7天。价格只demo_confirmation，正式锁价/承诺价待业务负责人。

失败/补交均保留，不能用最终PASS覆盖：

1. `d061437`首次新库安装：CSV model_id缺外部ID后缀，加载失败、tests=null；修正为当前ir.access格式。
2. `3ab7b04`安装：1 fail/5 errors/24。暴露换区flush/UoM实际API；另有测试helper空recordset布尔值误回A店、旧set_param API。修正产品与测试。
3. `85bacf1`升级：0 fail/1 error/22，reserved `_register`在registry变为bool；改为_register_walkin。
4. 后续升级22项通过，真实13组竞争通过。增加真实来源RPC绑定/未分类附件保护；补跨店HTTP转诊、普通原生复制回归并重新全新安装。
5. Firefox首次启动缺进程本地GTK路径，未关闭sandbox/安装系统依赖；复用已有本地库路径后跑通英文21项，但语言变更仍使用旧登录上下文，中文检查FAIL。测试修正为新登录后验证中文，最终重跑见上表。
6. 自建预览退出后端口仍短暂占用，runner在连接/建库前拒绝；等待该自建进程退出后正常新库安装，没有抢端口/停止既有服务。
7. 收口发现“确认演示快照”属于写动作，原price-read检查允许只读角色创建快照。最终产品限定本店price-write并隐藏只读按钮；增加真实HTTP拒绝回归，在另一全新S05库重跑安装/升级/并发/Firefox/翻译。原通过结果保留。

所有RR serialization failure是有界重试证据；deadlock未被吞掉/重试。全局锁正确性通过不等于已通过50会话性能目标。

## 用户效果验证

本次临时预览已在验证后核对PID/config并退出。复看可用上述最终库运行`scripts/s05.py serve --db DB --port 18115`，地址`http://127.0.0.1:18115/ydental/intake`及`/ydental/intake/prices`，仅S05 runner记录的新库允许；合成账号访问材料只在私有`.local/DB/access.json`，不放GitHub。演示库没有正式患者、价格或营业数据。

1. 集团主数据角色在当前店打开目录价目，新增项目、能力/单位；普通前台不能维护集团目录。
2. 本店价目角色设置服务报到/执行区，建立价格草稿，审核，再发布；冲突区间明确失败。
3. 明确选择演示策略冻结来源600快照；发布620版本，原600快照保留；缺价服务明确配置错误。
4. 前台创建患者后办两区独立预约/资格；首次到店仍未记录，任务待报到，无队列号。
5. 显式确认真实到店，再报洁牙任务；原预约余额0仍能用资格。
6. 改报种植成功后原位置撤销，洁牙任务待报到、资格保留；目标停接失败则原位置保持。
7. 仅作废位置填原因，保持资格后重新报到；另明确取消资格才按S03返额，开始后禁止返额。
8. 在目标店受理不定时转诊仅取得现场额；过期或缺额须明确重新受理，不静默延长。
9. 只读角色无写控制，HTTP伪造写也拒绝；中文重新登录后显示政策未批准提示。

对应Firefox截图与summary位于[evidence/s05/browser-attempts](evidence/s05/browser-attempts)，均为虚拟数据、无凭据可见。最终20261012T003922681586为24项PASS；实施方另人工查看换区、620版本/600历史快照、中文政策提示三张截图，内容与断言一致。页面采用基础表单，统一美化按总计划后续阶段处理。

## 审计、迁移、回滚和未交范围

本次只新增S05模块和原生保护字段，不改既有业务库，不跑生产迁移。动作receipt与S01审计同事务，失败HTTP另记denied；merge保留原号、原身份、来源和快照。无费用/库存/款项写入，无通知/门户/真实临床附件或实际打印。

生产没有部署，因此没有生产回滚动作。候选代码保留基线和独立分支；若技术复核需返工，在本阶段定向修正并保留证据。已有S05合成库保留，不drop/reset或接管历史库。真正生产升级、迁移和恢复必须另行授权，不能以卸载模块删除历史业务。

未交：真实S06叫号/排序/过号规则/工位租约/日终，真实S08发起医嘱和转诊，S09检查，S10费款，S12文书，正式价格锁价政策、患者门户/通知及S13吞吐与持续恢复。全部NOT_RUN或待责任阶段批准，不能冒称生产就绪。

仅申请GPT技术复核；写回读回#29后停止，不自动关闭、合并、发布或进入S06。
