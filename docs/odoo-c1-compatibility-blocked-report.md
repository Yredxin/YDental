# Odoo-C1：S05 已发布价与 S07 建仓兼容修正，真实测试阻断

## 身份与边界

唯一授权为 [#34 评论 6169133942](https://github.com/Yredxin/YDental/issues/34#issuecomment-6169133942)，范围以 [6168962080](https://github.com/Yredxin/YDental/issues/34#issuecomment-6168962080) 为准。GitHub API 读取 #23/#29/#31/#34 正文及全部 3/7/8/87 条有效评论，#35 OPEN/0。起点本地/远端均为 `0eb9fdb880decc5b81ac65771e35c57b101e2e2d`；原工作树干净。Odoo20 core 已跟踪 HEAD `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；固定 S10 test `255b48f54495eb99638af8ffc824771b9a5af3e7` 未修改。原 S07 候选文件 SHA256 `633da04a93a4ba4f9d28dd748838833558b7f3b45c22d3ac5090d9baaddc8807`，仍 **NOT_ACCEPTED**。core 目录原有未跟踪入口未改。

事前 [预检回执 6169326455](https://github.com/Yredxin/YDental/issues/34#issuecomment-6169326455) 在 CREATE/Odoo 前发表并通过 GitHub API GET 逐字读回。没有修改 Project、Issue 状态、Odoo core、S05 guard、S10 固定测试或其它产品代码。

## 代码候选与原生调用边

仅修改 `ydental_inventory/models/ydental_inventory_service.py` 的 `_setup`，产品 SHA256 `df07e1a7eebaec424c13973bf7937bac28defb7f2e27360b3cf6efdecdd2aa2b`。在原生 `stock.warehouse.create` 前锁仓库表和 `base.group_user` 行；按全库各法人活跃仓库最大数预测原生分支。新增后最大数 >1 时，要求 Settings 管理员事先显式配置 `base.group_user.implied_ids` 的 multi-warehouse 和 multi-location 两组；缺任一组即 `configuration_required`。最大数 <=1 而 multi-warehouse 已启用时也拒绝，以免原生自动移除集团组。原先 `_setup` 内 `group_user.sudo()._apply_group(...)` 已删除。创建后再检查组未变化；旧 `_operate` savepoint、receipt 幂等及 S01 审计边界保留。

锁定源码显示：原生 `stock.warehouse.create` 最后调用 `_check_multiwarehouse_group`；缺 multi-location 时可能调用 `res.config.settings.execute`，进而触发 product `set_values` 对全部原生价目表归档。S05 `_ydental_guard` 应继续拒绝受管价原生写。本候选以预配置阻断该广域 settings 路径，不把隔离测试中的组配置视为生产政策批准。未取得真实 Odoo 正例，故代码仍是 **待复核候选**。

## 实际验证与停止点

`py_compile`（产品、测试和私有运行夹具）exit0；新增真实 `_setup` AST Mock 六项 **6/6 SIMULATED** exit0，覆盖缺两组/缺 location/合法预配置/他法人现有双仓/原生组漂移/首仓误移除。`git diff --check` exit0。这些不代表 Odoo PASS。

唯一新库 `ydental_odoo_c1_20261014132000_a84d2c91`，OID `2100125`，cluster `7694897083368259627`，端口 `18263`，从无活动连接、124 文件逐 SHA 匹配的纯合成模板 `ydental_s10_test_20261014044700_4f6a8d2c` / OID `2100080` 克隆。`control.py create` exit0、`check` exit0。仅一次 Odoo shell PID `2768785`、PG backend `528747`；registry 加载 92 模块后，在 A 场景**准备 S05 合成目录**时退出 1，未发生 SIGSEGV。没有安装/升级、HTTP/Firefox、重试或第二座库。

失败原样：私有同一事务观察记录 `bus.bus` 6→7，发生于 `after_catalog_create`；夹具的严格逐步 bus 行不增断言触发。此前合成 Settings 用户创建曾记录一个 bus precommit 意图，投影为 `res.users/other`，但目录阶段的 bus 行**实际来源未知**；不能把它归咎于仓库，也不能把 W1 用户类型见证自动移植为白名单。该阶段 `mail.mail` 0→0、`account.move/payment/partial.reconcile` 与 `stock.move` 分别 0→0、仓库 1→1、库存 config 0→0、受管价 0→0。S05 价格创建/审核/发布、quote/快照、组预配置和 `inventory.setup` 均**尚未执行**。A/B/C/D 真实兼容场景均 **NOT_RUN**；本批没有 Odoo 产品 PASS，也没有产品 FAIL 证据。普通原生价归档政策继续 **POLICY_PENDING**。

Odoo 退出后独立只读核对：新库上述计数回到模板基线，`bus.bus=6`、`mail.message=851`、`mail.mail=0`、仓库 1、库位 12、门店/受管价/快照/库存 config/S01 审计与四项资金/库存业务表均 0；其它连接 0。事务内 `mail.message` 曾 851→858；新库 filestore 在模板 124 文件外留两文件，大小 305B/0B，哈希见私有观察，**原样保留**。不能仅凭回滚称文件可删除或外发绝无风险。全部历史库、filestore、日志与事故证据未动。

私有控制器、夹具、入口和观察日志在权限 700 的 `.local/odoo-c1-20261014-6169133942/` 与新库专属目录；日志 SHA256 `19fdc578e528e1260bafdccf1168afaf2e5c562e83d39bb41a3e2b1890cc186b`。脱敏机器索引见 [diagnostic.json](evidence/odoo-c1/diagnostic.json)。按一次 shell 异常即停，未修改夹具后重试。后续需 GPT 独立复核该停止点与候选设计，另行限定授权才能继续真实 Odoo 回归。

状态：S07 候选 **NOT_ACCEPTED**；S05×S07 兼容 **UNRESOLVED**；集团全局组政策 **POLICY_PENDING**；Native SIGSEGV 根因 **UNKNOWN**；S10 技术和生产 **BLOCKED**；S11 **NOT_STARTED**。
