# UAT-FIN-007｜财务解锁合成日结

- 所属阶段：U05；层级 L3；参与岗位：收费员、财务审批人。
- 真实权限：审批人需当前店 finance_approval write，进入页面需 settlement read，且在公司范围内。
- 需求／技术阶段：R21；S10-T15/16；准备状态 DATA_NOT_READY。

## 作用与核心行为

对一个经用户先前合成日结的最新周期作一次有据解锁，区分解锁与收款、退款。

## 页面与前置

`/ydental/settlement` 的收费员日结。使用 UAT-FIN-004 已完成的独立合成日结，先记录原 RUN、该门店、收费员、日期、方式和 Source trace 的周期。负责人确认该条是上述组合最新 confirmed 周期、允许用于本合成验证；无法确认时 BLOCKED。不得解锁历史受保护日结。

## 操作与预期

| 步骤 | 用户操作 | 可观察结果 |
|---|---|---|
| 1 | 财务审批人进入当前门店，找到对应日期、收费员和渠道的已确认日结。 | 唯一来源、状态及 Source trace 周期与准备记录一致。 |
| 2 | 展开该条“Unlock daily close with evidence”，填写合成财务解锁原因。 | 解锁表单只绑定该条日结；不具权限账号不显示该控件。 |
| 3 | 点击“财务解锁”一次。 | 返回后原记录状态显示已解锁；未知则停止并核原记录，不重复操作。 |
| 4 | 查看原条 Actual collections、实退及未终结退款暴露三项汇总快照，并与 FIN-004 原 RUN 中记录的三项比较。 | 三项汇总分别与原 RUN 相同；页面这里不是逐笔明细。解锁不等于修改原付款或自动再次日结。 |


## 异常、一次性提交及停止条件

只使用独立的新合成来源；相应动作产生持久记录。缺权限、对象、资格或合法配置时标记 BLOCKED，不借历史对象或改变规则。响应未知时立即停止，由负责人核查该原来源和结果，不重复提交；P0 停止受影响操作。实际用户结果初始 NOT_RUN。

## 结束条件与后续

登记本次 RUN 和可见结果；后续业务须以该来源的实际状态为前置，不重复生成相同来源。

## 源码与证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8`；仅 SOURCE 支持，不代表环境、用户或浏览器已验。
- [ydental_settlement/views/ydental_settlement_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_settlement/views/ydental_settlement_templates.xml)
- [ydental_settlement/controllers/settlement.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_settlement/controllers/settlement.py)
- [ydental_settlement/models/ydental_settlement_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_settlement/models/ydental_settlement_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-FIN-007-001`、`RUN-UAT-FIN-007-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

### 执行记录（复制本节以追加下一轮）

- RUN-ID：
- 测试日期：
- 实际产品版本：
- 测试环境标识：
- 实际岗位及门店：
- 合成业务对象逻辑标识：
- 浏览器及版本：
- CSS 视口宽度 × 高度：
- 浏览器缩放：
- 实际执行步骤及观察结果：
- 与预期是否一致：
- 用户验收结果：NOT_RUN（可选 NOT_RUN / PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 失败步骤及阻断下一项的原因：
- 关联问题 ID（可填写多个，例如 UAT-ISS-0001、UAT-ISS-0002）：
- 截图相对路径：
- 用户最终意见：
- 若为修复后复验，原问题 ID、原 RUN-ID、修复版本及复验结果：

### 问题记录（一个问题复制一份，可关联多个问题）

- 问题 ID（格式 `UAT-ISS-0001`，全套材料中唯一）：
- 对应用例及 RUN-ID：
- 发生页面和位置：
- 前置条件及合成对象：
- 首次发生的实际步骤：
- 预期与实际差异：
- 具体复现步骤（仅记录已安全观察到的事实）：
- 复现次数／是否稳定：
- 问题等级：P0 / P1 / P2 / P3（留空待定）：
- 分类：功能 / UI / 需求 / 环境（可多选）：
- 截图相对路径：
- 是否阻断下一项验收：

### UI/UX 意见（可按 RUN-ID 重复）

- RUN-ID、页面及位置：
- 桌面 / 平板 / 手机及实际视口、缩放：
- 信息布局：
- 操作流程：
- 字号与可读性：
- 间距、颜色和按钮：
- 桌面／平板／手机差异：
- UI 满意度：满意 / 基本可用但需优化 / 需要重新设计 / 不适用（留空待定）：
- 不满意原因及希望如何调整：
- 优先意见：必须修改 / 希望优化 / 可接受（留空待定）：
- 是否涉及需求变更：
- 截图相对路径：

本用例截图放在私有副本的 [截图目录](../images/UAT-FIN-007/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-FIN-007/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
