# S10 Native D1.7-R1 仓库优先 L2 准备阻断报告

## 1. 授权与固定身份

唯一授权为 [#34/6164071875](https://github.com/Yredxin/YDental/issues/34#issuecomment-6164071875)。原分支 `codex/s10-settlement-finance-r1-20261013` 从 `ab2dcb3ef020855c75fd371d8936a459b4b9e226` 前进；固定 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 均未修改。GitHub #23/#34 正文与有效评论、最新授权、#35 OPEN/0 评论均由 API GET 读取。PG 为 `127.0.0.1:5432`，cluster `7694897083368259627`。工作树开工时干净。

## 2. 离线纠错及强制检查点

上轮私有夹具在 S05 `_price` 后调用 S07 `_setup`，而原生 `stock.warehouse.create` 在第二仓库配置中可通过 `res.config.settings.execute` 调用 `product.pricelist.action_archive`；S05 的 `_ydental_guard` 拒绝无受控上下文归档。新私有夹具仅将唯一仓库 setup 移至 S01 授权之后、S05 正式价格之前，并断言 setup 前后无受控价目表、发布后唯一受控价目表 active。没有修改产品、原生模块、hook、固定 runner 或非法注入 `ydental_intake_mutation`。这只改变私有诊断夹具的顺序；**S05 受控价目表 × S07 新增仓库的产品级兼容性风险仍 UNRESOLVED**。

旧夹具 SHA256 `72d76cd84b0d78e28fd454ad65f66ec6d7988672f3f21203c30ec8c4daca6cbb`；新夹具 `0123ae7a9392680a08cf41bd06f85926d42c40a9ddc682537ec544d7330b3641`，完整 diff 留在权限 700 私有目录。`py_compile` exit0，AST/fake 16 正 26 负 exit0，标记 SIMULATED；原未修改 hook 函数体 AST stub 离线 1 正 12 负 exit0。第一次 hook 工具调用漏 `offline` 参数 exit1，纠正命令后 exit0；GDB 版本检查首次未加载私有库失败，正确设置 GDB 私有 `LD_LIBRARY_PATH` 后确认 17.1 exit0；均未启动 Odoo。首次 GitHub POST 将 Markdown 原文错误用作 JSON body 获 HTTP400；正确封装 JSON 后 [检查点 #34/6164241741](https://github.com/Yredxin/YDental/issues/34#issuecomment-6164241741) 发布成功，API GET 与本地正文逐字一致，SHA256 `3029f94b5b8f9e15f077d2f494bc489d46f9b4338485d6126a3ee9d922ec5708`。这些失败原样保留，不冒称首次成功。

模板 `ydental_s10_test_20261014044700_4f6a8d2c` / OID2100080：92 精确模块（清单 SHA `c1bbaa9395bd01d9e11912d56b73155d2b6cd63d3fbf1f58de0404d58e66b8a0`）、16 类业务交易表 0、70 系统附件、124 安装文件 SHA 一致、活动连接 0。模板无价目表记录，已有 1 个原生仓库。事故库 OID2056451、上轮失败库 OID2100087 及其他旧 OID 未用作模板。

## 3. 唯一新库与真实执行

唯一新库 `ydental_s10_test_20261014082746_bab36c03`，OID2100096，端口18255，cluster 同上；一次 `CREATE DATABASE ... WITH TEMPLATE ...` 经独立 postgres 管理连接 autocommit/IDLE/安全 Identifier 执行，外层 clone exit0。config SHA256 `d68b7f771e60436a8e2937525c7494c8757346759743bd99654e3acc7f274a7b`，marker SHA256 `73a64d0e6e9d1bf5a577e10f890b7130ac932fe29ec1019d0c202da659770e3a`，专属 data_dir/filestore/dbfilter、loopback/禁 SMTP/cron0；124 系统文件逐 SHA 复制。真实新 OID 的未修改 hook AST stub 接受，`l2_capture.target` 独立只读预检 PASS。配置与原始文件均留私有 700/600 目录。

准确外层命令及退出码：

| 顺序 | 命令 | 退出 |
|---|---|---:|
| 1 | `../.venv/bin/python .local/s10-native-20261014-6164071875-d17r1/l2_capture.py clone` | 0 |
| 2 | `../.venv/bin/python .local/s10-native-20261014-6164071875-d17r1/hook_verify.py real-marker` | 0 |
| 3 | `../.venv/bin/python .local/s10-native-20261014-6164071875-d17r1/l2_capture.py prep` | 2 |

A 由私有 GDB17.1 父 PID2600098 启动唯一 Odoo shell 目标 PID2600105，GDB/目标实际 exit1、无 signal11；Registry 载入区间 UTC 08:31:34.400—08:31:35.079。GDB 日志 SHA256 `7003652da2b2cd9aecd14c0ed3298423638bcf125897fdd30bf170d1f30b9071`，9227 字节。shell 在 `front._operate('report')` → `ydental_queue._queue_accept` → `ydental.queue.service._settings` 抛出 `configuration_required: Publish explicit heartbeat and timeout settings`；锁定源码 `ydental_queue/models/ydental_queue_service.py:54-60` 读取的 `ydental_queue.heartbeat_seconds` 为空，`int('')` 失败。该问题是本次真实执行新发现的准备前置配置缺口。没有 canary、没有唯一 confirmed event/fee，A **FAIL/BLOCKED**。由于 A 未通过，未发布 A 放行检查点，也未执行 B 双 GDB 窗口。不能把到达报到步骤解释为价格/仓库产品兼容性已修复。

## 4. 回滚后只读保全与 STOP

A 的自有 ORM 事务未执行最后的 commit。独立只读 PG 显示新库患者、治疗事件、fee、S07事件、stock.move/quant、受控价目表、account.move/payment/partial、S10 source/payment/refund/close、mail_mail 均 0；原 70 附件仍在。目标 filestore 共 130 文件，其中 124 为模板安装文件、6 为本次未被附件引用的新增文件；按授权原样保留，既不清理也不解释为已提交临床附件。原事故 OID2056451、模板 OID2100080、上轮失败 OID2100087 均不变；模板审计复跑 exit0、124 文件 SHA 一致。原上轮失败库的 6 个孤立文件、ledger 和 GDB 日志也未触碰。

实际预算：CREATE 1/1，A Odoo 1/1，B Odoo 0/2，合计 Odoo 1/3，Firefox 0，业务资金动作 0，已提交 L2 事实 0。未取得 Native C 栈，因为本次没有 SIGSEGV。原 S10 native 根因仍 **UNKNOWN**；无崩溃不等于修复。建议下一授权先静态确定合法的队列 heartbeat/timeout 发布配置路径、最小值和保护规则，再决定是否值得新库重试；本批不自行补配置或追加进程。

## 5. 私有证据与治理

原始日志、配置、marker、attempt ledger、完整 diff 与只读审计在 `.local/s10-native-20261014-6164071875-d17r1/` 和 `.local/ydental_s10_test_20261014082746_bab36c03/`（目录 700、私有文件 600）。脱敏机器索引见 `docs/evidence/s10-native-d17-r1-reorder-blocked/diagnostic.json`。本批 Project 0 mutation；#34 保持 OPEN，#35 未启用；旧库/filestore/volume/core/备份不删不改，Odoo20/odoo-12/产品/固定runner不改；未合并、强推、S11 或生产部署。S10 技术与生产持续 **BLOCKED**。
