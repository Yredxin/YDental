# S10-E2E-W3 方案 B 有界 Web 尝试：BLOCKED

## 边界与事前检查

- 唯一授权：[GitHub #34 / 6185309077](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185309077)；W1/W2-G0 独立复核和 #23、#29—#34 当前正文及有效评论已按授权读取，#35 OPEN/0 评论。起点与原远端 HEAD 均为 `a17cf61fadd983aa83ed53c791e79713b83f0b58`，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。没有并行 W3 任务。
- 纯合成模板 `ydental_s10_test_20261014044700_4f6a8d2c` / OID2100080：92 模块、被检经济表全空、无活动连接；124 个 filestore 文件逐 SHA256 核对。69 个附件指针引用其中 62 个不同文件。原库、附件、历史证据均保留。
- W1 的检查任务 `.task-id` 选择器只对应药房执行段。本批改为已签发检查行→任务和真实队列待报到任务双向核对，并检查处方首发/4+2 续发、工位、接诊、HTML 必填、CSRF/revision、原生库存与财务。23 步源码合同见[选择器合同](s10-e2e-w3-selector-contract.md)。同一浏览器流程在离线 DOM/HTTP/SQL 模拟中跑完 23 步、38 个异常按预期停止；真实 Odoo20 CLI 参数解析和只读 SQL schema 通过。详见[事前预检](s10-e2e-w3-preflight.md)及[预检机器证据](evidence/s10-e2e-w3/preflight.json)。
- CREATE 前检查点 [#34 / 6185552492](https://github.com/Yredxin/YDental/issues/34#issuecomment-6185552492) 已发布并经 API 逐字读回；事前九个可执行脚本 SHA256 与预检证据一致。后增的 `s10_e2e_w3_readonly_audit.py` 仅用于 STOP 后只读审计和生成脱敏证据，没有运行 Odoo 或 Firefox。

## 唯一真实窗口

只克隆一座新库 `ydental_s10_test_20261015060000_b6c7d8e9` / OID2100285 / 端口18278；CREATE 1 次 exit0。预备 Odoo shell 1 次（PID3332873，exit0），只建立合成主数据、角色、价格、原生入库各 20 件及合法财务配置，准备后无业务费用、发票或收款。未安装或升级模块。HTTP Odoo 1 次（PID3333099），按自身 PID/config 精确停止，exit0。Firefox/Playwright 1 次（PID3333227，exit1，signal11=false，未超时）。三进程均无 SIGSEGV，业务脚本失败后没有重启或重试。原有开发 Odoo 未触动。资源与日志哈希见[脱敏只读审计](evidence/s10-e2e-w3/verification.json)。

浏览器实际完成并逐步记录前 20/23 个步骤，34 个成功 POST 均逐条落盘，保留 20 张私有截图哈希。患者 ID1、门店 ID1、公司 ID1；真实 Web 完成就诊报到、诊疗文书、治疗、检查医嘱和接诊/确认、处方首发、药房 4+2 分段发药及工位交还。四条 confirmed 临床事件/费用/价格快照逐 ID 对应：event/fee/snapshot 1 为治疗 600，2 为检查 80，3 为处方 4×10=40，4 为续发 2×10=20。检查结果 ID1 confirmed；四次队列 execution 已完成、四个 lease 均非活动且释放原因为 `holder_exit`。业务原生 `stock_move` 3/4/5 均 done，分别出库物料 1、药品 4、药品 2；入库 move1/2 各 20，全部为合成物料。S01 对应临床、发药、检查、库存和账单审计均为 accepted。

第 21 步由真实结算 Web 表单提交，**经济事务已经提交**：四条 `ydental_settlement_source` 分别将费用 20/40/80/600 关联原生已过账发票 ID1；发票总额 740、未付余额 740；结算 `bill` receipt ID1 返回金额/余额 740，S01 `settlement.bill` accepted。服务端记录该 POST 为 HTTP 200。浏览器按预先固定的 HTML 合同要求 HTTP 303，得到 200 后于 `('settlement_http_class', 200)` 断言失败；该账单步骤没有写成功事件或截图。第 22/23 步线下 500 和补收 240 **NOT_RUN**；`account_payment`、`ydental_settlement_payment`、`account_partial_reconcile` 均 0，不得声称费库款全链通过。

## 停止原因与证据边界

STOP 后只读比较发现：原模板与本批新库中 `ir_ui_view` 键 `ydental_settlement.ydental_settlement_tokens` 的已安装 arch 相同，均**缺少** `name="output" value="html"` 隐藏字段；当前跟踪的 QWeb 源码有该字段。当前 controller 的 HTML 303 分支要求 `post['output']=='html'`；缺少字段可解释观察到的 HTTP 200。源 arch SHA256 `7160c6c9d525cc4c7790079a944baa052a25bd488b23cbd77db90ad69b4cf0bc`，当前 QWeb 文件 SHA256 `8f74cffa93a3a24f1d4c4f95a2a006fd698050cda8d27a99924de58770feb329`。这是**安装态 QWeb 与当前源码不一致**；不能据此断言当前产品源码实现有缺陷，也不能把 HTTP 200 直接称为账单事务失败。事前预检只核对文件源码，漏掉已安装 arch 的关键字段，故预检结论对这个运行态合同不充分。

根据授权，已提交经济业务后脚本失败立即停止。未重跑账单或收款、未改脚本重试、未升级模板或目标模块、未另建库。原模板被检经济表仍全空，两库在 HTTP 停止后均无活动连接。原生历史 SIGSEGV 根因继续 UNKNOWN；本次没有新的 SIGSEGV，不构成根因修复证据。

## 交付状态

本批只新增 `scripts/s10_e2e_w3_*`、`docs/s10-e2e-w3-*.md`、`docs/evidence/s10-e2e-w3/*`；不修改产品源码、财务模型、ACL、Odoo core、旧测试记录、Project/Issue 状态，不启 S11，不合并或部署。私有原始日志、动作事件和截图保留在 `.local/ydental_s10_test_20261015060000_b6c7d8e9/`；公开证据仅含脱敏 ID、数额、状态与哈希。[verification.json](evidence/s10-e2e-w3/verification.json)可核对所有实际经济行、进程退出码和私有文件哈希。

**W3 方案 B 为 BLOCKED，S10 完整技术与生产仍 BLOCKED。** 下一次若获新授权，需先核对已安装 QWeb 合同并明确修复/升级方案，再以新的有界窗口验证；本次绝不继续业务执行。
