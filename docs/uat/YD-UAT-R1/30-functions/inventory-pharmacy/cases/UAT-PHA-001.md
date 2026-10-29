# UAT-PHA-001｜医生开立并冻结合成处方

- 所属阶段：U03
- 参与岗位：治疗医生、前台
- 真实权限要求：当前门店 medical write，医生持有对应工位与正在服务的接诊、已保存当前版本的文书；报到需 frontdesk write。
- 对应需求／技术阶段及TC：R18、R20；S08-T07/08/13、S07-T05
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；前置不足为 BLOCKED，用户结果仍为 NOT_RUN。

## 业务作用与核心行为

为当前合成患者建立外带药处方，冻结后产生待明确报到的药房任务；开方不等于实际发药。

### 页面与前置

从 Clinical workbench 的 Actual treatment, orders and referrals 打开 Treatment and pharmacy（`/ydental/treatment`）。先完成 UAT-QUE-001 和 UAT-TRT-001，医生在本店持有有效工位及当前接诊，并保存当前文书版本。环境负责人提供同店有效药房服务映射、活跃合成药品、匹配单位与演示价格关联、可分两次发放的数量和合成用法；不可用真实药品/患者或历史处方。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 Treatment and pharmacy，核对门店、工位、患者与当前接诊。 | 页面显示约定合成患者和医生的当前接诊。 |
| 2 | 在 Examination or take-away prescription draft 选择 Take-away prescription，填合成目的。 | 显示处方草稿输入区。 |
| 3 | 选择精确药房服务、药品，输入批准总数量、规格、用法、频率和疗程。 | 药品和服务单位相符，四项说明均非空；数量按单位步长可拆成两次。 |
| 4 | 点击 Save order draft 一次。 | Frozen orders and remaining quantities 出现该患者的草稿、明细与版本；不出现实际发药事实。 |
| 5 | 核对草稿后在该处方点击 Issue and freeze order 一次。 | 该订单显示 Issued, frozen（已开立、冻结），显示对应药房 Segment 及 task，任务仍待明确报到；处方不再是可编辑草稿。 |
| 6 | 将该任务编号及患者交给前台，由 UAT-PHA-002 完成明确报到与药房处理。 | 不重复创建或冻结处方。 |

## 异常与权限负例

缺当前文书版本、药房映射、药品或一致单位时停止；无 medical write、跨店、旧版本不应开立。冻结不是正式临床签署，正式用药政策未批准。

## 一次性提交和停止条件

保存草稿和冻结均持久提交；冻结会创建药房任务。响应未知时先查现有订单与任务，不重新开方或换请求。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

记录已冻结处方及唯一药房任务，交 UAT-PHA-002；不得代替用户签署或实药。

## 源码依据与证据层级

固定产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明系统已部署、运行或用户验收通过。实际门店与账号准备后才可执行。

- [ydental_treatment/views/ydental_treatment_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/views/ydental_treatment_templates.xml)
- [ydental_treatment/controllers/treatment.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/controllers/treatment.py)
- [ydental_treatment/models/ydental_treatment_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/models/ydental_treatment_service.py)
- [ydental_queue/views/ydental_queue_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/views/ydental_queue_templates.xml)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-PHA-001-001`、`RUN-UAT-PHA-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-PHA-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-PHA-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
