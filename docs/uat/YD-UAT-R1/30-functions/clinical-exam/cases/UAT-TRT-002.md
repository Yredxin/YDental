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
- [ydental_treatment/views/ydental_treatment_templates.xml](../../../../../../ydental_treatment/views/ydental_treatment_templates.xml)
- [ydental_treatment/controllers/treatment.py](../../../../../../ydental_treatment/controllers/treatment.py)
- [ydental_treatment/models/ydental_treatment_service.py](../../../../../../ydental_treatment/models/ydental_treatment_service.py)
- [ydental_inventory/models/ydental_inventory_service.py](../../../../../../ydental_inventory/models/ydental_inventory_service.py)

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

截图目录：[本用例截图目录](../images/UAT-TRT-002/)。例如 `![步骤3](../images/UAT-TRT-002/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
