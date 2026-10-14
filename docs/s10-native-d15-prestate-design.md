# S10 Native D1.5-0：事故前置状态只读取证与最小实验设计

## 1. 任务、身份和结论

本批唯一授权为[#34 GPT-REVIEW/AUTHORIZE 6161244580](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161244580)，只做静态/只读分析。开工前用GitHub API取得#23/#34当前正文与全部有效评论（3/35）、逐字读取授权，#35 OPEN/0评论；`origin=Yredxin/YDental`、原分支与远端起点`d4efed555e9df001951f171d585a815a86d2ed5e`、起始工作树干净。固定product`4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test`255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`不改。Ubuntu venv CPython3.12.15；专用`127.0.0.1:5432`/PG cluster`7694897083368259627`，`odoo20-db`与独立`odoo12-db`仍在。

**研究结论：**原事故前的业务状态确有大量已提交事实，且最后bill夹具本身产生了一个confirmed fee和一条原生库存耗用，却没有对该fee出账。原PID2383730在Odoo shell载入registry后的`res.users.context_get`阶段SIGSEGV，发生在它执行stdin中的helper import、barrier及`bill`之前；PID2383729的SIGINT是守卫响应。不能将`bill`业务动作认作崩溃原因，也不能以D1.4-R1纯92模块未复现宣称Native问题修复。建议**仅申请未来独立授权的L1单变量窗口**，先隔离用户/门店/会话/权限状态；本批无执行额度。S10技术与生产持续BLOCKED，根因UNKNOWN。

## 2. 原事故时序及能证明的状态

原库`ydental_s10_test_20261014020300_8b6c1d4e`/OID2056451/port18247，configSHA`34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、markerSHA`96d261798a4b4370772d5700ba8516dd7677d2568f2b3fda80d3572b94a644e6`。另外四库OID2078375/2100078/2100079/2100080均由独立只读管理库查询保持原身份。事故`actions.jsonl` SHA`d6a578b75fd9ba331372e8616bf7a18999694649ffe65f3e1002660bcf0800cf`、`race-actions.jsonl` SHA`380aa68c226a8fd2b4b904706d6856638c6bc9c0303a11c274a9909a3fb20ff0`。在任何事故库新增聚合前，先发布并API逐字读回[预检检查点6161294008](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161294008)，正文SHA`48e16752eff3f18d5a8c38b77588741d343bd80f12fa333ed092d5a788e679fa`。

|UTC和顺序|命令/事务结果|对崩溃前状态的意义|
|---|---|---|
|02:04:15 / 动作1；02:04:26 / 动作2|S10安装PID2380553、首次升级PID2381168均exit0|事故库安装92模块，后续26个shell逐个启动。|
|动作3—24，02:04:50—02:07:52|F1、F5、跨日退款、55条分页、跨法人、S09回归与PDF等22个shell均exit0|这些合成事务按原runner独立提交；完整名称/PID/命令哈希见机器索引。|
|动作25—26，02:08:04—02:08:05|`finance_race_prepare`与`approval_race_prepare`均exit0|独立并发夹具先于bill夹具存在。|
|动作27：02:08:07.218 registry完成，02:08:16.674包装完成|`concurrency_prepare.py` PID2383521 exit0；`S10_CONCURRENCY_READY`在日志；`concurrency-fixture.json` mtime 02:08:16.317，SHA`dc51cd57f2c1793a8b0cebcc977fd3f24c67a086e345f4f7fccc254e9f10c62f`|脚本在自有cursor内`cr.commit()`；exit0加实际fee/event/stock关系聚合证明其业务前置提交，而非仅文件打印。|
|动作28：02:08:17.977 registry完成，02:08:18.406包装完成|`refund_race_prepare.py` PID2383625 exit0；又生成2个S01会话|这是两个actor前**最后一个**prepare，但bill所需最后prepare是动作27。|
|02:08:24.934—02:08:26.154|bill双shell启动；A/B registry分别02:08:25.341—26.116与02:08:25.340—26.114；A于26.154写PG barrier|A进入stdin脚本，B没有barrier文件；不能把A进度归给B。|
|02:08:26后|B PID2383730 SIGSEGV/exit-11；A PID2383729由守卫SIGINT/exit-2|B原日志SHA`f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、crash markerSHA`d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78`；Python最后可见栈在`field_computed→res.users.context_get→shell`，**没有C栈**。|

本批对37张必要表只查schema、总数、`create_date/write_date`时间聚合，均存在`create_date`；以B启动02:08:24.934为截点，37张表的全部现存行`create_date`均不晚于截点，`write_date`晚于截点计数0。这与28个前置动作exit0和事故后停止Odoo相互印证，但`create_date`是当前行元数据，**不是事故时的WAL快照或每行事务提交证明**。不把事故库最终行数单独当作崩溃瞬间事实。

当前快照相关总数：226治疗事件/225费源、236库存事件/238原生`stock.move`、17结算source、66收款/66退款/63日结、93 posted `account.move`、70 `account.payment`、73原生partial；10患者、103用户、176会话。这些属于**整个此前顺序执行状态**，不是bill夹具自身的增量。第27动作独占时间窗的新增聚合为2门店、9用户、11会话、30授权、1患者、1临床文书/版本、1队列执行、1治疗事件、1confirmed fee、1耗用、2库存事件及2原生stock.move；另8原生科目、4日记账、1结算配置，**没有新增`account.move/account.payment/partial`**。第28动作窗只新增2会话。按`concurrency-fixture.json`内部ID做**仅聚合**的关系核查：fee1→event1为confirmed、在actor启动前创建、尚无结算source；耗用1→S07事件1→done原生move1。这是bill目标可用的证据，不代表已执行bill。

## 3. 实际调用链、权限及副作用

固定源码SHA：`scripts/s10_r3_runner.py`=`f47dbf0c9b9bc76590d16cc8a862b3cac74a0485ea1789facb560dc10394a719`、`scripts/s10_r3_race.py`=`3f7d83ac78553af8fbfaf840526215d19ac6737b1d4693a4a95e386e121b3578`、prepare=`441befdfb841644c65517af6a60ea3084fbcea9e983dfd8a1e0307edf561c9aa`、actor=`b6093bca1ea3031a2550787f04e6c4972cc01a102d5b94a1d3c0d1a7d4168fbe`。`common.py`=`fd7fe3ee0543cb434381cc31ea312c0bf8cceb06dfc8d9932ff31720888a0d1d`、`treatment_common.py`=`ac4d5568a13358103f1bafbb712f32142fe16c9d2a4e5c494dbe8c3854d634ea`。

|调用与源码|真实服务、权限、前置|数据库/外部副作用及幂等|
|---|---|---|
|`setup(f)` [prepare:9—11](../scripts/s10_completion/concurrency_prepare.py#L9) → [treatment_common:9—42](../ydental_treatment_test/tests/treatment_common.py#L9) → [common:20—100](../ydental_treatment_test/tests/common.py#L20)|`base.sudo()`合成bootstrap；S01 `ydental.access.service`经内部session加入/授予门店权限；S05 `ydental.intake.service`建catalog/mapping；S03 `ydental.supply.service`建policy、营业、slot/publish；S07 `ydental.inventory.service`建仓库、两个产品与批次。至少manager/frontdesk/doctor/price/warehouse，药房后续权也配置。|两门店、9用户、4能力及授权/会话、空间和供给记录、1原生仓库/库位、7原生产品模板/变体、2lot；`ir.config_parameter`队列超时也会更改。各`_operate`有独立随机key和审计receipt；此时无真实收款/退款/posted凭证或库存move。新建测试用户可能有mail/bus副作用，未来必须限制外发。|
|S10财务演示配置 [prepare:12—24](../scripts/s10_completion/concurrency_prepare.py#L12)|manager取得`settlement:write`；同法人、演示策略，找income/sale/general journal。|创建`account.account`、4手工银行型journal与payment-method-line映射、`ydental.settlement.config`；窗口实际8 account账户/4 journal新增（包括原生间接创建），**无posted会计、无款**。不可把演示支付称银行接口。|
|`receive(f)` [prepare:25](../scripts/s10_completion/concurrency_prepare.py#L25) → [treatment_common:45—47](../ydental_treatment_test/tests/treatment_common.py#L45) → [inventory service:322—326](../ydental_inventory/models/ydental_inventory_service.py#L322)|manager门店`warehouse:write`、真实store库存config/product/未过期lot；`source_key`与操作key分别随机。|20份material真实入库：`ydental.inventory.event`、原生`stock.move/line/quant` done；`_event`按store/namespace/source_key去重，[native move:280—309](../ydental_inventory/models/ydental_inventory_service.py#L280)。无fee/posted账。|
|`price(f,100)` [prepare:25](../scripts/s10_completion/concurrency_prepare.py#L25) → [common:134—151](../ydental_treatment_test/tests/common.py#L134) → [intake price:263—310](../ydental_intake/models/ydental_intake_service.py#L263)|manager价目写权、catalog/公司币种；明确演示有效期，创建→review→publish。|1 S05 price、原生`product.pricelist/item`，价目审计；无库存、fee或posted账。100是**脚本传入价格**，本批没有读取目标fee的金额字段。|
|`opened_actual(f)` [prepare:26](../scripts/s10_completion/concurrency_prepare.py#L26) → [treatment_common:50—55](../ydental_treatment_test/tests/treatment_common.py#L50) → [common:168—194](../ydental_treatment_test/tests/common.py#L168)|frontdesk创建合成患者/预约/到店/报到，需已发布能力/slot；doctor合格工位enter→call→start，临床`open→save`，持有S06 lease/token。|1患者、claim/task/queue entry/execution/lease、1临床文书与版本及审计/receipt；无原生库存move或fee，`save`不等于收费。|
|`execute_args`与`execute` [prepare:27](../scripts/s10_completion/concurrency_prepare.py#L27) → [treatment_common:58—62](../ydental_treatment_test/tests/treatment_common.py#L58) → [treatment service:64—102,285—347,365—439](../ydental_treatment/models/ydental_treatment_service.py#L64)|doctor`medical:write`，活动lease/文书版本、已发布100价、material lot可用；`already_performed=False`、单项qty1、真实材料qty1，演示确认策略。|`ydental.treatment.event`/consumption/冻结价格快照/confirmed fee各1，S07 `inventory.event`和原生stock.move再1；来源`ydental_source`及操作key分别去重，fee以event唯一；**不创建结算source、invoice/payment/partial**。无可用库存或价格则预期拒绝/回滚，不能伪造费库。|
|夹具落盘与提交 [prepare:29—31](../scripts/s10_completion/concurrency_prepare.py#L29)|自有`env.registry.cursor()`，完整过程在一次cursor事务中。|先写私有`concurrency-fixture.json`再`cr.commit()`；故文件独存不能证明提交，需exit0/SQL联证。失败应回滚自有事务、保留现场并STOP，不原库重试。|
|actor [race:37—67](../scripts/s10_r3_race.py#L37) → [actor:8—49](../scripts/s10_completion/concurrency_actor.py#L8)|两Odoo shell独立OS/PG后端；若执行，读取fixture、barrier后以manager会话调用`ydental.settlement.service._operate('bill')`并显式commit。|**B在shell默认上下文加载时已崩溃，未运行该stdin脚本；未来Native窗口只读canary，不调用bill、退款或库存。**|

`from odoo.addons.ydental_treatment_test.tests... import`只是Python源码导入；事故库只读`ir_module_module`证实`ydental_treatment_test=uninstalled`、`ydental_settlement_test=installed`。前者原`pre_init_hook`仅容许受保护S08B/S08C/S09命名和marker，不能因为Python import成功便在S10新库安装它，不能改hook或伪装旧库。直接导入测试包可能使Python载入包代码，但事故B在stdin执行前崩溃，因此**该次B的helper import不曾执行**。原S10网络保护是process-local `sitecustomize.py`仅放行loopback PG和专属HTTP端口，配置SMTP指向loopback无服务、cron0；可能的非Python原生外发途径仍须独立隔离，不宣称全系统网络证明。

## 4. L0—L3可证伪夹具矩阵（全部为未来建议）

|层级/与事故关系|模型、数量和调用顺序|合法事实与副作用|未来新库与Odoo目标预算建议|可证伪结果及停止|
|---|---|---|---|---|
|**L0 已完成**：仅92模块registry，零业务|D1.4-R1纯92库OID2100080；无用户/临床/资金新数据。|无posted账、无stock.move。|原批安装1+GDB只读shell2已耗尽；**本批0**。不复用它做新写实验。|0.792秒重叠和有效PG观察下无崩溃，只削弱“纯92模块并发必然崩溃”假设，不证明稳定。|
|**L1 推荐下一次唯一层级**：隔离S01用户/会话/门店状态|另一全新库，未来先重新审计纯92来源；1公司（原生已有）、**1新门店/1合成manager/1员工关系/1授权会话/2授权类别**。只按[草案](../scripts/s10_native_d15_l1_draft.py)使用`ydental.access.store.create`、Odoo20 `new_test_user`、S01 `_session_for_key/_join/_grant`，固定随机源和单次提交；若要测试数量效应，须另行授权，而非本窗口逐渐加人。|仅S01审计/员工与可能Odoo mail内部记录；**0患者/fee/stock.move/posted账/资金**。loopback/禁SMTP/独立filestore和guard必须先有效。|新库1座；若从经新审计的纯92源受控克隆，准备shell **1** +独立GDB只读shell **2** = Odoo目标3；若从空库安装还需额外安装目标1，单独授权。|若真实SIGSEGV及C栈出现，L1状态在该受控环境足以伴随崩溃；若无崩溃，只记本层未复现，不能排除偶发或更复杂状态。任何准备失败/身份错/signal11即STOP并保留库。|
|**L2 条件候选，另行授权**：最小confirmed fee图|**另一座**全新库，从纯92态依次1店、必要manager/frontdesk/doctor及权限、1能力/catalog/价/营业slot/工位、1合成患者/资格/queue执行/文书、1 material产品lot、1真实入库、1真实治疗耗用、1confirmed fee。通过S01/S03/S05/S06/S07/S08真实ORM服务API，确定性key；不直接SQL塞临床事实，不安装`ydental_treatment_test`。原prepare的药房空间、第二门店及S10演示财务journal先剔除并记录差异。|预期1 S07 receipt move+1 issue move、1event/1fee；**0 posted invoice/payment/refund/close**。若某服务因缺财务配置而阻断，STOP记录缺口，不在窗口中临时扩大夹具。|与L1不同新库1座；经批准克隆纯92则准备shell **1**+GDB只读shell **2**；空库安装另计1。不能从L1库复制/原事故库克隆。|L1正常而L2真实崩溃可提高临床/库存/费图相关性，但不能单凭一次定位具体对象；两者都正常仍UNKNOWN。所有实际stock.move和price源须SQL勾稽后再进入捕获。|
|**L3 仅风险评估，不执行**：接近原事故全量|原26个顺序业务shell导致10患者/103用户/226event/225fee、数十退款日结和原生posted账库存。须重新逐项授权、脱敏、定义数据上限。|大量真实合成posted财务、付款/退款/日结、跨法人库存，风险明显高于Native读探针。|只能另建全新库；若完整重放，至少26个准备Odoo目标+安装/升级另计+2个GDB目标，**本轮和下一最小建议均不批准**。|即便复现也高度混杂，必须有C栈及逐层控制才能归因；任何前置异常STOP、保留原库不删除、不随机重跑。|

所有未来层级均须唯一新库名/OID/PG cluster、专属port/configSHA/marker/core、dbfilter/data_dir/filestore、独立安全附件核对和无真实患者/资金；只允许与授权数据库通信，角色和公司由真实服务校验。失败时停止自有进程、回滚未提交事务、保留新库/日志/filestore及旧现场，不DROP/改名/覆盖。

## 5. 未来最小实验与三个以内假设

1. **H1 用户/门店/会话状态足以影响shell上下文加载。** L1单一新增授权图与L0相比只改变该类持久状态；若GDB抓到同类型真实C栈，则支持H1；无崩溃只构成一次反例，不能证明不可能。旧库的103用户/176会话数量效应仍UNKNOWN，L1不模仿规模。
2. **H2 最小临床/库存/confirmed fee图影响registry后的Python/native对象生命周期。** 仅在独立批准的L2与L1比较；真实SIGSEGV及完整C栈可支持，正常退出不能排除偶发。原账款/退款/日结不是L2必要条件。
3. **H3 原事故需更广的已提交业务规模、特定Native扩展或偶发资源时序。** L0/L1/L2若都未复现，H3仍未证实；只能由新的分层设计与真实C栈区分，不能将未知当修复。

推荐下次**只授权L1一个窗口**：先新库保护和单一准备目标（最好GDB父捕获），准备exit0并做只读SQL状态/空业务表核对后，另一个窗口两个独立GDB父各带一只读`shell -c <new-config> --no-http`，**总建议Odoo目标1+2=3**（若空库安装另计1，必须明列授权）。沿D1.4-R1已验证的PG白名单观察器逐样新快照，记录两个OS PID、两个PG backend PID、唯一application_name、registry起止与是否重叠、GDB真实signal11而非设置文本、全部线程C栈/sharedlibrary及ELF Build ID、退出码/timeout/私有日志SHA。shell canary仅查询registry/模型/PG PID，**业务动作起点永不进入**。准备失败、任何signal11、无重叠、监测无效或资源阈值触发即STOP/INCONCLUSIVE，不追加目标。L1无崩溃只记一次有限窗口未复现；绝不自动进入L2/L3。

本批新增[受控L1源码草案](../scripts/s10_native_d15_l1_draft.py)有`FUTURE_AUTH_COMMENT_ID=None`硬闸门、直接执行始终拒绝；现阶段仅离线编译/AST/mock。未来若授权还须把正式评论ID、全新数据库marker/OID/cluster/core/configSHA、纯92来源、安全filestore、严格`PYTHONPATH`网络guard、禁SMTP、模块installed和私有权限逐项核实，且对`new_test_user`的非业务mail副作用单独审计。草案的`prepare_l1`在未批准闸门之后才出现ORM create，按marker中唯一`fixture_key`建确定性名称并先查重，使用自有cursor一次commit；随机密码不打印，失败不重试。其模拟通过**不表示夹具运行成功**。

## 6. 本批真实检查、失败史及UNKNOWN

只读命令包括`gh api`现行Issue/评论、`git`/core/venv/Docker身份、事故marker/actions/日志SHA、独立管理库OID/cluster SELECT、事故库只读37表count/time聚合及18相关表窗口计数、fixture源关系count、源码`rg/nl/sha256sum`，均exit0。37表全部现存行的`create_date`早于actor起点且`write_date`晚于起点0；原日志与marker哈希匹配。实际命令范围与退出码：

|执行命令（私有路径与参数已脱敏）|退出码|
|---|---:|
|`gh api`读取#23/#34/#35、分页评论、授权；`git remote/status/rev-parse/ls-remote`；core/venv/Docker身份|0|
|`../.venv/bin/python - <管理库cluster/OID SELECT>`；`../.venv/bin/python .local/s10-native-20261014-6161244580-d150/read_aggregate.py`|0/0|
|`../.venv/bin/python - <状态、fixture关系及prepare时间窗只读SQL>`；`sha256sum`/`rg`/`nl`|0|
|`gh api --method POST`预检评论、`gh api`评论逐字读回|0/0|
|`../.venv/bin/python -m py_compile -o <private pyc> scripts/s10_native_d15_l1_draft.py`|**2**|
|`../.venv/bin/python - <py_compile.compile(cfile=..., doraise=True)>`；`../.venv/bin/python <private offline_draft_check.py>`|0/0，后者仅SIMULATED|
|`python3 -m json.tool <machine index>`；`git diff --check`|0/0|

私有聚合SHA和逐命令索引见[机器证据](evidence/s10-native-d15/analysis.json)。

L1草案`py_compile`首次使用不支持的`python -m py_compile -o`，**exit2**，错误记录保留；按Python标准`py_compile.compile(cfile=...,doraise=True)`修正调用后exit0。AST扫描证实`prepare_l1`首个操作是guard、源码内全部直接SQL均为SELECT；fake环境合法1、负向11均为**SIMULATED**且exit0，当前真实授权硬闸门拒绝。没有Odoo import/数据库连接/ORM写入被运行。此类静态测试不证明未来Odoo20运行、网络完全隔离或Native根因。

仍UNKNOWN：原信号11的C backtrace/堆与共享库实时映射，旧S07/S08-C/S09事故是否同源，Odoo shell `context_get`触发的具体Native扩展或内存错误；第27动作每个间接ORM写的因果关系；事故时精确MVCC快照与低频复现概率；L1/L2是否足够、GDB扰动效应、非Python原生外发边界。未来正式财务科目/税/支付政策仍未批。本批绝不以任何静态/模拟项标PASS业务或Native稳定性。

## 7. 数据、审计与保全

新私有原始证据目录`.local/s10-native-20261014-6161244580-d150/`为700，文件600；事故库`.local/ydental_s10_test_20261014020300_8b6c1d4e/`原样保留。公开材料只有本报告、无个人字段的机器索引及永不在当前授权运行的安全草案；不上传配置密码、原始病历/患者、账号登录、财务原单、完整崩溃日志或core。原S00—S10数据库、五个固定OID、卷、filestore、日志和备份不删除、不覆盖；Odoo20 core/odoo-12/历史venv不修改。无数据库迁移或需回滚的数据写；如未来实验失败，保留新库作为证据而不是DROP。

## 8. 复核申请与停止

本批**新Odoo目标0、GDB-Odoo目标0、Firefox0、CREATE/克隆0、业务写0、Project mutation0**。#34/#35维持OPEN，未关闭Issue、未合并/强推、未启S11、未部署生产。请GPT独立复核事故前置证据、L1是否足以提供信息增益及未来条件；本报告**不是**D1.5执行窗口申请，不能自动批准L1、L2或恢复S10 D2。**S10全阶段BLOCKED，生产BLOCKED，Native根因UNKNOWN。**
