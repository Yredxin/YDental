# UAT-EXM-002｜检查医嘱、保留原工位与返回

- 所属阶段：U05
- 参与岗位：治疗医生、前台、检查医生
- 真实权限要求：开检查医嘱和保留/恢复：原治疗医生 medical write、有效医疗工位与接诊；检查报到依 frontdesk write，检查执行依 exam write、能力和有效资质。查询返回提示需相应业务读取权限；返回必须由原持有人确认。
- 对应需求／技术阶段及TC：R13、R14、R18；S06-T06/07/08、S09-T03/07/12
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；仅源码支持的拟验步骤，未部署、未实测、用户 NOT_RUN。

## 业务作用与核心行为

将外部检查任务和原医疗接诊关联；患者返回原工位时恢复接诊，不把检查段结束当成治疗完成。

## 页面与前置条件

从独立的新合成医疗接诊开始：UAT-QUE-001 已开始，UAT-TRT-001 已保存文书；现有精确检查服务映射、合成医嘱数据、人员能力、资质、模板及检查工位已经配置。患者与门店关系有效，原医生保有有效工位连接；不能保证这些条件时 BLOCKED。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入 `/ydental/treatment` 的 Examination or take-away prescription draft，选择 Examination order。 | 页面显示 Explicit purpose、Exact service mapping 和 Approved quantity。 |
| 2 | 填写约定的合成目的、精确检查服务及数量，点击 Save order draft 一次。 | Orders 列表出现该患者检查草稿；不等同已发行或实际执行。 |
| 3 | 核对草稿及项目后点击 Issue and freeze order 一次。 | 医嘱冻结，产生对应检查任务；记下该任务，勿再次开同一医嘱。 |
| 4 | 进入 `/ydental/queue` 的 Current execution segment，选择该明确外部检查任务，点击 Reserve workstation for external service 一次。 | Reserved return 显示原工位及保留状态；这是暂停原医疗段，不是完成或交还。 |
| 5 | 前台在 `/ydental/queue` 的 Pending explicit tasks 找到该检查任务 ID，点击该行 Report this explicit task 一次；检查人员在自己的浏览器按 UAT-QUE-001 开始并执行 UAT-EXM-001。 | 派生检查任务进入队列，检查来源与本患者一致，检查执行和结束各有记录；不重复 UAT-INT-003 的患者到店。 |
| 6 | 检查已结束后，原医生查看 Reserved return；确认合成患者已实际返回原工位。 | 原工位保留仍有效，且无未解决的其他实际执行；若过期或存在未解决执行则停止。 |
| 7 | 勾选 I see the patient actually returned，点击 Confirm return and resume 一次。 | 原医疗任务恢复 serving，保留被解决；检查结果仍独立保留。 |
| 8 | 返回 Treatment workbench 查看同患者接诊和检查结果。 | 继续医疗处理；需要交还或最终完成时使用 UAT-TRT-003，不把返回当作完成。 |

## 异常与权限负例

原持有人不在、保留过期、任务不匹配或其他执行尚未解决时不可确认返回；查询提示不是恢复。超时现场核验属于特殊流程，未建立安全前置时 BLOCKED。

## 一次性提交和停止条件

保存及发行医嘱、保留、报到、检查执行和恢复都是持久动作；每个动作仅由指定用例执行一次。响应未知先核来源、队列与接诊状态，不重放。

P0 数据、资金、临床安全或严重越权异常应停止受影响操作，保留事实并联系负责人；未确认提交时不重试。

## 结束条件及后续衔接

同一合成患者医疗接诊恢复 serving；后续 UAT-TRT-003 决定交还或正常完成。

## 源码依据与证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；源码不证明该环境已部署，也不等于用户验收或实际浏览器通过。
- [ydental_treatment/views/ydental_treatment_templates.xml](../../../../../../ydental_treatment/views/ydental_treatment_templates.xml)
- [ydental_treatment/models/ydental_treatment_service.py](../../../../../../ydental_treatment/models/ydental_treatment_service.py)
- [ydental_queue/views/ydental_queue_templates.xml](../../../../../../ydental_queue/views/ydental_queue_templates.xml)
- [ydental_queue/models/ydental_queue_return.py](../../../../../../ydental_queue/models/ydental_queue_return.py)
- [ydental_exam/models/ydental_exam_service.py](../../../../../../ydental_exam/models/ydental_exam_service.py)

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

截图目录：[本用例截图目录](../images/UAT-EXM-002/)。例如 `![步骤3](../images/UAT-EXM-002/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
