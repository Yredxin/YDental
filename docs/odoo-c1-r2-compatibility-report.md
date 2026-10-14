# Odoo-C1-R2：三功能组开启、跨法人合法建仓与双事务回归

## 身份和执行边界

唯一授权为 [#34 评论 6170156104](https://github.com/Yredxin/YDental/issues/34#issuecomment-6170156104)，依据 [独立复核 6170089290](https://github.com/Yredxin/YDental/issues/34#issuecomment-6170089290)。开工通过 GitHub API GET #23/#29/#31/#34 当前正文和全部 3/7/8/95 条有效评论、#35 OPEN/0；#34 当时最后有效评论即本授权。本地和远端原分支从 `f14a58b4331f921618f22a809a10d3abf5aeea35` 起步，工作树干净。Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、固定 S10 test `255b48f54495eb99638af8ffc824771b9a5af3e7`、S07 库存服务文件 SHA256 `df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b` 均不变；S05/S07 产品代码没有修改。

新 CREATE、Odoo 和业务 COMMIT 前，在 #34 发布[强制预检 6170436108](https://github.com/Yredxin/YDental/issues/34#issuecomment-6170436108)，并经 GitHub API GET 逐字读回。离线 `py_compile`、`git diff --check` 与锁分类/COMMIT 配额契约 3/3 通过；3/3 仅为 **SIMULATED PASS**。只读模板 OID2100080 有 92 安装模块，10 个受查业务表全 0、124 个 filestore 文件逐 SHA 匹配、无活动连接。

本批仅新增一座库 `ydental_odoo_c1r2_20261014140600_7a19d24e` / OID2100176 / 原 cluster `7694897083368259627` / port18266，独立 data_dir、loopback 网络守卫、SMTP 127.0.0.1:1 禁发及 cron0。`control.py create`、`check` 均 exit0。唯一 Odoo shell PID2802241、exit0、signal11=false，日志 SHA256 `d75fc55d38a3faf14fe4eddf44ad8f9c50784aa913420c7bf078db97492a1d37`。使用额度：**1/1 新库、1/3 shell、2/2 同时事务后端、2/2 有目的业务 COMMIT**。没有安装/升级、Firefox、完整 S10 财务或 Native 诊断。

## 真实 Odoo 结果

第一次 COMMIT 只持久化合成基线：真实 Settings 用户显式开启 `base.group_user` 的 multi-warehouse、multi-location、product-pricelist 三组；随后在两个合法法人门店发布各一条 S05 受管价版本和执行快照（合成报价 100/120），建立一条普通原生价目及固定 77 的规则，并配置合成用户的门店授权。新的 Odoo cursor 实际读回三组、两条已发布价/快照、普通规则、两店报价；直接原生归档受管价在 savepoint 中被 S05 guard 拒绝。第二次 COMMIT 仅持久化 A 法人普通仓库人员建立的一座 S07 仓库。B 法人合法建仓、同键幂等及跨法人负向在另一个自有 cursor 中真实执行后全部 ROLLBACK。

| 子项 | 真实结果 | 可证伪的核对 |
| --- | --- | --- |
| R2-1 三组全开后的 S05/S07 | **ODOO_PASS_COMMITTED** | 三组均 true、Settings=false 的普通仓库人员可持本店 `warehouse:write` 建 A 仓；主库位及药品/耗材/义齿/隔离库位的公司和门店正确。建仓前、未提交后、提交后新 cursor 的受管价/版本/快照及原生价目/rule 摘要同为 `bbd37ac89976acf53a8658610d3d61842fd2b088b628d5d6ae4d4411c9fecb73`；`base.group_user.implied_ids` 摘要同为 `f353d15238432e0ff603cda6838134ef72621a6fc39f2af84981db76ea99a1d3`，报价仍 100/120。A 的 `inventory.setup` S01 审计准确一条。 |
| R2-2 另一法人正例 | **ODOO_PASS_ROLLBACK** | B 公司专属普通人员有 B 店仓库写权、无 Settings 权；真实 B 仓 +1、config +1、库位 +13，库/四类业务位归 B 公司/B 店，A 仓与两店价源不变；同键重复 `already_accepted` 且无第二仓。A→B、B→A 无会员切店各被 `AccessError` 拒绝。回滚后 B 仓/config/审计均不持久。 |
| R2-3 双事务和提交读回 | **ODOO_PASS，含预期 40001 回滚** | 真实不同后端 540665/540685。A 事务完成 setup 但未提交时，B 事务开始另一店 setup；`pg_locks` 见 B 后端一条未授予的 advisory `ExclusiveLock`。A SQL 类别实际顺序为库存 advisory→mutex→`stock_warehouse` 表锁→`res_groups` 行锁。A COMMIT 后，B 在 mutex 更新时获 SQLSTATE `40001`，受控回滚；无成功的 B 并发业务写。全新 cursor 读回 A 仓、三组和两店价格一致；随后 B 的独立合法正例及回滚也经新 cursor 验证。 |

实际交错文件时间：14:15:34.149572Z A 建仓未提交；14:15:34.182605Z B 事务开始；14:15:34.237505Z 见 B 未授予 advisory 锁；14:15:34.257118Z A 第二次 COMMIT 完成；14:15:34.289312Z B 序列化回滚已记录；14:15:34.318818Z 新 cursor 读回。这些时间是私有证据文件写入时间，锁释放从 COMMIT 与 B 后续结果推断，未直接量测精确释放时刻。

**锁序证据边界**：A 实际执行了表锁再组行锁；B 在全局库存 advisory/mutex 阶段等待并因 40001 回滚，**未执行到自己的仓库表锁/组行锁**。因此两个后端同时争夺这两把后续锁的路径为 **NOT_RUN**，不能称表锁本身发生了等待，也不能由一次无死锁推断所有并发安全。未执行故意死锁或超时故障注入。真实 40001 是本次受控并发的预期事务回滚结果，未自动重试、未产生半仓库。

## Bus、mail 与审计的限定归因

本批 29 个阶段观察在[脱敏机器索引](evidence/odoo-c1-r2/diagnostic.json)中逐一保留无载荷类型、目标类别、调用源及独立计数。基线合成用户/目录准备产生内部 Odoo mail 记录，`bus.bus` 在目录阶段 6→9；两个法人实际仓库 setup 阶段均 9→9，`mail.message` 均 881→881，`mail.mail` 全程 0，各新增一条 `inventory.setup` 审计。基线 COMMIT 前有三个内部 Bus postcommit 渠道意图，COMMIT 后归零；这不是向外部收件人投递的证明。

对 R1 原私有 D 非管理员四阶段重新限定对照：`mail.message` 859→861 在人员创建、861→864 在人员授权，仓库阶段 864→864，故此前额外五条 mail.message 可定位到**准备阶段**。S01 审计 11→13 在人员授权，13→16 在仓库阶段；本批独立建仓只新增一条明确的 `inventory.setup`，R1 仓库阶段另外两条审计的具体业务原因仍 **UNKNOWN**。R1 Bus 7→8 出现在仓库观察点，`mail.record/insert → res.users` 的内部 mail 调用已记录，但精确触发仍 **UNKNOWN**；不能据本批无 Bus 就倒推旧行一定属于准备钩子，更不能称其 `stock_group_sync` 或已实际外发。

## 持久库与停止状态

Odoo 退出后另用只读 SQL 核对 OID2100176：92 模块；门店2、已发布受管价2、快照2、S07 config1、仓库2（含模板原仓1）、库位29、S01 审计31，其中 A 本店 `inventory.setup`1、B 0；`account.move`、`account.payment`、`account.partial.reconcile`、`stock.move`、`mail.mail` 均 0；`bus.bus=9`、`mail.message=881`，其它活动连接0。两条受管原生价目 active，另一个普通原生价目 active。新库独立 filestore 比模板多 6 个合成文件，原样保留；这座库的两次提交是本授权准许的合成数据，B 建仓没有持久化。旧 33 座 S10 库、C1 OID2100125、C1-R1 OID2100126 和事故/filestore 证据均未清理。

以上是 Codex 在隔离合成库中的应用层验证，需 GPT 独立复核。S07 候选仍 **NOT_ACCEPTED**，S05×S07 总体仍 **UNRESOLVED**，集团生产全局组政策 **POLICY_PENDING**，Native SIGSEGV 根因 **UNKNOWN**，S10 技术/生产 **BLOCKED**，S11 **NOT_STARTED**。本批不修改 Project/Issue 状态，不合并或部署。
