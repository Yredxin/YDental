# S10 Native D1.8-P0：S05 价格与 S07 仓库兼容性静态审计

## 1. 授权、范围和身份

唯一授权为 [#34 GPT-AUTHORIZE 6165415202](https://github.com/Yredxin/YDental/issues/34#issuecomment-6165415202)；复核了 #23、#34 全部有效正文/评论、#29 S05、#31 S07 现行正文及技术复核，#35 OPEN 且无启用评论。原分支在审计开始时干净，HEAD `1655248248e207a944a8524196d17a9e99ace8aa`，固定 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。本批只做静态审计、离线模拟、PG 管理库身份 SELECT；没有 Odoo/GDB-Odoo/Firefox、CREATE、配置写或业务写。没有新增业务聚合 PG 查询，因此授权要求的条件式查询检查点未触发。

只读 PG 管理库身份脚本返回 `127.0.0.1:5432`、cluster `7694897083368259627`，六个固定 OID 仍在：事故 2056451、纯 92 模板 2100080、L1 2100086、三次 L2 失败 2100087/2100096/2100105。没有对这些库 SELECT 业务表，也没有修改其 filestore、volume、日志、core 或备份。原始 API 响应与本地身份输出位于权限 700 的 `.local/s10-native-20261014-6165415202-d18p0/`；公开材料只保留非敏感身份与哈希。

## 2. 产品调用链与可证明的冲突

|环节|锁定源码|已证实 / 仍待验证|
|---|---|---|
|S07 setup|`ydental_inventory/models/ydental_inventory_service.py:128-177`|门店库存写权限、幂等键、savepoint 后，以门店公司创建 `stock.warehouse`，再建业务库位、config/审计。仓库创建先于 S07 config 完成。|
|原生仓库|`../addons/stock/models/stock_warehouse.py:137-162,308-325`|创建仓库、路线/拣货类型/库位后，统计**每公司活跃仓库数的最大值**。当最大值 >1 且内部用户尚未隐含 multi-warehouse group，若 multi-location group 也未隐含，就执行 `res.config.settings(...).execute()`；随后改 group implied IDs 并发 `stock_group_sync` bus。该判据是全库最大值，单一公司第二仓库也可能使其它公司用户组受影响；是否触发设置依赖此前 group 状态。|
|原生设置|`../odoo/addons/base/models/res_config.py:347-403`、`../addons/stock/models/res_config_settings.py:103-120`、`../addons/product/models/res_config_settings.py:38-45`|execute 需管理员，调用所有已安装模块的 `set_values()`。product 配置在 `group_product_pricelist` 为假时，对 `sudo().search([])` 的**所有**价目表调用 `action_archive()`，并未按公司/门店缩小范围。stock 配置还可能改拣货类型 `move_type`；后续模块的设置/重载副作用需实际测试核对。|
|S05 受控价|`ydental_intake/models/ydental_intake_service.py:263-310,312-350`、`ydental_intake/models/native.py:40-61,81-98`|正式价服务建有公司/门店标记的原生 pricelist/rule，审核发布；quote 校对原生 rule 与审核版本，snapshot 固定取价。受管原生写入仅允许服务私有 `MUTATION` 对象上下文。原生全量 `action_archive` 写 `active=False` 穿过 native `write`，受管记录被 `_ydental_guard` 拒绝，sudo 不豁免。不能修改 guard、伪造 MUTATION 或直接 sudo 归档。|

第一轮 L2 的原始 GDB 日志 SHA `2961e7042afd54125f5c1839f411bf69dc3e60fd25a7c0de549bd10507a9e666`，真实 traceback 从 `stock.warehouse.create` 经 `_check_multiwarehouse_group`、`res.config.settings.execute`、product `set_values:45`、`action_archive` 到 YD `_ydental_guard:47` 抛 `AccessError`。**该调用发生已证实**。日志没有逐条记录当时原生普通价目表是否已被更新、group 状态的完整前后值，也不能证明所有公司/门店均实际受影响。原生写入在同一未提交事务因异常应回滚数据库记录；外发邮件、bus 已发送包、文件系统新增、外部接口及日志不由 PostgreSQL 回滚自动保证。对于 bus，仅源码证实存在发送路径；失败点在 group 更新前，不能据此称当次已发送。没有证据表明该 setup 自动过账 `account.move`、发起付款或执行 stock.move；仓库配置可能建路线、库位和拣货类型，必须以后验 SQL 审计。权限还涉及 S07 本店库存权、原生管理员设置门槛、S05 本店价格权，不能以 sudo 广泛替代。

S05 正式需求 #29 要求门店、币种、单位、版本、生效区间、审核发布与历史快照不变；S07 #31 要求每店所属法人仓库、原生库存移动、跨店/公司权限隔离。因此跨模块兼容的产品验收目标是：**新增仓库不能静默改变任何已发布价源、已确认费用或历史快照**。现状 `UNRESOLVED`；仓库优先的私有夹具顺序不能证明事后新增仓库的正式业务安全。

## 3. 未来正式产品测试矩阵（本批未执行）

通用准备：仅未来另获产品级授权后，在全新隔离合成库用真实 Odoo 服务 API；对原生 pricelist/rule、YD 价版本/快照/fee、group、settings、仓库/库位/路线、审计、mail/bus、stock.move、account.move/payment 分别做前后逐行签名与可见页面核验。失败测试应在独立事务证明数据库回滚，另审文件/外发。正常场景不应生成资金、posted 会计凭证或治疗库存移动。每项含合法管理员正例及无库存权/跨店/跨公司/旧页面 RPC 负例；不得读写真实业务资料。

|场景|具体初始化与操作|PASS 判据 / FAIL 证据|
|---|---|---|
|A：已发布价后新增仓库|同公司 A 店有正式 S05 catalog、review/publish 的价、100 元合成快照与已确认费；授权仓管在另一新店执行 S07 `setup`。记录 multi-location、multi-warehouse、pricelist group 起值。|可合法完成且旧价版本、原生受管 pricelist/rule、快照、confirmed fee 逐行相同，quote 仍取原价；新增仓库/库位/审计有来源。若产品仍抛 guard AccessError 或静默归档、改价，即 FAIL；失败后无半仓库、资金/posted账仍 0。UI 应显示明确成功或可解释拒绝，不可显示半成品。|
|B：同法人双店受管价|公司 C 下 A/B 店分别有不同受管价、版本及快照；在 B 新增仓库，用 A 店权限和无权账号做负向。|A/B 价目及快照均不变，A 不因 B 操作被归档；B 只新增本店库存配置，跨店写/RPC 拒绝。对 `sudo().search([])` 的全量作用域和 `stock_group_sync` 作精确审计。任何 A 价变更、越权或跨店库存事实即 FAIL。|
|C：普通与受管价共存|公司 C 有普通原生 pricelist 及 A/B 受管价，明确各 active 初值，再新增仓库。|普通原生价的期望生命周期需产品政策先定：若多仓库设置不应禁用 pricelist group，则所有价保持；若原生设置被明确授权禁用，则须解释普通价处理，但受管价、历史价源仍绝不可静默变化。普通价是否允许归档必须写入产品验收合同，不能用本批推论代替批准。|
|D：group 状态交叉|四种受控组合：multi-warehouse 隐含开/关 × product pricelist group 开/关，且记录 multi-location 起值；逐组从一仓库增至同公司第二仓库。|每组明确是否调用 settings.execute、是否允许由管理员先启用功能、最终 group 和受控价格结果；关价目功能但已存在受管价的组合必须明确 fail-closed 或合法迁移方案。各组做权限负向和事务回滚；全公司 group 副作用可解释，无暗中改价、无 posted 账。|

## 4. 候选解决方向；均未获实施授权

**A：原生生命周期预配置。** 先由有权管理员通过 Odoo 支持的配置路径启用 multi-location/multi-warehouse 及 pricelist group，再通过 S05 正式服务建受管价；事后增仓不得让 settings 默认值关闭价目功能。优点是尽量复用原生设置；缺点是 group 为全库用户权限效果，既有库如何迁移、跨公司影响、邮件/bus/参数、stock picking policy 都须精确审计。不能把“诊断时仓库先于价格”作为正式修复；未来需 #29/#31 跨模块产品级授权、隔离库正反测试和可回滚迁移。不得改历史快照或已确认费/原生凭证。数据库事务可回滚，已外发消息需单独补偿计划。

**B：在 YD 受控库存集成中分离无关设置副作用。** 评估可否在不改 Odoo core、不放宽 S05 guard 的前提下，使用受支持的原生 group 生命周期接口，仅配置新增仓库所必需的 multi-location/group，避免对 `res.config.settings` 非相关字段执行默认值覆盖；任何价目变更必须经 S05 正式服务和授权。必须验证原生仓库内部再次调用 `_check_multiwarehouse_group` 时不会重新触发全局 settings，避免依赖伪造 mutation context 或 sudo 归档。优点是对已发布价的扰动范围较小；风险是与原生 group 自动同步、升级及跨公司权限冲突，测试成本高。需要 #29/#31/S10 的明确产品变更授权和全回归。失败回滚 group/仓库/价源数据库写入，bus/邮件/文件另审。**当前尚无已证明安全的实现**，所以产品兼容仍 `UNRESOLVED/BLOCKED`。

## 5. 三次 L2 失败与诊断夹具契约

|轮次|真实失败与证据|正确解释|
|---|---|---|
|L2，OID2100087|已发布 S05 受管价后 S07 setup 触发上述原生全局归档，被 guard 拒绝；GDB 日志 SHA 见第 2 节。|真实产品集成兼容风险；事务未形成已提交 L2。|
|R1，OID2100096|仓库先于价格越过第一阻断，但 `_settings` 读取空 heartbeat/timeout，要求显式 `1 <= heartbeat < timeout <= 86400`；原日志 SHA `7003652da2b2cd9aecd14c0ed3298423638bcf125897fdd30bf170d1f30b9071`。|合成夹具遗漏队列配置；不修改产品默认值。|
|R2-F，OID2100105|私有夹具用 `mail.message` 全库绝对数 `>100` 拒绝。纯92模板原本 **851**，回滚后新库仍 **851**，`mail.mail=0`；日志 SHA `f16dc1d22971bd14e2cc48f4e84378cacb2a1cc36a678775f49614ce4bd30555`。|夹具误把模板基线当本批增量；失败在 commit 前，不能声称业务结果已提交。与真实外发邮件无等价关系。|

以后若另获授权，应在同一自有事务 cursor 内保存模板基线的**记录 ID 集与非敏感归属摘要**，对新消息、`mail.mail` 队列、`ir.attachment` 分别做增量/来源核查；绝对阈值 100 或无限放大阈值均错误。`mail.message` 是内部消息，新增需按模型、subtype、来源关联逐项白名单；`mail.mail` 是待发队列，应为零且另核 SMTP/外发 guard。提交前暂存对象计入本事务观察；异常回滚后用独立只读连接证明数据库记录回到基线。`ir.attachment` 行与 filestore 文件分别比对：基线逐 SHA，不删 851 条或旧附件；新文件记录相对路径类型、大小、mtime、SHA、MIME、SHA1 扇出、附件引用。原生无图内部用户可生成 avatar SVG，附件 `_file_write` 可留下零字节 GC checklist；前两旧库 6+6 文件及 R2-F 4 个文件已有逐 SHA 分类，但**无引用不自动等于泄露，也不自动等于无害**。已知头像候选需与 Odoo20 模板完整字节及合成账号来源对照，未知文件直接 STOP，保留现场。离线 `scripts/s10_native_d18_p0_contract.py` 仅演示 ID 增量/文件分类，不能替代 ORM、真实 PG 或外发审计；`run_fixture` 永久拒绝执行。

## 6. Native 独立风险及再申请门槛

原 PID2383730 为真实 signal11；只有 Python faulthandler 最后可见帧，没有当时完整 Native C 栈、core、动态 maps。CPython 完整 debug_info 与部分扩展符号不足；纯模块/L1 有界并发未复现，三次 L2 均在准备阶段失败，**未执行双 GDB L2**。因此 Native 根因 `UNKNOWN`，本批没有稳定性 PASS。未来有意义的有界申请至少需先有正式可构造且已验收的安全合成前置状态、真正 signal11 时全线程 C 栈/共享库 Build ID/maps 的 GDB 能力、独立 OS/PG PID、同一 registry 初始化窗口重叠证据、独立只读 PG 观察、资源上限及第一次异常即 STOP。若不能使实验可证伪，不应再重复建 L2 库等待偶发崩溃。

## 7. 离线验证、失败记录和停止

执行 `../.venv/bin/python -m py_compile scripts/s10_native_d18_p0_contract.py scripts/s10_native_d18_p0_contract_test.py` exit0；首轮 `../.venv/bin/python scripts/s10_native_d18_p0_contract_test.py` exit1，仅 AST 测试漏识别 `ImportFrom`，已仅修测试并保留此失败；再执行同命令 exit0、6/6 `SIMULATED`。补充 Mock cursor 快照及锁定源码 AST 调用边断言后再次运行 exit0、8/8 `SIMULATED`。私有 `identity.py` 对 postgres 管理库只读 OID/cluster SELECT exit0，未查询业务/消息聚合。所有实际命令及退出码由同名机器索引列出。未进行任何产品行为修改或运行时 Odoo 验证。

固定 S10 product/test、Odoo20 core、历史数据库、filestore、日志、卷均保留；Project mutation 0，#34 不关闭，#35/S11 未启动，未合并/强推/部署。**S05×S07 产品兼容 UNRESOLVED；S10 技术和生产持续 BLOCKED；Native 根因 UNKNOWN。**
