# YD-N1 R1 / S10-P0-04 BLOCKED 交付与独立复核申请

## 范围与停止结论

唯一授权为 [#34/6205786507](https://github.com/Yredxin/YDental/issues/34#issuecomment-6205786507)。原分支从 `35d24828ad3e05a9b006168cd2c01bd43677a50d` 前进；Odoo20 core 固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。已读 #23、#34 当前正文及全部有效评论、#35 OPEN/0，以及 P0-03 预检、交付和 GPT 复核。正式预检 [6205917372](https://github.com/Yredxin/YDental/issues/34#issuecomment-6205917372) 和 CREATE 前字段路径修正的补充预检 [6205929586](https://github.com/Yredxin/YDental/issues/34#issuecomment-6205929586) 均经 GitHub API 逐字读回；后者冻结最终脚本 SHA 和预算。首次控制命令在 `checkpoint()` 的旧式 JSON 字段引用处停止，CREATE/HTTP/Firefox/POST 均为0；修正、重新离线验收和补充读回后才启动真实流程。首版预检原件保留在 [preflight-initial.json](evidence/s10-p0-04/preflight-initial.json)，最终冻结版为 [preflight.json](evidence/s10-p0-04/preflight.json)。

**本批整体 BLOCKED。** 唯一新克隆 `ydental_s10_test_20261016_p004_9a6e37f2` / OID **2100320** / 原 cluster `7694897083368259627` / loopback **18287**。真实 Firefox 到达旧日结9第二页，并完成 user10 一笔 `unlock(close_id=9)` 的无权拒绝。user14 在他店会话 GET 到合法表单后，浏览器测试脚本把 `close_id` 从63改为9，却继续使用依赖 `[value="63"]` 的 Playwright locator；随后填理由超时，**未持久化 user14 intent、未发送其 POST**。user6 合法 unlock9 也 **NOT_RUN**。唯一 Firefox/HTTP 额度已用，未重启或重试。

停止后独立只读发现 user14 门店3结算页 GET 新增四条 `settlement.invoice_view` accepted S01 审计，累计本批新增审计 **13** 条，超过事前字段门禁 **11** 条，且该事件类型不在事前允许集合。该门禁也为失败，不以原生 GET 来源为由事后放宽。原生资金、库存和全部历史业务记录仍匹配。

## 证据分层

| 项目 | 证据级别 | 实际结果 |
|---|---|---|
| 退款14驳回 | HISTORICAL_REAL_WEB_REFUND14_REJECT | P0-03 已真实驳回；本批永久只读，refund_reject POST 0 |
| 三源保全 | NEW_READONLY_P003_SOURCE | R3 OID2056451、P0-02 OID2100311、P0-03 OID2100319 的固定表/schema/module/view/filestore签名与封存原件全等；无活动连接 |
| P0-04 初始克隆 | READONLY | 一次 CREATE；643张public表、265张受管表/schema/module/view、194份filestore及1075附件指针与P0-03停止库全等 |
| 日结9第二页 | NEW_REAL_WEB_CLOSE9_PAGE2_GET | user6 实际点击 `closes_page=2`，GET **200**；ID9/confirmed/最新cycle可见，HTML表单含自身CSRF、key、revision、`output=html`，pageerror 0；截图SHA见机器证据 |
| user10 无权 unlock9 | NEW_REAL_WEB_PERMISSION_DENIAL | 自身登录/门店1/CSRF/revision/唯一key；先存intent，再原生HTML POST **1次**；HTTP **303**、跳转GET **403**、Odoo服务端 `actor=10 action=settlement.action result=denied`；S01未新增denied行，产品 `_denial` 实际只写服务端日志；独立只读确认close/refund/receipt/mutex/资金不变，字段门禁PASS |
| user14 跨店拒绝 | NOT_RUN_POST | 自身门店3登录及结算页GET **200**，ID63合格表单存在；修改目标ID后 locator 超时，未到intent/POST |
| user6 唯一解锁 | NOT_RUN | 无unlock9 intent、POST或成功收据；close9仍confirmed、mutex仍243 |
| 命令收据与mutex门禁 | COMMAND_RECEIPT_MUTEX_FIELD_GATE | 离线唯一成功正例核 revision243→244、唯一receipt按真实reason/key重算SHA256；真实本批只核旧receipt242及revision243不变。成功 Web 门禁 NOT_RUN |
| 原生资金库存 | NATIVE_FINANCE_UNCHANGED / READONLY | 原生move/line/payment/partial/full reconcile、stock及YDental经济源/收款/实退相关14表逐表签名与克隆初始全等；receipt命令表单列为元数据，242旧行全等、没有新增行 |
| 模拟 | SIMULATED_PASS | 同顶层控制路径1正例；40反例全部FAIL_CLOSED。真实Odoo20 CLI parser确认无升级/init/install/shell/test |

P0-03 退款14仍 `rejected`、approver6、S01审计2661、无原生outbound/credit；命令收据242仍为 actor6/store1/refund_reject、实际退款0，mutex XMLID唯一行ID1 revision243。日结9仍门店1/收费员5/2026-07-15/card、cycle1最新、gross/refunded/pending均0、confirmed。user6门店1有settlement与finance_approval写权；user10门店1无两权；user14仅他店3有两权。本批未再次提交退款14任何操作。

## 过程、门禁与原因

控制命令为 `.venv/bin/python scripts/s10_p0_04_control.py run`。最终 [预检](evidence/s10-p0-04/preflight.json) SHA256 `025348bbb9bf9224f9df00054e0ad79c4d5d9ec3b1c9c17251dd9222fb5e4226`，首版 [预检原件](evidence/s10-p0-04/preflight-initial.json) SHA256 `f6655245c9d56ebfe6fa9565a292d2274f10f23b263fbb142dbae5562dc3b2ee`。最终脚本6份 SHA 逐项固定在预检中。事前允许的成功变化仅 close9 六字段、mutex ID1 revision一次+1、唯一actor6/store1的 unlock 命令收据及一条对应S01 accepted；其余业务、资金库存默认全签名一致。无权请求不得推进业务或命令元数据；原生资产/首次登录等按事前逐字段上限核验。真实已执行的 user10 无权POST通过该门禁。

唯一 HTTP PID **4006255** exit **0**，log SHA256 `148141e83b51dbab47fa7b828d615ac8778274ae7488f3db261454a0d281f791`；唯一 Firefox PID **4006329** exit **1**（Playwright locator超时，非SIGSEGV），log SHA256 `bcec47a69913ef8b93a27fd7b8c13ce2a35d42f3ca60cd3b86adf82525cf6ae6`。CREATE命令为 `CREATE DATABASE "ydental_s10_test_20261016_p004_9a6e37f2" WITH TEMPLATE "ydental_s10_test_20261016_p003_75c1e9b2"`，一次成功。目标 marker SHA256 `8afd6122428c723fafa597536c64f146b5b5a339bbb866229d8660f648173f29`，config SHA256 `578a1304e65dab36440c6e51374276903d7b9ba989e4b75697c1fb9ae62abc`，filestore manifest SHA256 `27174fa6aa277611a62f4feaf8deb65701d5bbd0d38f91b7966a9b90f0901372`。唯一 user10 intent SHA256、实际响应/只读观察 SHA256、日结第2页截图 SHA256 和全部643表前后签名见 [脱敏机器证据](evidence/s10-p0-04/blocked.json) 与 [真实业务前后快照](evidence/s10-p0-04/business-before-after.json)。私有完整intent、CSRF、HTTP响应、截图与日志仅保存在权限700的 `.local/s10-p0-04/`及目标库目录，不上传。

目标库停机后与私有 `stopped-readonly.json` 完全相等。相较克隆初始仅11张表变动：`hr_employee`、`hr_version`、`mail_message`、`orm_signaling_default`、`res_device_log`、`res_partner`、`res_users`、`res_users_log`、`resource_resource`、`ydental_access_audit`、`ydental_access_session`。其中mail内部首次登录tracking+4、设备/登录/会话各+3、ORM信号+2，资产附件与filestore无新增；S01审计+13（登录/会话/切店各3、他店invoice_view 4），超上限并含非许可事件。close、refund、receipt、mutex、account、stock等均无改变。R3/P0-02/P0-03停止库再次只读核验全等，四库最终无活动连接。

## 预算与保全

| 动作 | 消耗/上限 |
|---|---:|
| CREATE | 1/1 |
| Odoo HTTP | 1/1 |
| Firefox | 1/1 |
| 无权 unlock9 POST | 1/2，仅user10 |
| 合法 unlock9 POST | 0/1 |
| refund_reject POST | 0/0 |
| 新收款、实际退款、贷项、出账、库存写、再日结 | 0/0 |
| Odoo upgrade/install/init/shell、sudo | 0/0 |

P0-04新库、R3/P0-02/P0-03旧库及filestore、日志、截图、intent、响应和全部失败证据原样保留；没有重试、换库、恢复P0-03预算或补做日结。产品addon、Odoo20 core、旧脚本与旧证据、Project/Issue状态均未修改，未部署、合并、强推或启动S11。S10整体技术与生产持续BLOCKED。本报告仅申请GPT独立复核已发生的真实Web有限事实、两个阻断和硬STOP；不申请P0-04整体PASS。
