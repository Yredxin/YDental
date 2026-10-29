# 前台

当前环境 **ENVIRONMENT_NOT_READY**；所有用户用例初始 **NOT_RUN**。本岗位是业务体验身份，不是固定权限模板或自动授权。先由负责人核对实际账号、当前门店、允许公司范围、类别等级及业务前置；只用独立合成数据。

## 职责与门诊作用

维护合成患者及预约资格，登记实际到店和任务报到，连接医生、检查与药房。

## 真实权限及范围

当前门店 frontdesk write 用于登记、报到；患者建档为 patient 或 frontdesk write。只读与临床背景有独立条件；追加叫号还需专门授权组。前台不因此获得 medical、exam、pharmacy 写权限；QUE-002 中前台只协助，过号操作须由持有对应工位且具 medical、exam 或 pharmacy write 的人员执行。

16 个实际授权类别及等级说明参见 [岗位与权限矩阵](../../00-guide/role-permission-matrix.md)。业务能力、Odoo 组、门店成员关系与权限类别是不同条件，不能从岗位名互相推导。

## 推荐顺序与功能用例

先按各用例的前置条件准备独立合成对象；以下是分支导航，并非把不同业务任务串成一次操作。跨岗位项只执行前台承担的部分，原始结果只记在对应的功能用例内。

- 患者和预约：先 [UAT-PAT-001](../../30-functions/intake-queue/cases/UAT-PAT-001.md)，再按前置进入 [UAT-INT-002](../../30-functions/intake-queue/cases/UAT-INT-002.md) 与 [UAT-INT-003](../../30-functions/intake-queue/cases/UAT-INT-003.md)。
- 检查衔接：[UAT-EXM-002](../../30-functions/clinical-exam/cases/UAT-EXM-002.md) 中仅对派生检查任务单独报到，不重复实际到店。
- 处方与药房：[UAT-PHA-001](../../30-functions/inventory-pharmacy/cases/UAT-PHA-001.md)、[UAT-PHA-002](../../30-functions/inventory-pharmacy/cases/UAT-PHA-002.md)，前台承担任务报到，医生和药房分别执行自己的动作。
- 无时段转诊：[UAT-FUP-002](../../30-functions/followup-lab/cases/UAT-FUP-002.md) 的目标店接收本身记录到店，不能再用 INT-003 重复登记到店。
- 过号异常：[UAT-QUE-002](../../30-functions/intake-queue/cases/UAT-QUE-002.md) 单独准备已叫号但尚未启动的合成任务；前台协助，过号由有权工位人员执行。

每项先核各用例的页面、权限、数据和停止条件。观察桌面、平板、窄屏三档布局及实际浏览器、宽度、缩放，在原用例记录实际 UI 意见；不将不同岗位或设备的体验代填为 PASS。

## 参与的跨岗位场景

[患者预约至报到叫号](../../20-scenarios/02-intake-queue/README.md) · [治疗、检查及返回](../../20-scenarios/04-exam-return/README.md) · [药房与分次发药](../../20-scenarios/05-pharmacy/README.md) · [复诊、转诊与外加工](../../20-scenarios/08-followup-lab/README.md) · [跨店与常见异常](../../20-scenarios/10-exceptions/README.md)

## 常见异常与限制

预约、到店、报到是不同动作。转诊接收已记录到店时不得再记一次；检查派生任务只做单独报到。

任何持久提交结果不明、对象或权限不符、来源不能唯一识别时停止受影响动作，由环境负责人核对，切勿盲目重试。真实患者、资金、正式签署、外部通知与生产环境不在本资料制作授权内。

## 阶段记录入口

先在对应功能用例中填写实际结果，再在 [阶段完成登记](../../40-results/stage-status.md) 引用用例及问题编号；[问题汇总](../../40-results/issues.md) 和 [UI 意见](../../40-results/ui-feedback.md) 只索引原始记录。
