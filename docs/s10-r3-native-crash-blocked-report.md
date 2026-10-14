# S10 定向返工：新原生 SIGSEGV，持续 BLOCKED

## 1. 任务、授权和固定版本

依据 [#34 GPT-REVIEW/AUTHORIZE 6158230350](https://github.com/Yredxin/YDental/issues/34#issuecomment-6158230350)；已读取 #23/#34 当前正文与全部有效评论，并注意到其后 GPT 直接提交的 [候选交接 6158453170](https://github.com/Yredxin/YDental/issues/34#issuecomment-6158453170)。从用户给定 `d99f27fffcd6f9b79f1b1ac271dd026493b826b6` 沿原分支 `codex/s10-settlement-finance-r1-20261013` 快进，没有改写历史。GPT 未实测的候选 final `0804ff36142cad8c301996c1747276d5a08d9dd5` 后，补充了日结截点与中文翻译；本批最后产品提交 `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`，固定测试提交 `255b48f54495eb99638af8ffc824771b9a5af3e7`。本报告及证据属 final 提交，SHA 以 #34 回执为准。product→test 仅 `scripts/`，test→final 仅文档/证据/AGENTS。

**新 SIGSEGV 已触发授权停止条件。S10 持续 BLOCKED；本批不申请技术 PASS。**

## 2. 需求完成情况

| 功能 | 状态 | 固定版本的实际范围与限制 |
|---|---|---|
| 跨日退款日结 | 部分 | 用真实收款昨日、实际退款今日、另一真人执行、门店当地日和微信渠道回放；历史已确认日结实退仍为 0，今日真实退款 100，原生 outbound 对应今日。`_close` 截点改用带微秒 UTC，避免同秒新已退被误算在途。并发组因新崩溃未通过。 |
| 收款方式更正后退款 | 部分 | 现金误录更正微信，原生重分类凭证已过账；实退 100 原生 journal=微信而非原现金。更正前款项未覆写。跨渠道支付政策仍需生产批准。 |
| 旧退款/日结分页 | 部分 | 55 条申请、55 个日结及 59 笔付款后，旧记录在服务端分页可查；固定库 Firefox 第 2 页操作因新崩溃未执行。 |
| 真实费用、出账、核销、库存和跨法人交易 | 部分 | 固定库已执行治疗/检查/药房 4+2、740/500/240、旧 270+新 200/300=270+30、仅选新账、跨法人原生销售/采购/凭证/收发；固定双后端首组在业务动作前崩溃。 |
| 零元账单、退款状态、实物更正、审计、权限 | 部分 | 固定库单进程模型流程 exit0，生成零元 posted 账无假 payment，双人真实退款、失败/未知恢复、药品隔离退库、六类角色及来源审计负向；并发审批、真实浏览器和完整回归未通过。 |
| 中文 PDF/翻译 | 部分 | 固定库生成账单、小票、四种退款状态 PDF，逐份可读单页且提取到中文；未在固定库完成逐页视觉与 Firefox 下载。`zh_CN.po` 导出 373 项均有译文、安装载入 `zh_CN`，运行时完整覆盖验收未完成。 |

产品位置：`ydental_settlement/models/ydental_settlement_service.py`、退款/日结模型、controller、QWeb 与 `i18n/zh_CN.po`。合成演示科目和人工线下收退款仅用于隔离库，不表示银行、微信接口自动到账。

## 3. 流程实际回放与原生 SQL

固定库 `ydental_s10_test_20261014020300_8b6c1d4e`，OID **2056451**，端口 **18247**，PG cluster `7694897083368259627`，config SHA256 `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`，Odoo20 core SHA `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。库、原始配置、filestore、日志和事故 marker 全部保留。

| 合成流程 | 已提交的原生事实 | 固定库只读结果 |
|---|---|---|
| F1 治疗 600 + 检查 80 + 同处方先发 4 后发 2，药费 40+20 | posted invoice 1=740；原生付款 500/240，partial 1/2=500/240；两笔药房 S07 done move | invoice 1 余额 0；真实发药事件/费源各 2，无第 7 份 |
| F5 旧 270 + 新 200，付 300 | 旧 invoice 4、新 invoice 6 独立；原生 partial 4/5=270/30；仅选新账另付 200 仅核 invoice 7 | 原账 0；新账后续其他合法付款/退款测试后的余额 165；未选旧账的独立场景未核旧 |
| 跨日退款与更正 | 昨日现金标签更正微信，昨日确认的日结实退 0；另一收费员今日执行微信 100，原生 outbound journal 13，状态 reconciled | 原实际退款日为 2026-10-14，channel=wechat，executor=15；历史确认快照未追溯改写 |
| T09 | 两法人 sale.order=1、purchase.order=1、双方 posted 凭证和 done 收/发 | trade 1 的销售凭证 88/company1、采购凭证 89/company2；库存双 move done |

崩溃后**只读** PostgreSQL：226 event、225 fee、17 settlement source、66 实际线下收款、66 退款、63 日结、1 trade；93 `account.move`、70 `account.payment`、73 `account.partial.reconcile` 合计 2621、238 `stock.move` done。source 缺 posted/公司不符 0、重复 fee source 0、`pg_stat_database.deadlocks=0`。已退退款 4 件均有原生付款来源；账与库具体 ID、金额、journal、状态、SQL 计数见 [机器证据](evidence/s10-r3-blocked/incident.json)。这些单进程已提交业务事实不等于并发或全阶段通过。

## 4. 测试结果：S10-F1—F6、T01—T16

固定 SHA 下 `create` exit0；`install` PID2380553 exit0；首次 `upgrade` PID2381168 exit0；26 个真实业务 shell PID/命令/日志哈希逐条固定，均 exit0。首组双 PostgreSQL 后端出账竞争：PID2383729 因守卫收到 SIGINT，exit -2；PID2383730 **SIGSEGV，exit -11**。`--no-http` shell 在 registry loaded 后、脚本业务动作前崩溃，Python 栈停在 ORM `field_computed`/`res.users.context_get`；根因 UNKNOWN，不能归因于 S10 产品、Python 或某扩展。没有继续其余并发、持久业务再次 upgrade、固定 Firefox。

| 项 | 状态 | 固定库已覆盖／阻断 |
|---|---|---|
| F1 | BLOCKED | 740 与 500+240 单进程原生链通过；同源双后端固定组遇 SIGSEGV。 |
| F2 | BLOCKED | 双人申请/批准/实际退款、驳回、未知、失败恢复单进程通过；同退款双审批者固定竞态未运行。 |
| F3 | BLOCKED | 跨日日结、更正、补录和锁的单进程通过；日结与退款/重分类固定竞态未运行。 |
| F4 | BLOCKED | 临床、检查、4+2 发药、费库账以及更正单进程通过；固定库完整上游模型/HTTP 回归未结束。 |
| F5 | BLOCKED | 不同业务日 270+200/300=270+30、仅选新账和同日 ID 单进程通过；并发与浏览器未完成。 |
| F6 | BLOCKED | 权限矩阵与跨店最小欠款摘要、代收拒绝的模型测试通过；固定 Firefox 未运行。 |
| T01 | BLOCKED | 首组双后端在脚本动作前发生新 SIGSEGV；本轮不能用旧 SHA 的竞争 PASS。 |
| T02 | PASS（限定模型路径） | 740/500/240 的原生账、款、partial 与重复 key 通过。 |
| T03 | PASS（限定模型路径） | 零元 posted invoice，无假付款；负值/超额折扣拒绝。 |
| T04 | BLOCKED | 自批拒、退款额度保护单进程通过；双审批者与额度并发未运行。 |
| T05 | PARTIAL | unknown/failed/恢复与实际退款、完成后同 key 重试模型通过；响应丢失的真实 HTTP 路径未全验。 |
| T06 | PASS（限定模型路径） | 未收免单原生贷项，收退款均 0。 |
| T07 | BLOCKED | 日结锁、财务解锁、方式更正、重结模型通过；与退款/重分类竞争未运行。 |
| T08 | PARTIAL | 文书文字更正、实际项目冲正、药品真实隔离库存分别通过；完整同接诊上游回归未完。 |
| T09 | PARTIAL | 两法人原生正例、同法人调拨、缺料/公司批次/过期/库存故障负向通过；异币种和并发订单未完。 |
| T10 | PARTIAL | 六角色工作台/PDF/收款拒绝和跨店摘要通过；撤权旧页、合并患者、附件/原生 RPC 未全验。 |
| T11 | PARTIAL | 账单/小票及 approved/unknown/rejected/done 真 PDF 各一页，中文字可提取；固定库视觉逐页与 Firefox 下载未完成。 |
| T12 | BLOCKED | 安装、首次升级、真实 S09 检查模型/PDF 通过；带已提交业务再次升级及完整 S08/S09 HTTP 回归因崩溃未运行。 |
| T13 | PASS（限定模型路径） | 270+30 原生核销、仅选新账不核旧、超额/跨店拒绝。 |
| T14 | BLOCKED | 角色服务端鉴权及摘要模型通过；固定 Firefox 多角色按钮和旧页未运行。 |
| T15 | PARTIAL | 已确认 600 后调价 620 仍按 600、文字与实际更正不覆写原单，驳回无贷项；同源重印视觉未完。 |
| T16 | BLOCKED | 锁后补录双时间、财务解锁和普通用户篡改负向模型通过；并发及固定浏览器未运行。 |

## 5. 字段、动作、配置与事故保护

退款保留请求/批准/未知/失败/撤销/完成分态；实际退款记录执行日、执行人和更正后的渠道，原收款与确认日结不回填。工作台 payments/refunds/closes 分别分页，门店与患者授权先过滤。`_close` 截点取精确 UTC 微秒以区分同秒实际已执行退款。中文 PO 是合成演示文本，不构成生产财务/税务政策批准。

事故日志 SHA256 `f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`，守卫 marker SHA256 `d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78`。`/proc/sys/kernel/core_pattern` 指向 apport；未见该 PID core，`coredumpctl` 不可用、内核 journal 窗口无条目。不能据此给出 native 根因。崩溃后 Odoo/Firefox 子进程 **0 次**；仅保留原常驻 Odoo PID42433，不修改其环境。无 Project 写入、旧库删除、Odoo20 核心、odoo-12、volume 或生产操作。

## 6. 用户效果与失败历史

旧基线缺陷在独立隔离库以真实 SQL/负向流程复现：跨日实际退款曾回写历史日结，现金更正微信后退款仍使用现金 journal，旧分页记录消失；原失败库和日志保留。GPT GitHub 候选库 OID1969080 的日结同秒边界测试失败，修复截点后候选库 OID2012598 通过；其 PASS 不移作固定库验收。固定前库 OID2034523 的 Firefox 第一次因预览进程缺 `wkhtmltopdf` 路径在首张 PDF 下载失败；修正预览环境后实际浏览器下载账单 PDF HTTP200，但旧 receipt locator 诊断超时，该库及日志保留。固定库原计划在所有按钮、三类 PDF 下载和分页操作后完成并发、二次升级；新 SIGSEGV 触发后均停止，未生成固定 Firefox PASS。

旧 OID1947350/1969080/1990861/2012598/2034523、当前 OID2056451 与更早所有合成库及失败材料未删除。固定库 PDF 八份各一页、中文提取计数/字节哈希见机器证据；这只是字节与文本验证，**不冒称逐页目视**。用户侧入口和完整按钮仍待新 native 诊断授权后再做。

## 7. 数据、审计、回滚和保全

当前库业务数据已提交且只读，不能用本次崩溃后的新库重跑拼接 PASS。保全 `.local/ydental_s10_test_20261014020300_8b6c1d4e` 原日志/marker/config/filestore/PDF，提交脱敏 [incident.json](evidence/s10-r3-blocked/incident.json) 与只读 SQL 脚本。最后产品/测试源码均已固定；回退为不部署、不合并该独立分支，合成库继续保留待复核。原 native SIGSEGV 根因与生产科目、税、凭证及支付政策仍未知或未批。

## 8. 技术复核申请与停止

申请 GPT 复核新 PID2383730 SIGSEGV 事故、已完成的单进程财务修正及继续恢复的安全边界。根据 #34 授权，**不得再运行 Odoo/Firefox 完成余项**；S10 保持 BLOCKED，#34 继续 OPEN/进行中/Todo，不启动 S11、不合并、不强推、不生产部署。#34 回执发布并逐字读回后立即停止。
