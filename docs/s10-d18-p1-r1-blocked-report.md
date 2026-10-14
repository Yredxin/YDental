# S10 D1.8-P1-R1 单库诊断：安全停止

## 授权和身份

- 唯一授权：[GitHub #34 评论 6166455763](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166455763)。事前检查点：[评论 6166745140](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166745140)，在 CREATE 前发表，GET 逐字读回一致。
- 起点及当时远端 HEAD：`ec9b3b4be8bd6b6892e58e85c4da79bce27e4370`；Odoo20 core：`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。S07 候选文件 SHA256：`633da04a93a4ba4f9d28dd748838833558b7f3b45c22d3ac5090d9baaddc8807`，本批字节未变，仍 **NOT_ACCEPTED**。
- 历史事故 OID2056451、纯92模块模板 OID2100080、L1 OID2100086、失败库 OID2100087/2100096/2100105/2100114 均只读核对。PG 127.0.0.1:5432，cluster `7694897083368259627`。#35 OPEN/未启用。

## 事前证据和执行额度

旧 P1 的复合断言同时判断 `mail.mail`、`bus.bus`、`account.payment`、`account.partial.reconcile`，失败前没有逐项事务内快照；触发者仍 **UNKNOWN**。本次私有新观测器在每一动作后的断言前，以 O_EXCL/600 写入四项独立计数、bus precommit 意图、组状态和文件差异，flush、fsync 并读回。旧原件保留；没有修改产品代码。

离线 `py_compile`、AST 边界检查均 exit0。12 项 Mock/FakeEnv 正负测试最终 exit0，仅 **SIMULATED**；最初 unittest 模块路径命令 exit1、两项离线测试夹具修正前 exit1，均非真实 Odoo 结果。私有控制器只读 `check_base(False)` exit0。模板重核：92 installed，所查业务表空，70 系统附件、124 个已核 SHA 的安装文件，`mail.message=851`、`bus.bus=6`、外部连接0。

预算实耗：CREATE **1/1**；Odoo 目标 **1/1**；Firefox **0**；模块安装/升级 **0**；业务事务 commit **0**。首次错误的 GitHub 评论 POST 使用纯文本而非 JSON，HTTP400、没有创建评论；改为 JSON POST exit0，GET 逐字读回 exit0。没有把该网络/命令错误计入数据库或 Odoo 重试。

## 唯一数据库和真实失败

在检查点读回后，唯一 `CREATE DATABASE WITH TEMPLATE` exit0：`ydental_s10_test_20261014105200_6bc8a41f`，新 OID **2100123**，端口18261。独立 `check` exit0：92模块、空业务表、OID/cluster、严格 dbfilter、独立 data_dir/filestore、loopback/禁 SMTP/cron0 和124文件一致。config SHA256 `44b717be2945b43492a63c4b1d8cb108aff13542b03a8bd07967772a4b2fc05e`；marker SHA256 `a978533ad037a83a800d247d340151bfc980023a1d236003c0640139d7bdac65`。

唯一 GDB 父 PID **2683604**，Odoo OS PID **2683611**，PG backend PID **497372**；GDB/目标 exit1，真实 signal11 **未见**，日志 SHA256 `607dca2b67288c23a57177ebaa08177fe930410bf1b4ba113b7c530c614a5a62`。首个 A 场景在合成 Settings 用户创建后的 `after_settings_user_create` 检查中因 `Unexplained bus intent` 安全停止。仓库 setup 尚未调用；A/B/C/D 兼容性均 **NOT_RUN**，不能据此评价 S07 产品候选。

| 事务内阶段 | mail.mail | bus.bus 行 | account.payment | account.partial.reconcile | mail.message | bus precommit 意图 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| BASELINE | 0 | 6 | 0 | 0 | 851 | 0 |
| 门店创建后 | 0 | 6 | 0 | 0 | 851 | 0 |
| Settings 用户创建后、断言前已 fsync | 0 | 6 | 0 | 0 | 853 | 1 条，目标为本批合成 Settings 用户，类型经脱敏仍未解释 |

这证明四项**已保存的事务内计数**在该早期阶段没有增加；不证明旧 P1 的失败触发项，也不证明后续仓库动作安全。`mail.message` 的两个事务内新增来源模型为 `res.partner` 和 `res.users`，与 `mail.mail` 发信队列不同。bus 意图尚不是已提交 `bus.bus` 行，也未证明 postcommit NOTIFY；未知类型按预设规则阻断。此时 base.group_user 的 multi-warehouse/multi-location/pricelist 布尔状态均为 false；并未测试候选的全局组变更。

## 退出后独立只读保全

新库回滚后：92 installed、门店/价格/快照/S07配置/治疗费/stock.move/account.move/payment/partial/mail.mail/访问审计均0，`mail.message=851`、`bus.bus=6`、`ir.attachment=70`。原生仓库1、库位12、路线4，与安装模板基线一致。base.group_user implied_ids 共4项，源/新库排序ID SHA256 同为 `982aab7716015636e1a458975ffaae4126c4c07912cf13cc99cb35ab802b3351`。历史 OID 不变；源 filestore 的124文件逐 SHA 保持相同。

新 filestore 在合成用户创建时出现2个回滚后未引用文件：一个305字节 SVG，一个0字节空文件；两者在新库 `ir.attachment` 引用数0。时间和动作关联已观察到；具体原生生成链仍 **UNKNOWN**，仅可推测头像/缓存或清理标记。原件按700/600私有证据保留，不删除、不公开内容，也不称安全无害。无法据本次证明有无事务外通知；未见已提交邮件队列。历史库、卷、日志、core、备份均未修改或清理。

## 结论和后续复核问题

- 安全观测器按约束在未知内部 bus 意图处停止；A/B/C/D 全部 NOT_RUN，S05×S07 兼容性 **UNRESOLVED**，当前 S07 候选 **NOT_ACCEPTED**。全局集团权限政策仍需正式决定。
- 只有在审清用户创建的 bus 意图具体 Odoo 源码路径、事务范围和这两个未引用文件的来源，并对更新后的诊断契约重新授权之后，才值得申请新的单库产品试验；本批没有新额度。
- 原 PID2383730 的 Native SIGSEGV 根因仍 **UNKNOWN**。本批无 signal11 不等于修复。S10 技术与生产持续 **BLOCKED**；Project 零修改，#34未关闭，S11未启动，无合并、强推或部署。

私有原始目录：`.local/s10-d18p1r1-20261014-6166455763/`、`.local/ydental_s10_test_20261014105200_6bc8a41f/`（权限700/600）。脱敏机器索引：`docs/evidence/s10-d18-p1-r1/diagnostic.json`。原日志、配置、用户数据、观察 JSON 和文件内容均不上传。
