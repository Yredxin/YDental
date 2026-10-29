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

- [ydental_treatment/views/ydental_treatment_templates.xml](../../../../../../ydental_treatment/views/ydental_treatment_templates.xml)
- [ydental_treatment/controllers/treatment.py](../../../../../../ydental_treatment/controllers/treatment.py)
- [ydental_treatment/models/ydental_treatment_service.py](../../../../../../ydental_treatment/models/ydental_treatment_service.py)
- [ydental_queue/views/ydental_queue_templates.xml](../../../../../../ydental_queue/views/ydental_queue_templates.xml)

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

截图目录：[本用例截图目录](../images/UAT-PHA-001/)。例如 `![步骤3](../images/UAT-PHA-001/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
