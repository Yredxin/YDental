# 店长与授权协调

当前环境 **ENVIRONMENT_NOT_READY**；所有用户用例初始 **NOT_RUN**。本岗位是业务体验身份，不是固定权限模板或自动授权。先由负责人核对实际账号、当前门店、允许公司范围、类别等级及业务前置；只用独立合成数据。

## 职责与门诊作用

协调本店人员、空间、排班、业务交接及文书责任，为各岗位准备可执行的门店范围。

## 真实权限及范围

当前店有效成员且具店长身份；人员授权按 ACC 规则，空间配置需 space write，排班容量需 capacity write，价目需 price write。文书转派的操作人自己须具本店 medical write，且为原负责人或本店店长；目标责任人须具 medical write、来源能力和资质。身份本身不替代上述其他业务类别。

16 个实际授权类别及等级说明参见 [岗位与权限矩阵](../../00-guide/role-permission-matrix.md)。业务能力、Odoo 组、门店成员关系与权限类别是不同条件，不能从岗位名互相推导。

## 推荐顺序与功能用例

按照列出的用例及其前置依赖顺序进行；跨岗位项只执行本账号承担的部分，其余交由有权人员完成。操作与原始结果只保存在对应的用例内。

[UAT-ACC-001](../../30-functions/access/cases/UAT-ACC-001.md) → [UAT-ACC-002](../../30-functions/access/cases/UAT-ACC-002.md) → [UAT-ACC-003](../../30-functions/access/cases/UAT-ACC-003.md) → [UAT-SPC-001](../../30-functions/space-scheduling/cases/UAT-SPC-001.md) → [UAT-SPC-002](../../30-functions/space-scheduling/cases/UAT-SPC-002.md) → [UAT-SCH-001](../../30-functions/space-scheduling/cases/UAT-SCH-001.md) → [UAT-SCH-002](../../30-functions/space-scheduling/cases/UAT-SCH-002.md) → [UAT-SCH-003](../../30-functions/space-scheduling/cases/UAT-SCH-003.md) → [UAT-INT-001](../../30-functions/intake-queue/cases/UAT-INT-001.md) → [UAT-TRT-003](../../30-functions/clinical-exam/cases/UAT-TRT-003.md)

每项先核各用例的页面、权限、数据和停止条件。观察桌面、平板、窄屏三档布局及实际浏览器、宽度、缩放，在原用例记录实际 UI 意见；不将不同岗位或设备的体验代填为 PASS。

## 参与的跨岗位场景

[新门店与员工准备](../../20-scenarios/01-store-staff/README.md) · [医生交接与文书责任](../../20-scenarios/07-document-handover/README.md) · [跨店与常见异常](../../20-scenarios/10-exceptions/README.md)

## 常见异常与限制

员工授权必须核范围；撤权旧页用例入口尚未固定，保持阻断；未确认文书责任不可因换人丢失。

任何持久提交结果不明、对象或权限不符、来源不能唯一识别时停止受影响动作，由环境负责人核对，切勿盲目重试。真实患者、资金、正式签署、外部通知与生产环境不在本资料制作授权内。

## 阶段记录入口

先在对应功能用例中填写实际结果，再在 [阶段完成登记](../../40-results/stage-status.md) 引用用例及问题编号；[问题汇总](../../40-results/issues.md) 和 [UI 意见](../../40-results/ui-feedback.md) 只索引原始记录。
