# S10-UI1-R4：PDF 实际通过，权限负向夹具阻断

**本批结论：BLOCKED_TEST_HARNESS，非完整 UI1/S10 PASS。** 唯一 R4 新库上，受控 Odoo 进程实际找到了 `/usr/local/bin/wkhtmltopdf` 和 `wkhtmltoimage`；真实 Firefox 下载了 bill、receipt、refund 三类 PDF，均 HTTP 200、`application/pdf`、响应头 SHA256 与文件一致、各 1 页。三张逐页 PNG 已人工查看：中文清晰，法人/门店、出账时实收 0 与欠 100、收 60 后欠 40、实退 20 与待退 0 的含义符合当时业务状态。收款、退款、日结和解锁也形成对应的原生账务与 S01 审计。后续读权角色的负向测试因**测试脚本在页面上读取不存在的 CSRF 输入**，在发送请求前抛错，唯一浏览器进程 exit1；本批按异常停止，余下项目均标 `NOT_RUN`。没有第二次浏览器或 Odoo 重试。

## 授权、身份和预检

以 [#34 R4 授权](https://github.com/Yredxin/YDental/issues/34#issuecomment-6183640723)、[R3 交付](https://github.com/Yredxin/YDental/issues/34#issuecomment-6183115487)及 [GPT 独立复核](https://github.com/Yredxin/YDental/issues/34#issuecomment-6183199751)为准。GitHub API 读取 #23/#29/#31/#34 正文和全部有效评论（3/7/8/124），#35 OPEN/0；执行前没有更新授权或并行交付。原分支、本地及远端起点均为 `26238bf3351e6d2949e1dbd6afb731e5e5022bdf`，工作树干净。固定 core、S10/S07 服务及 controller/QWeb 哈希匹配授权，本批产品代码零修改。

只读源 R3 库 `ydental_s10_test_20261015024000_d36e2b81` / OID2100256 / cluster7694897083368259627：配置 SHA256 `9d4ecea18b99ceb23cee15a671ec64bd93e6568b5417e9741f1ae55eec72129f`、marker SHA256 `e11b497a74abb65c1d501130fd4e4fd438ddce8790a81a626ba788ee891eabb1`，克隆前 0 活动连接、92 已安装模块，两条各 100 的确认费用、两张各 posted 100/余额 100 的发票、两条 bill source/receipt，付款/退款/日结/partial 为 0、审计 178、mail.mail 0、内部 Bus 30。源 filestore 实际 150 文件，164 条附件引用指向 75 个唯一文件，存在且 SHA1 相符，清单 SHA256 `abf18f3ab41a8db6c22e269b590fd5910cc1fc954f44cbda6bbffc317aa332db`。R3 第二笔 bill 的实际审计用户为 fixture `frontdesk` 用户 6；R2 第一笔为 `manager` 用户 5，纠正上一批报告误称第二笔由经理提交。

用户安装的两套工具在本批受控子进程环境中真实 `which` 到 `/usr/local/bin/`，`--version` 均为 `0.12.6.1 (with patched qt)`。只给本批子进程设置既有私有 Noto CJK `FONTCONFIG_FILE`，不改全局配置。无患者/无外网中文 HTML→PDF 烟测 exit0、`%PDF-`、1 页、SHA256 `ea0267c7546d46e2f928363128475ff93d1a7dfa1b82d7aeb8858d62f023ba45`，只记 **RENDERER_SMOKE_PASS**。初次烟测辅助命令在基础 venv 导入 PyMuPDF 失败、未调用渲染；改用已有私有 verify-lib 后才得到完整烟测。R4 实际 `create()`/CLI 的 Fake 外部服务离线流程 10 项，实际 `pdf()` 函数对 200 下载/409 已知渲染拒绝/403/409 泛错及完整私有正文保存的离线演练均 **SIMULATED_PASS**，不当作 Web 结果。[事前强制检查点](https://github.com/Yredxin/YDental/issues/34#issuecomment-6183755327)已在 CREATE/Odoo/Firefox 前发表并经 API 逐字读回。

## 唯一新库与真实 Web

仅一次 CREATE：从源 OID2100256 至 `ydental_s10_test_20261015033000_a4c82d17` / OID2100265、端口18273，新 marker 真实记录 source_oid=2100256，独立 config/data_dir/filestore/dbfilter。CREATE 后独立检查真实 OID、marker、固定适配器、继承账务和候选 QWeb 通过。不重新出账、不准备临床、不升级模块。唯一 Odoo HTTP PID3244847 正常停止 exit0、无 signal11/超时。运行日志实际记录使用上述两套 wkhtml 工具。三次 wkhtmltopdf 还报告 `ConnectionRefusedError` 警告，但 Odoo 随后分别返回三份有效 PDF；警告不等于本批 PDF 拒绝，也不据此推断旧 409 的唯一根因。

唯一 Firefox 进程用隔离的 manager/frontdesk/reader contexts 重新登录。bill PDF 在任何 R4 资金动作前真实 GET，响应 200 且浏览器下载；未改变原生资金行，新增一次 `settlement.report_download` 审计。随后 user6 (`frontdesk`，已明确具有本店结算写权) 只选继承 invoice2 现金实收 60；invoice1 仍余额 100，invoice2 变余额 40，一笔原生 inbound payment 60、posted entry 60 与 partial 60。退款申请 20 为 requested；不同人 user5 审批后由 user6 实退 20，退款 done，一张 posted out_refund 20、原生 outbound payment 20/posted entry 20、partial 20。同一实际收费员/门店/业务日/现金日结记 gross60、refunded20、pending0，再由 user5 财务解锁，close 状态 `unlocked`。对应六次普通 HTML 提交均返回本地工作台 303 与可信反馈，各有独立 receipt/S01 业务审计。收款同 key JSON 重放返回 200 `already_accepted`，刷新未增加原生资金；伪造 notice 查询未显示成功反馈。请求者自批与跨店审批各真实返回 403。登录、只读查看和门店切换产生的审计与上述业务审计分开；源库末次只读仍为原 2 张 posted 100/余额各100、资金/退款/日结/partial0、审计178、mail0/Bus30。

三份 PDF 实际下载 SHA256：bill `27508b1e6e4192e80e7dcd5daaff5046919a90c597bc76a99a61aaaf0c18902a`；receipt `cb5c6c423e182f31a45d217925102402e4ad8398a6e360bf456dd3d2eb907bae`；refund `203018cc943191a3498435b4ee9c59b753a069cbadc1e3adc7f121314ce12d59`。每份 1 页，SHA 与响应头相等、中文标签及金额提取通过；私有逐页 PNG 已逐张目视，均显示演示非税务声明和当时正确的法人/门店及金额。PDF 文件、PNG、原始日志、合成身份与凭据均仅保留在权限受限的 `.local`，不上传 GitHub。本批**没有再出现 HTTP 409**；新夹具对非 2xx 先保存完整正文的路径只完成离线演练，不能反推 R3 当时 409 的精确正文或唯一原因。

## 停止点、未测与用量

在业务完成后，脚本对只读角色准备测试无写权限时，`api(reader, 'bill', ...)` 从当前结算只读页面寻找 `[name=csrf_token]`，该输入不存在，Playwright `page.evaluate` 在浏览器内抛出 `null.value`；**该无权 POST 未发出**，因此不是产品 403/权限验收失败。浏览器 exit1，`browser-complete.json` 未产生。后续不修改脚本重试。另一个只读 `verify-target` 命令在业务后按设计要求目标财务等于源财务，因此 exit1；这条命令本应只在业务前使用。业务后改用仅检查 marker/OID 的 `target()` 和源库只读基线校验，均通过；这不表示已发生旧数据变动。

| 项目 | 结果 |
| --- | --- |
| 受控 PDF 工具及中文最小烟测 | `RENDERER_SMOKE_PASS`，非 Odoo 业务 |
| 实际 Odoo 的三类 PDF HTTP/下载/SHA/1页中文视觉 | bill/receipt/refund `PASS`，仅本批合成对象 |
| 收60、申请退20、异人审批、实退20、现金日结/财务解锁 | Firefox + 原生账务 + S01 `LIMITED_PASS` |
| 同 key 重放、刷新、伪造 notice、请求者自批、跨店审批 | 指定路径 `PASS`；不概括其它权限 |
| 无写权用户 POST、JSON 403/409、无效 CSRF、撤权旧 revision、HTML 失败反馈、无权 PDF 直链 | `NOT_RUN`；停在发出无写权请求前 |
| JSON 200 原有成功合同 | 同 key `already_accepted` 指定路径 `PASS`；其它成功操作 JSON `NOT_RUN` |
| >50 条真实 HTTP 分页 | `NOT_RUN`，未伪造受控财务记录 |

实际预算：新库 1/1、Odoo HTTP 1/1、Firefox 1/1、模块升级 0、准备 shell 0、原版 HTTP 0；事前列名成功业务/有审计导出 **9/12**（六项业务 + 三类 PDF），管理员撤权未运行，其余两次未分配不消耗。基础 Python 包装器首次因用了系统 Python 导入 psycopg2 失败，在启动 Firefox 前退出，随后用原 venv 启动唯一 Firefox；这不构成第二浏览器。业务数据库在停止后只做只读核对：目标 2 张原生 posted out_invoice（余额 100/40）、一张 posted out_refund20、两笔原生 payment60/20、两条 partial60/20、退款 done20、日结 unlocked，S01 审计 234、mail.mail0、内部 Bus30。没有真实新 SIGSEGV、未知外发或重复资金证据；旧 Native 根因仍 UNKNOWN。

本批只新增 R4 专属测试、报告和[脱敏机器索引](evidence/s10-ui1-r4-blocked/verification.json)，保留所有旧库及新库、filestore、marker/config、日志/core/备份。未使用 sudo、安装软件、做基础设施安全专项，未改产品/core/fixed adapter、Project/Issue 状态，不重跑 FC1/FC2、不合并/部署/启动 S11。完整 UI1 与 S10 技术/生产继续 **BLOCKED**，等待 GPT 独立复核下一步夹具修正范围。
