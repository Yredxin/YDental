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

[工作台与控件](../../../../../../ydental_followup/views/ydental_followup_templates.xml) · [路由与选项来源](../../../../../../ydental_followup/controllers/followup.py) · [权限与状态](../../../../../../ydental_followup/models/ydental_followup_service.py)

## 用户填写区

- 测试日期：
- 实际使用版本或测试环境：
- 实际岗位及门店：
- 浏览器、窗口宽度、缩放：
- 用户验收结果：NOT_RUN（可选 NOT_RUN / PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 实际观察：
- 与预期是否一致：
- 失败步骤：
- 问题描述：
- 具体复现步骤：
- 复现次数／是否稳定：
- 问题等级：P0 / P1 / P2 / P3（留空待定）
- 是否阻断下一项验收：
- 截图相对路径：
- UI满意程度：满意 / 基本可用但需优化 / 需要重新设计 / 不适用（留空待定）
- 不满意的页面、位置和原因：
- 希望如何调整：
- 是否涉及需求变更：
- 用户最终意见：
- 修复后复测结果：

截图目录：[本用例截图目录](../images/UAT-FUP-001/)。例如 `![步骤3](../images/UAT-FUP-001/03-用途.png)`；保留原图与失败截图，用户材料保存在私有副本。
