# UAT-TRT-001｜医疗文书：编辑、保存与文字确认

- 所属阶段：U04
- 参与岗位：治疗医生
- 真实权限要求：当前门店 medical write；对应工位的医疗能力、有效持有连接和正在 serving 的医疗接诊。查看只需 medical read；写入受当前接诊及编辑占用约束。
- 对应需求／技术阶段及TC：R12、R17、R18；S08-T01/03/06/10/15/16、S12-T03
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；仅源码支持的拟验步骤，未部署、未实测、用户 NOT_RUN。

## 业务作用与核心行为

用独立文书记录合成接诊文本并保留版本；文字确认不会执行治疗、产生费用或代替正式签署。

## 页面与前置条件

从已完成 UAT-QUE-001 的新合成医疗任务开始，当前医生持有原工位且患者与门店匹配；页面为 YDental → Treatment workbench（`/ydental/clinical`）。仅填写预先约定的合成内容，不使用真实患者资料。此例保存后须先按后续业务决定是否确认；已确认文本不能再用普通保存改写。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入 Treatment workbench，核对门店、患者和接诊段；若已有文书再核对原作者和责任人。 | 患者和当前合成任务一致；新文书创建前无原作者和历史；没有当前接诊时页面提示 No current medical reception，停止。 |
| 2 | 点击 Open for editing 一次。 | 页面取得可编辑状态，显示 Server version 和编辑结果；若编辑占用或连接失效，停止。 |
| 3 | 在 Structured clinical draft 输入约定的合成文本；可选择一颗牙位及明确状态。 | 输入出现在选定字段；无牙位可选 No corresponding tooth；未观察不能写成已观察。页面约 900ms 后可能自动保存并创建持久版本。 |
| 4 | 点击 Save draft 一次，记录服务器版本与时间。 | 页面显示服务器已保存并记录 Server version 与时间；自动保存可能先产生版本，因此不能预设仅增加一次。若没有成功确认则停下核对。 |
| 5 | 刷新或重新打开并核对刚保存的内容、原作者和责任人。 | 服务端内容与合成文本一致，刷新后查看 Authored version history 中的保存版本、原作者和责任人；不一致则保留本页并记录差异。 |
| 6 | 若此合成文本已准备确认，取得编辑权并点击 Confirm text only 一次。 | 文字状态为 confirmed，服务器版本增加；刷新后查看版本历史中的确认版本，不表示治疗执行、接诊完成或正式签署。 |
| 7 | 查看后续操作入口，决定进入实际治疗或保留未完成责任流程。 | 未见新增治疗事实或费用即可继续；若已确认需更正，使用有原因的追加更正，不覆盖旧版本。 |

## 异常与权限负例

只读用户不可保存；另一有效编辑者占用、旧版本、失效连接应拒绝；不自行撤权或造旧版本。不能确认是否保存时先保留未同步内容并由负责人核查，不盲点。

## 一次性提交和停止条件

打开可能新建文书；输入后约 900ms 自动保存也可能产生持久版本；手动保存、确认、追加更正均产生持久版本。确认后再改须走带原因的更正，不重复提交。

P0 数据、资金、临床安全或严重越权异常应停止受影响操作，保留事实并联系负责人；未确认提交时不重试。

## 结束条件及后续衔接

记录版本与文本状态；治疗执行转 UAT-TRT-002，结束和待完善责任转 UAT-TRT-003。

## 源码依据与证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；源码不证明该环境已部署，也不等于用户验收或实际浏览器通过。
- [ydental_clinical/views/ydental_clinical_templates.xml](../../../../../../ydental_clinical/views/ydental_clinical_templates.xml)
- [ydental_clinical/controllers/clinical.py](../../../../../../ydental_clinical/controllers/clinical.py)
- [ydental_clinical/models/ydental_clinical_service.py](../../../../../../ydental_clinical/models/ydental_clinical_service.py)
- [ydental_clinical/models/ydental_queue_service.py](../../../../../../ydental_clinical/models/ydental_queue_service.py)

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

截图目录：[本用例截图目录](../images/UAT-TRT-001/)。例如 `![步骤3](../images/UAT-TRT-001/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
