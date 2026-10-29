# 用户验收计划

## 目标与责任

由用户在独立合成测试环境中按真实岗位操作，记录实际行为、问题和 UI 意见；Codex 准备环境事实及 L4 技术证据，用户审阅，不代用户填写结果。参与者可同时承担多个岗位，但每一动作须由实际具有对应门店权限和资格的账号完成。[权限矩阵](role-permission-matrix.md) 与具体用例共同确定条件。当前环境 **ENVIRONMENT_NOT_READY**，以下均为计划，非已开始验收。

## 阶段登记分组及依赖

以下按各用例现有“所属阶段”归档，阶段编号是**登记分组，不是强制线性执行顺序**。每项必须先满足用例中的实际依赖；例如 U03 的 PHA-001 依赖 U04 的 TRT-001，U05 的 EXM 用例依赖 U04 医疗接诊，U05 结算依赖已确认费用。未满足时 BLOCKED，不能按编号强行执行。U00 环境准备未通过时其他操作不可开始。

| 登记阶段 | 该组固定用例 | 目标/限制 |
|---|---|---|
| U00 | [UAT-ACC-001](../30-functions/access/cases/UAT-ACC-001.md), [UAT-ACC-002](../30-functions/access/cases/UAT-ACC-002.md) | 环境、门店员工和授权准备；登录地址和账号仅私下提供。 |
| U01 | [UAT-ACC-003](../30-functions/access/cases/UAT-ACC-003.md), [UAT-INT-001](../30-functions/intake-queue/cases/UAT-INT-001.md), [UAT-PAT-001](../30-functions/intake-queue/cases/UAT-PAT-001.md), [UAT-INV-001](../30-functions/inventory-pharmacy/cases/UAT-INV-001.md), [UAT-SPC-001](../30-functions/space-scheduling/cases/UAT-SPC-001.md), [UAT-SPC-002](../30-functions/space-scheduling/cases/UAT-SPC-002.md) | 空间、患者、目录及库存前置；撤权旧页入口未知保持阻断。 |
| U02 | [UAT-INT-002](../30-functions/intake-queue/cases/UAT-INT-002.md), [UAT-INT-003](../30-functions/intake-queue/cases/UAT-INT-003.md), [UAT-SCH-001](../30-functions/space-scheduling/cases/UAT-SCH-001.md), [UAT-SCH-002](../30-functions/space-scheduling/cases/UAT-SCH-002.md), [UAT-SCH-003](../30-functions/space-scheduling/cases/UAT-SCH-003.md) | 排班容量、营业日及预约到店；依靠合法可售合成供给。 |
| U03 | [UAT-QUE-001](../30-functions/intake-queue/cases/UAT-QUE-001.md), [UAT-QUE-002](../30-functions/intake-queue/cases/UAT-QUE-002.md), [UAT-PHA-001](../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md) | 队列与处方；处方须先完成适用 U04 医疗前置。 |
| U04 | [UAT-TRT-001](../30-functions/clinical-exam/cases/UAT-TRT-001.md), [UAT-TRT-002](../30-functions/clinical-exam/cases/UAT-TRT-002.md), [UAT-TRT-003](../30-functions/clinical-exam/cases/UAT-TRT-003.md), [UAT-INV-002](../30-functions/inventory-pharmacy/cases/UAT-INV-002.md), [UAT-PHA-002](../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 医疗、文书、药房和库存来源；一次性动作按实际状态衔接。 |
| U05 | [UAT-EXM-001](../30-functions/clinical-exam/cases/UAT-EXM-001.md), [UAT-EXM-002](../30-functions/clinical-exam/cases/UAT-EXM-002.md), [UAT-FIN-001](../30-functions/settlement/cases/UAT-FIN-001.md), [UAT-FIN-002](../30-functions/settlement/cases/UAT-FIN-002.md), [UAT-FIN-003](../30-functions/settlement/cases/UAT-FIN-003.md), [UAT-FIN-004](../30-functions/settlement/cases/UAT-FIN-004.md) | 检查与结算；两者是不同流程，分别核 U04 来源及其用例前置。 |
| U06 | [UAT-DOC-001](../30-functions/documents-reporting/cases/UAT-DOC-001.md), [UAT-DOC-002](../30-functions/documents-reporting/cases/UAT-DOC-002.md), [UAT-RPT-001](../30-functions/documents-reporting/cases/UAT-RPT-001.md), [UAT-RPT-002](../30-functions/documents-reporting/cases/UAT-RPT-002.md), [UAT-FUP-001](../30-functions/followup-lab/cases/UAT-FUP-001.md), [UAT-FUP-002](../30-functions/followup-lab/cases/UAT-FUP-002.md), [UAT-LAB-001](../30-functions/followup-lab/cases/UAT-LAB-001.md), [UAT-LAB-002](../30-functions/followup-lab/cases/UAT-LAB-002.md) | 复诊、外加工、文书和报表；每项核真实来源与分权。 |
| U07 | 无；引用相关用例与专项证据 | 综合体验、异常与用户总结；无单独归属于 U07 的功能用例，按相关案例及 L4 证据记录。 |

[场景](../20-scenarios/01-store-staff/README.md)是业务导航，场景步骤链接到唯一功能用例；同一已提交来源不可重放。不同独立合成对象可按具体用例前置分别执行，使用已存在来源时先核状态。三档体验和异常应在实际所执行用例记录，不另造用户结果。

## 层级和结束条件

L1只读及操作体验，L2单岗位合成操作，L3跨岗位业务闭环，L4专项技术证据由Codex准备供用户审阅；不可把SOURCE、模型或历史技术结果当成浏览器、独立提交或用户 PASS。全部用例初始 NOT_RUN；按实际执行填写 PASS、PARTIAL、FAIL、BLOCKED 或 N/A 的理由。阶段结束需列出适用用例、结果、问题与未测原因；影响资金、数据、临床安全或严重权限的 P0 立即停止受影响操作。

最终用户结论须有各阶段记录、问题及复验引用，明确未验项和用户意见；技术 FAIL/UNKNOWN 不因用户偏好被抹去。用户可记录 PARTIAL 或未完成，不要求强行全通过。生产发布、正式政策及真实外部通道需要单独批准，用户验收完成不自动构成批准。
