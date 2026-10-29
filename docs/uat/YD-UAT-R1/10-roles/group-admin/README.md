# 集团管理

当前环境 **ENVIRONMENT_NOT_READY**；所有用户用例初始 **NOT_RUN**。本岗位是业务体验身份，不是固定权限模板或自动授权。先由负责人核对实际账号、当前门店、允许公司范围、类别等级及业务前置；只用独立合成数据。

## 职责与门诊作用

维护授权范围内的组织、权限模板和集团公共资料，为门店准备合成测试资源。

## 真实权限及范围

集团管理员组、内部用户会话和允许公司范围；建店、模板管理与公共资源另按用例限定。业务页面仍需各自类别与范围，集团组不等于全业务写权限。

16 个实际授权类别及等级说明参见 [岗位与权限矩阵](../../00-guide/role-permission-matrix.md)。业务能力、Odoo 组、门店成员关系与权限类别是不同条件，不能从岗位名互相推导。

## 推荐顺序与功能用例

按照列出的用例及其前置依赖顺序进行；跨岗位项只执行本账号承担的部分，其余交由有权人员完成。操作与原始结果只保存在对应的用例内。

[UAT-ACC-001](../../30-functions/access/cases/UAT-ACC-001.md) → [UAT-ACC-002](../../30-functions/access/cases/UAT-ACC-002.md) → [UAT-SPC-002](../../30-functions/space-scheduling/cases/UAT-SPC-002.md) → [UAT-INT-001](../../30-functions/intake-queue/cases/UAT-INT-001.md) → [UAT-LAB-001](../../30-functions/followup-lab/cases/UAT-LAB-001.md)

每项先核各用例的页面、权限、数据和停止条件。观察桌面、平板、窄屏三档布局及实际浏览器、宽度、缩放，在原用例记录实际 UI 意见；不将不同岗位或设备的体验代填为 PASS。

## 参与的跨岗位场景

[新门店与员工准备](../../20-scenarios/01-store-staff/README.md) · [复诊、转诊与外加工](../../20-scenarios/08-followup-lab/README.md) · [跨店与常见异常](../../20-scenarios/10-exceptions/README.md)

## 常见异常与限制

权限模板替换可能将缺项降为 none；创建账号前由负责人核对登录名全局未占用。

任何持久提交结果不明、对象或权限不符、来源不能唯一识别时停止受影响动作，由环境负责人核对，切勿盲目重试。真实患者、资金、正式签署、外部通知与生产环境不在本资料制作授权内。

## 阶段记录入口

先在对应功能用例中填写实际结果，再在 [阶段完成登记](../../40-results/stage-status.md) 引用用例及问题编号；[问题汇总](../../40-results/issues.md) 和 [UI 意见](../../40-results/ui-feedback.md) 只索引原始记录。
