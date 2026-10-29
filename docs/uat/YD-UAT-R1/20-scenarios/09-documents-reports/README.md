# 文书、PDF、原件与经营报表

当前准备：**ENVIRONMENT_NOT_READY**。本页是流程导航；所有用户用例初始 NOT_RUN，用户结果只填写在各功能用例中。

**逻辑对象：** `SC09-DOC-A` 和已存在的 `SC06-BILL-A` 收款。这些是未来分配的逻辑编号，并非数据库 ID；先按[合成对象映射](../../00-guide/scenario-data-map.md)由负责人核验实际对应与状态，再按[唯一执行清单](../../00-guide/execution-checklist.md)执行或接续。结果记录在唯一原始用例对应 RUN-ID；同一来源已执行动作只引用原记录，不重复提交。

**目的与价值：** 将已确认来源以原件及报表追溯，区分可浏览 PDF 与真实出纸。
**参与岗位与交接：** [治疗医生](../../10-roles/treatment-doctor/README.md) → [经营报表](../../10-roles/report-user/README.md) → [收费](../../10-roles/cashier/README.md)。箭头表示主要协作，并非授权或严格身份切换；各步骤以其岗位为准。
**前置准备：** SC03-EXEC-C 的 TRT-001 C 已确认文书及原 RUN、合法来源读取权限、专用导出授权和场景06的合成收款已准备；禁止真实患者与正式票据。
**起始对象与终止状态：** 起始：新合成文书及收款；终止：原件、PDF请求、授权来源报表及导出可以对照；审计入口未定部分阻断。

| 步骤 | 承接岗位 | 流程动作 | 唯一功能用例 | 用户应观察 |
| --- | --- | --- | --- | --- |
| 1 | 治疗医生／授权文书使用者 | 生成并读取文书原件 | [UAT-DOC-001](../../30-functions/documents-reporting/cases/UAT-DOC-001.md) | 核对与 SC03-EXEC-C 原 RUN 的患者、已确认版本和保存原件；无 confirmed 版本或已有原件则停止，不重确认。生成是持久动作。 |
| 2 | 授权文书使用者 | 请求该原件打印 | [UAT-DOC-002](../../30-functions/documents-reporting/cases/UAT-DOC-002.md) | 浏览器收到PDF请求结果；不以此声称设备出纸。 |
| 3 | 经营报表／收费 | 查询与回源 | [UAT-RPT-001](../../30-functions/documents-reporting/cases/UAT-RPT-001.md) | 授权门店及来源与已知合成收款对应。 |
| 4 | 经营报表／授权导出人员 | 导出并按来源编号核对 | [UAT-RPT-002](../../30-functions/documents-reporting/cases/UAT-RPT-002.md) | 导出为重新查询；按来源模型及内部编号对照，审计入口未知部分BLOCKED。 |

**一次性业务提交：** 生成原件及打印请求产生对应记录；导出时不可重发费用或收款以制造报告。
**停止而非重放：** 原件、来源或门店不匹配，导出无法关联唯一来源、权限不足、提交结果未知时停止。

每步只在对应功能用例执行并记录。已提交的同一业务来源不得重放；若需验收另一独立支线，按用例前置准备不同的新合成对象，可再次执行该用例并分别记录。场景引用已有结果时只接续或查看，不重复提交。若指定用例前置不足，记录 BLOCKED。

**结束与后续：** 达到上方终止状态后，可进入 [下一场景](../10-exceptions/README.md)，或返回 [场景与手册总入口](../../README.md) 选择支线。

## 1.1 独立补充支线

[UAT-ACC-005](../../30-functions/rework-access-patient/cases/UAT-ACC-005.md) · [UAT-EVD-001](../../30-functions/rework-lab-evidence/cases/UAT-EVD-001.md)

以[执行清单](../../00-guide/execution-checklist.md)新增独立分支和[对象映射](../../00-guide/scenario-data-map.md)为准；仅接续已明确关联的原始 RUN，同一已提交来源不重放，数据未准备时停止。
