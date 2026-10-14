# Odoo-C1-R1：S05 已发布价与 S07 建仓真实兼容回归

## 授权、版本和边界

唯一授权为 [#34 GPT-AUTHORIZE 6169607381](https://github.com/Yredxin/YDental/issues/34#issuecomment-6169607381)，承接 [独立复核 6169546255](https://github.com/Yredxin/YDental/issues/34#issuecomment-6169546255)。开工时 GitHub API 读取 #23/#29/#31/#34 正文及全部有效评论，并核对 #35 OPEN/0；本地与远端分支 `codex/s10-settlement-finance-r1-20261013` 均为 `69f76749f12ddca384465cdc2f1b759bf02d3fea`，工作树干净。Odoo20 core HEAD `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、固定 S10 test `255b48f54495eb99638af8ffc824771b9a5af3e7` 和 S07 产品文件 SHA256 `df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b` 已核对；本批均未修改。

上一 C1 的单次 shell 在合成目录准备阶段因 `bus.bus` 6→7 被夹具提前阻断。原始证据不足以把该行精确归因，仍标 `UNATTRIBUTED_PREPARATION`；旧日志、OID2100125 与 filestore 原样保留。本批只新增私有合成夹具、离线 Bus 投影契约测试及本报告和脱敏索引。夹具逐动作记录无载荷 Bus 类型、目标模型类别、调用源，另分别记录 precommit 意图、事务内 `bus.bus` 行数、postcommit 渠道意图数，以及 mail、资金和库存计数。准备阶段 Bus 非零如实记录，不单凭它判产品失败；仓库阶段 `stock_group_sync`、集团组漂移、财务/库存异常仍为硬失败。离线 `py_compile`、`git diff --check` 和 6/6 契约测试通过，后者仅是 **SIMULATED PASS**。

在新建数据库和启动 Odoo 前，强制 [预检检查点 6169781624](https://github.com/Yredxin/YDental/issues/34#issuecomment-6169781624) 已在 #34 发表并以 GitHub API GET 逐字读回。

## 实际运行

只创建一座新合成库 `ydental_odoo_c1r1_20261014134200_6d3e9f20` / OID2100126 / cluster `7694897083368259627` / port18264，源为只读核验过的纯 92 模块模板 OID2100080；124 个模板 filestore 文件逐 SHA 核对后复制至独立 data_dir。`control.py create`、`check` 均 exit0；唯一新 Odoo shell PID2782829、PG backend533676，exit0、signal11=false、日志 SHA256 `51d509aeecf34d311a0147c0b13866efe8fa9db2ff25e5c7e7f00292356bc1cc`。使用已有 Odoo20 core、独立配置、loopback-only 网络守卫与 SMTP 禁发。第二座预算库和余下三次 shell 均未使用；无安装、升级、Firefox 或完整 S10 财务测试。

每组用独立 Odoo cursor 执行真实 ORM/服务操作、负向 savepoint，最后回滚该组事务。私有 `fixture-progress.json` 记录八组结果，163 个阶段观察文件记录计数和 Bus；公开脱敏逐阶段索引见 [diagnostic.json](evidence/odoo-c1-r1/diagnostic.json)。这里的 **ODOO_PASS_ROLLBACK** 指真实 Odoo 断言在事务中通过，未将业务提交到数据库；不是 GPT 验收或生产批准。

| 场景 | 本批结果 | 实际核验 |
| --- | --- | --- |
| A 已发布 S05 价后建仓 | ODOO_PASS_ROLLBACK | 100 元版本/快照及 quote；Settings 测试用户在该事务内显式预配 multi-warehouse、multi-location；S07 建仓、主库位与药品/耗材/义齿/隔离子库位的公司和门店一致；同键/新键重复调用幂等；无仓库写权限用户被拒绝。 |
| B 同法人双店与跨法人负向 | ODOO_PASS_ROLLBACK | 同公司两店 100/120 元价源互不串用；仓库绑定目标店；无目标店授权的切店拒绝，非所属法人建店拒绝；另一法人内部用户的生效全局组状态经真实 ORM 观察。**另一法人合法建仓未执行。** |
| C 普通原生价与受管价并存 | ODOO_PASS_ROLLBACK | 合成普通 `product.pricelist` 与已发布受管价共存；建仓前后价目/rule/版本/快照摘要相等，quote 保持 100 元；直接 `sudo().write({'active': False})` 受管价被 S05 guard 拒绝。 |
| D 两组均缺、仅 location、仅 warehouse | POLICY_BLOCKED ×3 | 实际 `UserError`；仓库/config/库位及仓库动作审计增量均 0，价格摘要和 `base.group_user.implied_ids` 不变。`pricelist` 组分别覆盖 off/on/off，不能把测试配置当集团政策批准。 |
| D 两组已预配 | ODOO_PASS_ROLLBACK | `pricelist` off 情况下可建仓，价格和集团组不漂移；仓库人员拥有门店 `warehouse:write` 且无 Settings 权限时也能建仓，不会自行转换全局组。 |

所有成功场景的仓库动作产生 1 个仓库、1 个 S07 config，主库位及四类业务子库位逐对象核对；事务总 `stock.location` 增量为 13（包含 Odoo 原生附属库位）。全部场景 `account.move`、`account.payment`、`account.partial.reconcile`、`stock.move`、`mail.mail` 增量均为 0。集团 multi-warehouse、multi-location 和原生 pricelist 组在每组正式仓库动作前后相等。价格摘要覆盖受管价格、版本/快照及原生价目/rule；摘要相等是运行时断言，私有进度记录仅保存 `module_digest_stable=true`，没有逐阶段公开价格哈希。

## Bus 分阶段归因

准备阶段的合成用户/目录/价源操作可增加事务内 Bus 行，不能合并为仓库副作用。例如 A 的目录后 `bus.bus` 6→7，记录 `mail.record/insert → res.users`、来源 `mail:__init__` / `mail:_store_channel_fields`，postcommit 渠道意图 1；随后 A 仓库步骤 7→7、无新 `_sendone` 调用。B 的目录准备至 8 行，仓库步骤 8→8；C 与 D 的大部分建仓或拒绝步骤亦无新 Bus 调用。准备阶段行数的精确内部触发顺序仍不能仅凭采样完全证明，旧 C1 新行也不据此改判为特定 W1 事件。

**D 的非管理员正例是例外观察**：仓库观察点 `bus.bus` 7→8，记录一条 `mail.record/insert → res.users`，调用源为 Odoo mail；postcommit 渠道意图 1→2。该组此前创建并授权了合成仓库人员，现有阶段采样不能证明该行由仓库动作本身还是准备操作的延迟钩子造成，因此分类为 `WAREHOUSE_BUS_RECORDED`、**精确归因 UNKNOWN**，没有当作安全白名单，也没有把它冒称 `stock_group_sync`。所有建仓观察未见 `stock_group_sync` 类型；未证实实际向外发出通知，且测试 cursor 最终回滚。Bus 未解开的这一项应由 GPT 复核。

退出后独立只读 SQL 核验新库回到模板业务计数：门店、受管价、快照、S07 config、审计及原生资金/库存业务表全 0；`stock.warehouse=1`、`stock.location=12`、`bus.bus=6`、`mail.message=851`、`mail.mail=0`，其它连接 0。新库独立 filestore 比源模板多 22 个合成文件；数据库事务回滚不等于文件自动回收，全部原样保留。旧 33 座 S10 库、本次及前批 C1 库、filestore、日志、事故证据均未清理。

## 结论和未覆盖项

本批 A/B/C 及 D 合法配置的**有限应用层兼容子项有真实 Odoo PASS_ROLLBACK**；D 缺组组合为预期 **POLICY_BLOCKED**，不是产品异常。双 PostgreSQL 后端锁序竞争、并发 group cache 传播、跨法人合法建仓、外发通知投递、完整 S10 回归均 **NOT_RUN**；不能由单进程顺序测试推断通过。普通原生价目的生产归档政策和集团全局功能组启用仍 **POLICY_PENDING**。

S07 产品候选持续 **NOT_ACCEPTED**；S05×S07 总体验收由 GPT 独立复核，当前正式状态仍 **UNRESOLVED**；Native SIGSEGV 根因 **UNKNOWN**；S10 技术/生产 **BLOCKED**；S11 **NOT_STARTED**。本批不修改 Project、Issue 状态、Odoo core、S05/S07 产品、固定 S10 test，也不合并、强推或部署。
