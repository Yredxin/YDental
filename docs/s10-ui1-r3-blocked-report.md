# S10-UI1-R3：候选已加载，修后 Web 于首份 PDF 阻断

**结论：BLOCKED。** 固定 controller/QWeb 候选已经在唯一 R3 新库真实升级并加载。真实 Firefox 的剩余费用出账表单返回本地 303，重新显示结算工作台和可信反馈；新增一张合成 100.00 的 posted 原生账单，继承账单未变。随后的首份 bill PDF 请求实际返回 HTTP 409；浏览器夹具只等待下载，30 秒超时，未保存该响应正文。因此本批立即停止，不能把前一步成功扩展为完整 Web、PDF 或 S10 验收。

## 身份与先行门槛

按 [#34 R3 授权](https://github.com/Yredxin/YDental/issues/34#issuecomment-6182876575)和 [R2 独立复核](https://github.com/Yredxin/YDental/issues/34#issuecomment-6182771191)，通过 GitHub API 读取 #23/#29/#31/#34 当前正文及全部有效评论（3/7/8/120），核查 #35 OPEN、0 评论；执行前没有更新授权、交付或并行执行。`origin`、本地和远端分支均为 `c2a26eed14ecf2f3961539f607145a737596c1d6`，工作树干净。Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、历史 S10 product/test、当前 S10 service blob、S07 service SHA256 和 controller/QWeb 候选哈希均符合授权。产品候选及其他产品代码本批零修改。

原 R2 库 `ydental_s10_test_20261015014500_c72e6f91` / OID2100240 是本批唯一克隆源，不是空模板。只读核实 cluster `7694897083368259627`、配置/marker 哈希、0 活动连接、92 已安装模块、2 条各 100.00 的合成确认费用、1 次 bill receipt/source、1 张 posted 100.00 且余额 100.00 的原生账单、0 payment/refund/close；S01 审计 162。实际 filestore 150 文件，164 条附件引用所指的 75 个唯一文件存在且 SHA1 匹配。源库、filestore 和原证据持续保留。

新增 R3 测试脚本副本保留 R2 的 marker、固定适配器和阶段门禁。实际 `create()`/CLI 分发经非空临时文件、假 PG/网络走完复制、假 CREATE、marker、新 fixture 与末尾校验，并覆盖复制/CREATE/创建后身份/重复调用及阶段失败，7 项 **SIMULATED_PASS**；原 R2 的 34 项合同及 19 项全控制流离线检查重跑 **SIMULATED_PASS**。编译和 XML 静态检查通过，均不当作真实 Odoo 验收。

原 venv、锁定 core 的真实 `_parse_config` 在禁 DB 连接、registry、子进程和监听的环境下执行 6/6 个独立解析进程。旧 `--test-disable` 被拒绝（exit2）；第二次有效 argv 已完成解析，但证明阶段的额外 Git 子进程触发守卫（exit1），离线去除该额外调用；第三、四次拟用配置分别接受完整升级和 HTTP argv。CREATE 后，第五、六次对**实际新配置**分别接受完整升级和 HTTP argv：升级只对目标库更新 `ydental_settlement`、`init={}`、HTTP 关闭、`stop_after_init=true`；HTTP `update/init={}`、HTTP 开启、`stop_after_init=false`；两者 `test_enable=false`、`test_tags` 空、`test_file` 空，addons/data_dir/dbfilter/loopback 与新库一致。无解析进程连接数据库或执行升级。

[强制预检](https://github.com/Yredxin/YDental/issues/34#issuecomment-6183019141)在 CREATE、真实 Odoo 和 Firefox 前发布，并经 API 逐字读回。预检已列完整命令、最多 12 次业务/导出提交中的具体 11 项和 STOP 条件。

## 唯一真实运行

从源 OID2100240 仅一次 CREATE 新库 `ydental_s10_test_20261015024000_d36e2b81` / OID2100256，独立端口 18272、配置、data_dir、filestore 和严格 dbfilter；新 marker 如实记录 `source_oid=2100240` 和目标真实 OID。独立 `verify-target` 核实 marker、固定适配器及继承财务基线。没有复制旧 cookie、会话或旧成功标记。实际新配置的真实 CLI 解析再次通过后，按顺序启动恰好两个 Odoo 进程：一次 `-u ydental_settlement` exit0，随后 HTTP 进程就绪且最终按精确 PID 正常停止 exit0；两者均未见 signal11 或超时。升级前后继承 fee、source、receipt、原生账和 S01 审计逐行相同；新库数据库 QWeb 实际包含候选表单标识及反馈节点，源库仍是原 QWeb。未自动开启测试。

唯一 Firefox/Playwright 进程使用新登录的隔离角色 contexts。经理对剩余 fee2 提交普通 HTML 出账，响应 303 `text/html`，本地 `Location` 携随机通知令牌，最终回到 `/ydental/settlement` 工作台并显示服务端会话反馈。真实新库只有 fee2 的新增 bill receipt/source 和一张 posted 100.00、余额 100.00 的原生 out_invoice；继承 invoice1 仍 posted、余额 100.00，未发生自动核销、payment、refund、close 或 partial reconcile。审计从 162 到 178，包含登录/范围、出账和只读查看等分类；`mail.mail=0`、内部 Bus 30 未增加。该出账是本批 **1/12** 次事先列名的成功业务提交，不是 R2 继承成果。

首个 bill PDF 真实 GET `/ydental/settlement/pdf/bill/2` 在 Odoo HTTP 日志中返回 **409**，没有产生下载。浏览器夹具等待下载超时后 exit1；409 响应正文未被捕获，精确拒绝原因 **UNKNOWN**。同一日志在请求前报告缺少 Wkhtmltopdf/Wkhtmltoimage，提示 PDF 渲染环境可能相关，但本批没有证明 409 的完整错误链，也没有进行系统调查、产品修补或重试。HTTP 409 与夹具未捕获非下载响应这两个事实分别记录；不归咎于未证明的单一原因。

| 验收项 | 本批实际结果 |
| --- | --- |
| 真实 CLI、源库身份、一次克隆、候选升级及 QWeb 加载 | PASS，证据范围仅限上述检查 |
| 修改前 HTML 导航到 JSON | R2 已真实复现，本批按授权未重跑 |
| 修后 HTML 成功、持续工作台及 fee2 原生账务 | Firefox/HTTP/原生账务有限 PASS |
| bill PDF 下载 | HTTP_FAIL：409；响应正文 UNKNOWN，下载及视觉 NOT_RUN |
| 收 60、申请退 20、异人审批、实退、日结、财务解锁 | NOT_RUN |
| HTML 失败反馈、JSON 200/403/409、CSRF、跨店、自批、撤权旧 revision、同 key/刷新 | NOT_RUN |
| receipt/refund PDF、三类逐页中文视觉、无权直链 | NOT_RUN |
| >50 条真实 HTTP 分页 | NOT_RUN；未伪造受控财务行 |

额度：解析 6/6；新库 1/1；业务 Odoo 2/2（顺序），其中新库升级 1/1；Firefox 1/1；计划内成功业务/有审计导出 1/12。prepare 和原版 HTTP 均为 0。浏览器在 PDF 下载等待超时后停止；没有第二次浏览器、升级、数据库或业务重试。原 R2 库末次只读仍是原 2 fee、1 source/receipt/move、posted 100.00/余额 100.00、0 payment/refund/close/partial、审计 162，config/marker 哈希不变。所有历史数据库、filestore、失败现场及新库保留。

下一步需 GPT 独立复核并另行明确：如何在受控范围取得 HTTP 409 正文、如何处理 PDF 渲染条件，再决定是否给新的单批 Web 预算。本批不改产品、Odoo core、固定适配器、财务模型、Project/Issue 状态；不 sudo、不做基础设施安全专项、不重跑 FC1/FC2、不合并/部署/启动 S11。S10 完整技术及生产仍 **BLOCKED**，旧 Native SIGSEGV 根因 **UNKNOWN**。[脱敏机器证据](evidence/s10-ui1-r3-blocked/verification.json)仅含状态、数量及哈希；原始日志、截图、凭据和合成身份留在私有运行目录。
