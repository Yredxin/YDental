# UAT-FUP-001｜创建复诊计划与记录模拟联络

- 所属阶段：U06
- 参与岗位：复诊联络
- 真实权限要求：本店 followup write；创建还须本店 medical read，患者当前门店关系有效。
- 对应需求／技术阶段及适用 TC：R08、R23；S11-T01–06
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；下述为源码依据，尚未实际部署或用户验收。

## 业务作用与核心行为

由已确认的实际治疗来源建立复诊计划，并区分联络记录、预约、到店与治疗完成。

## 页面与前置条件

进入 Follow-ups → Follow-up workbench（`/ydental/followups`）。环境负责人先准备独立合成门店、合成患者和该患者一条本店 confirmed 治疗事件；事件须为 confirmed treatment 且所属执行段为 reserved、handover 或 interrupted，并在页面 Confirmed treatment event 选项中显示该患者及事件号；选项找不到则 BLOCKED，不重做 TRT-002 来源。通知策略关闭或仅使用经批准的隔离测试接收器；真实电话、短信、邮件和外部通知未授权。当前用户是本店合格负责人。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入工作台，查看顶部 Store。 | 显示准备好的合成门店。 |
| 2 | 展开 Create follow-up from an actual treatment event，选择患者和相同患者的 confirmed 事件，记录事件号。 | 患者与事件选项中的姓名一致；不匹配时停止。 |
| 3 | 选 Post-visit，填写未来 Planned at，Deadline 留空或不早于计划时间。 | 输入的日期时间符合门店时区及前置要求。 |
| 4 | 点击 Create plan 一次。 | 返回工作台；在患者行看到类型、计划时间、责任人及状态；记录此行，不能仅凭跳转认定唯一提交。 |
| 5 | 在该行展开 Record contact，方法选 Other、结果选 Unknown，备注写“合成测试，无实际联系”，点 Save contact result 一次。 | Contact history 出现该次合成记录；状态需重新查看，不能把 Unknown 当已送达。 |
| 6 | 查看该行 Appointment 和 Appointment status。 | 未关联预约时不能据此认定已预约、到店或治疗完成；预约由前台用例单独创建。 |

## 异常与权限负例

无 followup write 的账号不应出现写入控件；无 medical read 不可创建。无同患者 confirmed 来源或不符合责任范围时停止。只在独立合成对象上验证负例；不要用历史受保护记录。

## 一次性提交及停止条件

Create plan 和 Save contact result 均为持久提交，未知时先读取该患者行及 Contact history，无法确认则停止，不重复提交。真实通知及联络未获批准。 出现数据或严重权限异常，停止受影响操作并登记。

## 结束条件及后续衔接

唯一计划及合成联络记录可读后可继续预约／报到用例 UAT-INT-002、003；预约、到店和治疗各由其用例唯一执行。

## 源码依据和证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；并非运行证据或用户验收通过。

[工作台与控件](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_followup/views/ydental_followup_templates.xml) · [路由与选项来源](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_followup/controllers/followup.py) · [权限与状态](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_followup/models/ydental_followup_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-FUP-001-001`、`RUN-UAT-FUP-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-FUP-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-FUP-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
