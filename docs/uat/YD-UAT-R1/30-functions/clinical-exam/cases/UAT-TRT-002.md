# UAT-TRT-002｜实际治疗项目及费库来源

- 所属阶段：U04
- 参与岗位：治疗医生
- 真实权限要求：当前门店 medical write；有效原医疗工位、接诊段和同患者文书及当前版本；服务能力、映射、价源及实际选用批次必须符合该门店合同。
- 对应需求／技术阶段及TC：R18、R19、R21；S08-T04/07、S07-T05、S10-T01
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；仅源码支持的拟验步骤，未部署、未实测、用户 NOT_RUN。

## 业务作用与核心行为

区分已保存文本和实际治疗事实；一次确认可产生费用与耗材来源，供后续结算和库存核对。

## 页面与前置条件

UAT-TRT-001 已保存同一新合成患者接诊文书，当前工位连接有效；环境负责人提供可售合成项目、已审核价源及充足的合成批次。项目、数量、牙位和是否耗材均按合成测试清单确定；无合法价源或批次则 BLOCKED，不补造事实。Treatment workbench 的 Actual treatment, orders and referrals 链接在新标签打开 `/ydental/treatment`。提交前须确认该标签具备原工位有效连接；若无法确认则 BLOCKED，不重复发起。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入 Treatment and pharmacy，核对门店、工位、患者及接诊段。 | 均与本次合成接诊匹配；无当前患者或写权限则停止。 |
| 2 | 阅读 Actual treatment confirmation 区域，选择约定 Project。 | 选择的是本店真实存在的服务映射；无目标项目则停止并登记环境缺口。 |
| 3 | 填写 Actual project quantity、FDI tooth 与 Verified tooth state；如需要，填写对应 surfaces。 | 字段与合成测试清单一致；牙位不适用使用 0 和 not applicable。 |
| 4 | 若清单指定模拟耗材，选择 Verified physical batch 并填写实际合成数量；不使用耗材则保持 No physical material used。 | 批次、数量和单位与准备清单一致；库存不足或批次不明停止。 |
| 5 | 填写 Actual reason / source evidence；确认页面没有已存在同次治疗来源。 | 可见事实与此次合成演练一致；不能将已有事实当新治疗重做。 |
| 6 | 点击 Confirm actual treatment 一次，阅读确认并按提示确认。 | 页面短暂提示后重载，在 Immutable actual events 区核对患者、项目、数量、来源及状态；若 pending，记录待核对原因而非视作已完成账务。响应未知则停止核查，不重试。 |
| 7 | 保留该来源供库存和结算用例读取。 | 治疗事实有独立来源；文书确认与本操作各自独立。 |

## 异常与权限负例

无 medical write、接诊或门店不匹配、失效连接、无匹配服务、库存不足或旧版本不得继续；未能确认提交先只读核查。负例不得拿历史业务重试。

## 一次性提交和停止条件

Confirm actual treatment 产生不可重放的治疗事实，可能同时产生费用和库存来源；响应未知或待核对立即停止，由负责人核对来源及状态，不重复点击或更换来源。

P0 数据、资金、临床安全或严重越权异常应停止受影响操作，保留事实并联系负责人；未确认提交时不重试。

## 结束条件及后续衔接

单次来源已登记并可供 UAT-INV-002、UAT-FIN-001 核对；结束患者接诊转 UAT-TRT-003。

## 源码依据与证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；源码不证明该环境已部署，也不等于用户验收或实际浏览器通过。
- [ydental_treatment/views/ydental_treatment_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/views/ydental_treatment_templates.xml)
- [ydental_treatment/controllers/treatment.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/controllers/treatment.py)
- [ydental_treatment/models/ydental_treatment_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/models/ydental_treatment_service.py)
- [ydental_inventory/models/ydental_inventory_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_inventory/models/ydental_inventory_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-TRT-002-001`、`RUN-UAT-TRT-002-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-TRT-002/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-TRT-002/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
