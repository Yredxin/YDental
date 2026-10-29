# 跨店、撤权、超时、库存不足及旧页异常

当前准备：**ENVIRONMENT_NOT_READY**。本页是流程导航；所有用户用例初始 NOT_RUN，用户结果只填写在各功能用例中。

**逻辑对象：** `SC10-ACCESS-A`、`SC10-QUEUE-A`，其余负例须单独分配对象。这些是未来分配的逻辑编号，并非数据库 ID；先按[合成对象映射](../../00-guide/scenario-data-map.md)由负责人核验实际对应与状态，再按[唯一执行清单](../../00-guide/execution-checklist.md)执行或接续。结果记录在唯一原始用例对应 RUN-ID；同一来源已执行动作只引用原记录，不重复提交。

**目的与价值：** 用独立合成对象识别权限和状态边界，并在无法安全复现时保留缺口。
**参与岗位与交接：** [集团管理](../../10-roles/group-admin/README.md) → [店长](../../10-roles/store-manager/README.md) → [前台](../../10-roles/front-desk/README.md) → [治疗医生](../../10-roles/treatment-doctor/README.md) → [检查医生](../../10-roles/exam-doctor/README.md) → [药房](../../10-roles/pharmacy/README.md) → [仓库](../../10-roles/warehouse/README.md)。箭头表示主要协作，并非授权或严格身份切换；各步骤以其岗位为准。
**前置准备：** 专门的合成账号、两个门店和可识别对象独立准备；不可改变历史责任或通过伪造身份制造异常。
**起始对象与终止状态：** 起始：指定合成对象与已记录正常状态；终止：记录实际拒绝或明确 BLOCKED，不声称预拦截等于产品拒绝。

| 步骤 | 承接岗位 | 流程动作 | 唯一功能用例 | 用户应观察 |
| --- | --- | --- | --- | --- |
| 1 | 授权者／测试人员 | 核查跨店、撤权和旧页边界 | [UAT-ACC-003](../../30-functions/access/cases/UAT-ACC-003.md) | 当前业务入口 ENTRY_UNKNOWN；未固定入口与权限时 BLOCKED，不执行撤权。 |
| 2 | 工位人员／前台 | 专用已报到任务按 QUE-001 步骤1–4 叫号后暂停，再执行过号 | [UAT-QUE-002](../../30-functions/intake-queue/cases/UAT-QUE-002.md) | 确认同一任务 calling 且未开始，再核状态及次数；不要执行 QUE-001 第5步或重复叫号、过号。 |
| 3 | 治疗医生／检查医生 | 审阅外检返回的超时与原持有人限制 | [UAT-EXM-002](../../30-functions/clinical-exam/cases/UAT-EXM-002.md) | 缺安全超时条件时 BLOCKED，不重放已发行医嘱。 |
| 4 | 药房／仓库 | 审阅库存不足与来源识别限制 | [UAT-PHA-002](../../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md) | 不足时停止发药；需要负例须另备专门合成对象且由负责人确认。 |

**一次性业务提交：** 撤权、过号、医嘱、发药都可能持久改变状态；本场景引用原用例，不让用户重复执行已经提交的业务。
**停止而非重放：** 遇数据、资金、临床安全或越权风险立即停止受影响动作；状态／提交不明、受保护对象、特殊环境缺失时停止并保留原始证据。

每步只在对应功能用例执行并记录。已提交的同一业务来源不得重放；若需验收另一独立支线，按用例前置准备不同的新合成对象，可再次执行该用例并分别记录。场景引用已有结果时只接续或查看，不重复提交。若指定用例前置不足，记录 BLOCKED。

**结束与后续：** 达到上方终止状态后，可进入 [下一场景](../01-store-staff/README.md)，或返回 [场景与手册总入口](../../README.md) 选择支线。

## 1.1 独立补充支线

[UAT-ACC-004](../../30-functions/rework-access-patient/cases/UAT-ACC-004.md) · [UAT-ACC-005](../../30-functions/rework-access-patient/cases/UAT-ACC-005.md) · [UAT-PAT-002](../../30-functions/rework-access-patient/cases/UAT-PAT-002.md) · [UAT-PAT-003](../../30-functions/rework-access-patient/cases/UAT-PAT-003.md)

以[执行清单](../../00-guide/execution-checklist.md)新增独立分支和[对象映射](../../00-guide/scenario-data-map.md)为准；仅接续已明确关联的原始 RUN，同一已提交来源不重放，数据未准备时停止。
