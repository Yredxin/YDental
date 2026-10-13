# S09 BLOCKED 技术复核报告｜YD-N1 R1｜2026-10-13

## 1. 任务、授权、基线与实际环境

唯一授权为 [#33 GPT-ACTIVATE 6141057408](https://github.com/Yredxin/YDental/issues/33#issuecomment-6141057408)；已读取 #23/#33 当前正文及全部有效评论，核对 #32 技术 PASS 6140703673 与状态同步 6140901633、复核 6140955734。开工回执 [6141225307](https://github.com/Yredxin/YDental/issues/33#issuecomment-6141225307) 已发布并逐字读回。此报告是 Codex 自测，不代表 GPT 亲测或用户效果验收。

| 项 | 实际值 |
| --- | --- |
| 固定基线 | `42788593474f309b4bd17d7dd0aed85966b6e484` |
| 分支 | `codex/s09-exam-workbench-r1-20261013`，由固定基线新建 |
| S09 product | `85e465cd55f9d4c03b195795f2f9c4e7178b07a7` |
| S09 test / runner | `d1fdaec7e2751068f69c7f8f75b8d0782af5d18c`；仅测试脚本与隔离 runner，不构成固定全量 PASS |
| final | 以 #33 本批 BLOCKED 评论记录的完整 SHA 为准 |
| Odoo | Community 20.0；核心 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，未修改 |
| Python / PostgreSQL | 项目 venv 3.12.15；PG 18.6，cluster `7694897083368259627`，Docker `odoo20-db` 原卷未变 |
| 新隔离库 | `ydental_s09_test_20261013082800_a1b2c3d4`，OID `1403489`，专属端口 `18190`，原生产开发 Odoo 8069 健康 200 |

Project #4 开工前后各两次完整读回 21 字段/选项、37 项（15 当前+22 归档）及值、6 视图与可见字段数 `9/9/5/3/7/3`、7 公开 workflow。唯一 mutation 是 #33 自定义执行状态 `待启用/441473f3`→`进行中/57b99552`，前后逐叶差异仅同一字段 `name/optionId`。#33 保持 OPEN/Todo/S09，#32 保持待用户验收，#34—#37 待启用。Project 的首次前读与两次后读原件留 `.local/s09-project-start/`；临时脚本重用文件名覆盖了第二次前读原文件，**先前已执行的双读深比较结果存在，但该份原响应不能再提供独立原文件哈希**。本限制记录在 [project-start.json](evidence/s09/project-start.json)；不声称私有 workflow 内部规则可见。

## 2. 需求完成情况与当前源码合同

product 新增 `ydental_exam` 独立 addon，依赖真实 S08-C 堆栈：检查结果、不可普通改写的版本、资质有效期、幂等 receipt、真实医嘱行绑定、受控演示 PDF、HTTP 工作台。S08-B 的 `_start` 保留未安装 S09 时 `exam_integration_required`，只新增默认拒绝的上层钩子；安装态的上层检查绑定冻结行、真实任务、患者、门店及 S06 叫号。S08-B 原库存来源校验仅补 `exam` 事件类别识别，仍沿原 S07 原生批次/流水和 S08 费源。没有新增患者队列、可改库存余额或财务账本。

| 要求 | 当前结果 | 证据与限制 |
| --- | --- | --- |
| 真工位/技师、全景和 CBCT 分开叫号 | 候选实现，未完成固定验证 | S06 原 `_service_eligibility` 与 S09 `_exam_start_authorized`；首候选仅走过一条全景路径，双机与跨能力竞争未测 |
| 冻结行、真实开始、独立结果/版本/附件、逐项状态 | 候选实现，未完成固定验证 | `ydental_exam/models/`；第二次探针走到 PDF，但断言失败且事务回滚 |
| 执行价/费源/适用耗材 | 候选实现，未完成固定验证 | 复用 S08 `_event/_quote/_settle`；第二次探针的 `state==confirmed && amount==80` 断言 FAIL，真实差异值因旧脚本未打印而 UNKNOWN；没有冒称费用正确 |
| 保留、交还、部分返回、跨日续检、唯一后继 | BLOCKED | S06/S08 上游合同保留，S09 全场景未重放；不能用上游旧 PASS 代替本批 |
| 中文 PDF、下载、权限、审计 | 候选实现，未完成固定验证 | 第二次探针 Odoo 记录 PDF 生成，随后整体断言 FAIL；未做二进制中文抽取、逐页目视或权限负向；无正式签发 |
| 正式模板、设备/PACS、S12原件、S10结算、生产 | NOT_RUN / 未授权 | 不作为本批 PASS |

当前产品代码仍含未实测路径，不能视为完整工程交付。尤其无固定版本的 HTTP/Firefox、实际双 PG backend、跨日、附件越权和已提交费库签名证据；中文 PO 未完成，安装日志明确 `ydental_exam: no translation for language zh_CN`。正式医疗字段、模板审阅、签发、生产取价政策仍待业务负责人决定，不能默认填“正常”或冒称设备连接。

### 字段与动作草案，需返工验证

| 对象 | 原来源及字段 | 控制 |
| --- | --- | --- |
| `ydental.treatment.line` | 已冻结 exam 订单、真实 task、mapping/capability、患者、门店、原医嘱作者、数量/原生单位 | 原订单不可追加/删已做；S09 增 `aborted/partial` 状态，未安装仍拒绝 exam start |
| `ydental.exam.qualification` | 用户、门店、准确代码、有效期、审核依据、撤销标记 | 人事授权入口；没有真实资质记录时非空资格要求拒绝 |
| `ydental.exam.result` | 唯一行、原作者、模板版本、当前结果状态、真实 execution/event、编辑会话/CAS、工位/门店日 | 草稿不等于实际执行；`event` 有唯一源 `s09-exam-line-ID` |
| `ydental.exam.version` | 结果号、版本号、草稿/确认/更正、作者、原因、UTC、前版 | 追加版本；结论不自动生成；当前演示测量仅值/单位/未知/不适用 |
| `ydental.exam.receipt` | actor+key 唯一、请求指纹、结果 | 重试幂等；未知提交须查原源 |
| S08 event/fee/S07 move | 真实检查 event→S05 原时间快照→fee；耗材行才触发原生库存源 | 缺价/缺料的 pending 与核对路径未被固定验证，不能宣称恢复已成功 |

候选动作允许：`draft` 保存独立文字，`perform` 明确真实实施，`confirm` 确认文字，`correct` 追加更正，`abort` 记实际中止/部分完成，`finish` 结束检查段，`reconcile` 核对原事件；`grant_qualification` 为有据人事资质。服务端使用 S01→S04→S03→S05→S06→S07→S08→S09 的既有锁序与私有守卫；实际并发正确性 **NOT_RUN**。报告只写“演示/未审核签发”，报告/附件路由分别要求源读取和 export-write；安全负向未测。

## 3. F1—F4 真实流程回放

| 流程 | 实际结果 | 原始状态、队列、费库、结果证据 |
| --- | --- | --- |
| F1 全景+CBCT | **FAIL 候选；无提交成功** | 第二次探针曾建立冻结双行、交还医疗段、仅报告并叫起全景、保存草稿/真实执行/确认并调用 PDF；随后 `state==confirmed && amount==80` 断言失败，事务回滚。失败时脚本未打印实际值，故价格/事件状态 UNKNOWN。第三次探针在 registry 初始化即 native SIGSEGV，未进入业务脚本。只读 SQL 确认相关检查结果/事件/费源/执行各 0。CBCT 未独立受理验证。 |
| F2 保留+检查/恢复竞争 | NOT_RUN/BLOCKED | 未跑 hold→全景→CBCT waiting→query_return/restore 或 serving 拒绝；不能借旧 S06 结果。 |
| F3 交还+部分返回 | NOT_RUN/BLOCKED | 候选只走到 D1 handover 与全景单线；D2 根管续诊、共享结果、未做 CBCT 决策未核。 |
| F4 昨日/今日 | NOT_RUN/BLOCKED | 00:00/00:10、今日重新受理、旧结果更正及费源签名未核。 |

无 Firefox 截图，无可交付 PDF 二进制或逐页中文目视结论；第二次探针生成 PDF 后事务失败不构成报告验收。所有合成失败库、原始日志及 SHA 保留，本次不删除/重置。

## 4. S09-T01—T13 逐项状态

| TC | 本批状态 | 实际依据与缺口 |
| --- | --- | --- |
| T01 | NOT_RUN/BLOCKED | 全景候选单机曾叫起；双全景不同 backend/CBCT错叫未测 |
| T02 | NOT_RUN/BLOCKED | 内嵌医疗 serving、草稿经济零副作用未测 |
| T03 | NOT_RUN/BLOCKED | 医生 hold 与技师独立编辑未测 |
| T04 | NOT_RUN/BLOCKED | 部分结果回传/多单后继唯一未测 |
| T05 | NOT_RUN/BLOCKED | 取消 vs 开始双连接、中止事实未测 |
| T06 | NOT_RUN/BLOCKED | 已签原单增删拒绝和新单增项未测 |
| T07 | NOT_RUN/BLOCKED | restore vs 开始互斥未测 |
| T08 | NOT_RUN/BLOCKED | 跨日/00:10清理未测 |
| T09 | NOT_RUN/BLOCKED | 重传、更正、执行源唯一和经济签名未测 |
| T10 | NOT_RUN/BLOCKED | PDF 候选生成，权限/中文/逐页和附件负向未测 |
| T11 | **BLOCKED** | 新库 product 安装 exit0、64模块；upgrade、带真实业务再 upgrade、S08 A/B/C 回归与未装 S09 fail-close 隔离回归均 NOT_RUN |
| T12 | NOT_RUN/BLOCKED | D1 下班、D2 根管资格、部分结果未测 |
| T13 | NOT_RUN/BLOCKED | 字典/翻译、调价不改旧快照、查看/更正审计矩阵未测 |

没有任何 S09 TC 可以报告为全项 PASS。静态 `compileall`、XML parse、`git diff --check` 通过；它们不能替代实测。尚无独立 `ydental_exam_test` addon、无固定 test SHA 完整安装/升级/HTTP/Firefox/翻译/真实并发回归；test commit 只保存本次隔离 runner/失败复现入口。

## 5. 原生崩溃、失败链和安全停止

详见 [native-crash.json](evidence/s09/native-crash.json)。首次新库安装 PID1790263 exit0、日志 SHA `316ca186…`；首次探针 PID1791592 exit1，合成夹具在未装测试 adapter 的演示容量政策下被 S03 正确拒绝；第二探针 PID1792160 exit1，走到原生 PDF 后 F1 价格/状态断言失败；第三探针 PID**1792405**、`PYTHONFAULTHANDLER=1`，Odoo registry 初始化期间 **SIGSEGV**，native exit **-11**、runner外层 **245**，日志 SHA `761e3cd6bfda2aef894fd7c413e532c28fcc853aa89b054452db4995b6132daf`。Python 栈为 garbage-collecting→`contextlib.__exit__`→`odoo/orm/registry.py:176`；没有可用 native 栈、core 软限 0、未见 apport 包，**根因 UNKNOWN**。没有证据把它归因于本批业务代码、旧 S07/S08-C 故障或某个扩展。按授权自此停止所有 Odoo/Firefox/数据库重跑；runner 新增 crash marker 拒绝后续 S09 动作。

崩溃后仅只读 SQL/环境：PG cluster 与OID未变；`ydental_exam_result/version/receipt`、`ydental_treatment_event/fee`、`ydental_queue_execution` 均 0，deadlock0；`odoo20-db` 健康、原 Odoo8069 返回200；共享内存 256MiB 总/约93MiB 使用；odoo12容器未动。崩溃取证仅定位 Python 运行阶段，**不是内存破坏根因证明**。生产部署继续 BLOCKED。

## 6. 用户效果验证与权限

本批仅有候选服务端动作，没有真实 Firefox 界面操作/截图或用户观感验收。初版工作台入口 `/ydental/exam` 与原 `/ydental/queue`、`/ydental/treatment` 相连，待复核恢复后需按用户路线逐步测试：开全景+CBCT→选全景报到→合格技师叫号/保存结果→部分返回→CBCT继续或附因取消/另开→次日续做→受控下载。当前不能声称其中任一步已由固定版本 Firefox PASS。

服务端权限设计仍待攻击性验证：exam-write 不应带来 medical-write/price/warehouse 权；medical 只允许当前合法接诊目的读；export-write+源读取才能下载；附件 ID、报告 ID、跨店、撤权旧页、旧版本和伪造 RPC 均须负向通过。现有代码 `sudo` 仅在已核对 store/患者/行后取源与创建不可普通改写记录，但此断言需真实 HTTP/RPC 审计，不能自称安全 PASS。

## 7. 数据、迁移、回滚和遗留风险

只新增一座隔离合成 S09 库；旧库、原 S08 分支与提交、原始失败日志/图/PDF均保留。没有更改 PG/Odoo 服务配置、卷、Odoo20 核心、odoo12，也没有生产迁移。product 新表安装成功，但已有业务升级和升级前后 SQL 签名 **NOT_RUN**。失败探针事务回滚后的业务表计数为零；候选安装/序列与原始日志留在 `.local/ydental_s09_test_20261013082800_a1b2c3d4/`，不删除。

若未来获准诊断：先分层确认新的 SIGSEGV 在 registry 初始化的可重复性、Python/native 栈与 core 收集的可行性；处理第二探针未捕获的实际价格/状态差异；再以**新库和新的固定版本**完整做安装/升级/带业务再次升级、真实并发、HTTP、Firefox、翻译、PDF逐页、权限审计和上游回归。不可把本次 product 安装 exit0 或旧阶段 PASS 拼成新阶段技术 PASS。真实已做医疗/库存一旦将来提交，应恢复原事实而不是回滚为“未做”；历史库绝不覆盖。

## 8. 复核申请与停止

请求 GPT 对 native SIGSEGV 证据、第二探针业务断言 FAIL、候选产品边界及下一轮诊断/修正范围做独立技术复核。**S09 当前 BLOCKED**，无完整开发/测试交付，S10不启动；#33保持 OPEN/Todo/进行中，不自行转待用户验收，不合并/强推/生产部署。#33发布本批 `[CODEX] S09 BLOCKED与技术复核申请` 后逐字读回并立即停止。
