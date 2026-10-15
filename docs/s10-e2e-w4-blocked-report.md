# S10-E2E-W4 方案 B 收款收尾：升级范围门槛 BLOCKED

## 授权与事前门槛

- 唯一授权 [#34 / 6185772190](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185772190)，W3 独立复核 [#34 / 6185715797](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185715797)。固定原分支和本地/远端起点 `71a554667157cdd917c0062db5e4ddf1693f6410`，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。API 读取 #23、#29—#34 当前正文和有效评论，#35 OPEN/0；没有并行 W4 任务。没有修改产品 addon、财务模型、ACL、Odoo core 或 W3 历史证据。
- 完整离线门槛见[预检说明](s10-e2e-w4-preflight.md)、[页面及收款合同](s10-e2e-w4-payment-contract.md)和[现行机器预检](evidence/s10-e2e-w4/preflight.json)。真实 Odoo20 CLI 解析只请求 `-u ydental_settlement --stop-after-init --no-http`；同一 `execute_pipeline` 与 `payment_flow` 的离线正例和 23 个 STOP 注入通过。来源 W3 OID2100285 的四费600/80/40/20、原生库存、唯一 posted740/residual740 账单及零付款、92 模块、38 表逐行签名、152 filestore 文件和 164 附件指针均在 CREATE 前只读核实。
- 第一次事前检查点 [#34 / 6186047602](https://github.com/Yredxin/YDental/issues/34#issuecomment-6186047602) 已发布并逐字读回。CREATE 前真实 `checkpoint()` 因预检 JSON 路径写错而 STOP；当时资源使用全零。只修本批 W4 控制脚本和离线夹具，保留[第一次预检](evidence/s10-e2e-w4/preflight-initial.json)，重跑完整离线门槛并以真实预检 JSON 核验 `checkpoint()`；[哈希补充检查点 6186090718](https://github.com/Yredxin/YDental/issues/34#issuecomment-6186090718)经 GitHub API 逐字读回后，才启动唯一真实执行。

## 唯一新库与升级事实

从 W3 合成库 `ydental_s10_test_20261015060000_b6c7d8e9` / OID2100285，只读克隆唯一 W4 库 `ydental_s10_test_20261015064000_d41e7b62` / **OID2100301** / port18279。一次 CREATE exit0；克隆后来源/目标的 38 张临床、价格、库存、会计、结算及本店权限表完整行签名相等，已安装 92 模块、安装态视图、152 个 filestore 文件与 164 个附件指针一致。来源库始终只读，旧私有材料保留。

只运行一次受控 Odoo20 模块更新进程 PID3358214，`-u ydental_settlement --stop-after-init --no-http`；exit0、无 signal11、无超时，升级日志 SHA256 `80d5cfdc368f512b651c9dbdce5e1681a60bab3205b0768e3c9eb7bc771f60e7`。目标安装态 `ydental_settlement_tokens` 的 `en_US` arch 从旧 SHA256 `7160c6c9d525cc4c7790079a944baa052a25bd488b23cbd77db90ad69b4cf0bc`（无 `output=html`）变为 `f454d4e36da804a2ff87a7519c680d59c33ff38e92e40ef296e2be6e1e49db3d`（有该字段）。这只证明**安装态 arch 已变**；未启动 HTTP，因此没有真实渲染表单或 HTTP303 实测。

升级后只读比较：来源/目标 38 张受控表仍逐行同签名，原生 invoice1 仍 `posted`、总额/余额 740，四个 settlement.source 和原 `bill` receipt 不变，原生 `account.payment`、S10 payment、partial 仍 0。filestore manifest/附件指针同 SHA；`ir.model.data` 的 25,493 个键零变化。`ir.ui.view` 410 个有 key 的视图中，改变的 5 个 key 均属 `ydental_settlement`。两库在取证后无活动连接。

## STOP：非目标模块元数据与依赖加载

固定合同要求仅目标模块元数据可变。实际 Odoo 日志先记 `updating modules list`，然后加载 `ydental_settlement (91/92)`，**还加载 `ydental_settlement_test (92/92)` 并记录“creating or updating database tables”**。只读 SQL 对比 `ir_module_module` 702 条记录：682 条 `write_date` 变化，其中 681 条为同一时间戳，`ydental_settlement_test` 为稍后时间戳；这些记录的 `state` 和 `latest_version` 均未变化，安装模块集合仍为 92。即使目前未观察到已发生的业务经济行变化，依赖模块加载和非目标模块元数据变更已经触发本批预先固定的升级范围 STOP 门槛。不能在本次自行放宽判断后继续收款。

控制命令在 `after_snapshot` 的非目标模块元数据断言退出1，**HTTP 0、Firefox 0、GET真实工作台 0、现金500与240均 NOT_RUN**；未发送任何付款 POST，没有第二次 CREATE 或升级。进程没有新 SIGSEGV；既有 Native 根因仍 UNKNOWN。离线模拟没有复现 Odoo `-u` 的模块清单刷新和依赖测试模块加载，这是本批预检覆盖缺口，不把纯离线 PASS 称为升级范围 PASS。完整脱敏机器证据见[verification.json](evidence/s10-e2e-w4/verification.json)，私有原始 config、日志及新库均保留。

## 交付结论

**W4 为 `BLOCKED_UPGRADE_SCOPE_BEFORE_HTTP_AND_PAY`。** 本批只有已安装 QWeb 同步与经济事实不变的有限只读证据；真实表单、303 反馈和 740→240→0 原生收款核销链均未验证。#34 继续 OPEN，S10 完整技术及生产持续 BLOCKED，不启 S11，不修改 Project/Issue 状态，不合并、强推或部署。请求 GPT 独立复核 Odoo20 模块清单刷新、`ydental_settlement_test` 依赖加载与后续新授权边界；本批现场停止并保全。
