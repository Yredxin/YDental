# UAT-TRT-003｜保存后交还、正常完成和待完善责任

- 所属阶段：U04
- 参与岗位：治疗医生、具备授权的文书负责人或店长
- 真实权限要求：医疗接诊终止需当前门店 medical write、有效原工位和编辑权；责任转派由原负责人或本店店长执行，新负责人须在职、具备 medical write 及来源能力/资质；各条件按实际授权核对。
- 对应需求／技术阶段及TC：R14、R17；S06-T08/16、S08-T05/06/15/16、S12-T03
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；仅源码支持的拟验步骤，未部署、未实测、用户 NOT_RUN。

## 业务作用与核心行为

分别验收需后续接续的交还和最终正常完成，并保留未确认文书责任。

## 页面与前置条件

准备两个互不相同的新合成医疗接诊及各自文书：A 用于交还和待完善责任（保持 pending，不能先 Confirm text only），B 用于正常完成。先按 UAT-QUE-001 开始 A 并完成 UAT-TRT-001 的保存；完成 A 的交还后再开始 B 并保存 B 的文书，或者由不同医生在各自独立工位分别准备，不能假设同一医生同时持有两个接诊。不得对同一接诊先交还又正常完成。页面 `/ydental/clinical`。负责人事前准备符合来源资格的第二位合成医生。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 A 的 Treatment workbench，核对患者、接诊段、文书原作者和责任人。 | A 为当前有效 serving 接诊，文本已在服务端保存且仍待完善。 |
| 2 | 取得 A 的 Open for editing，点击 Save and hand back reception 一次。 | 文书保存成功后原接诊进入 handover，并产生可接续任务；这不是正常完成。若无成功回执，停止并核对。 |
| 3 | 在 Documents awaiting completion 中打开 A，核对责任人、服务器版本及原作者。 | 待完善文书仍有明确责任人，原作者和版本可见。交还已释放本次编辑器；若仍有有效编辑者须停止并由持有人释放。接诊任务交接责任与文书责任分别核对。 |
| 4 | 原责任人或店长选择符合资格的新负责人，填写 Transfer reason 并点击 Transfer pending document 一次。 | 责任人变为所选医生，版本历史及原作者保留；编辑占用未释放或资格不符时应拒绝。 |
| 5 | 新负责人打开 A 的待完善文书并按需补充合成文本，保存后点击 Release editing。 | 服务器版本与补充内容可读，编辑占用释放；原作者和旧版本仍可见。 |
| 6 | 在 A 交还完成后，只读取独立接诊 B 的 UAT-QUE-001 和 UAT-TRT-001 原 RUN，核对患者、当前 serving 接诊、已保存文本版本及原工位连接，再打开编辑。若 B 尚未准备，按执行清单第 22–26 行使用不同合成对象准备并记录 RUN；已完成的叫号和保存不得重放。 | B 与 A 不是同一来源；原工位连接有效。 |
| 7 | 只在 B 点击 Save and complete reception 一次。 | B 接诊段状态为 completed，任务结束；工位租约可仍保留，不能仅凭完成推断工位退出。A 的交还不会变成正常完成。 |

## 异常与权限负例

没有可见完成按钮、原接诊无效、编辑未释放或新责任人缺医版权/能力时停止；无医疗写权限不能代签。旧页与超时测试需独立环境并先核状态，不以提交失败替代权限证明。

## 一次性提交和停止条件

交还、正常完成、转派和补记各为持久动作。同一来源只选择交还或完成；结果未知先核接诊、任务、文书及责任，不重放。

P0 数据、资金、临床安全或严重越权异常应停止受影响操作，保留事实并联系负责人；未确认提交时不重试。

## 结束条件及后续衔接

A 交还并保留可追溯责任，B completed；如责任转派前置不可建立则单列 BLOCKED。后续按接续任务或结算来源继续。

## 源码依据与证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；源码不证明该环境已部署，也不等于用户验收或实际浏览器通过。
- [ydental_clinical/views/ydental_clinical_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_clinical/views/ydental_clinical_templates.xml)
- [ydental_clinical/models/ydental_clinical_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_clinical/models/ydental_clinical_service.py)
- [ydental_clinical/models/ydental_queue_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_clinical/models/ydental_queue_service.py)
- [ydental_queue/models/ydental_queue_return.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_queue/models/ydental_queue_return.py)
- [ydental_treatment/models/ydental_queue_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_treatment/models/ydental_queue_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-TRT-003-001`、`RUN-UAT-TRT-003-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-TRT-003/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-TRT-003/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
