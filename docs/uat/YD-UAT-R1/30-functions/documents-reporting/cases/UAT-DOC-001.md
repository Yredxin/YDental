# UAT-DOC-001｜预览并保存合成文书原件

- 所属阶段：U06
- 参与岗位：治疗医生或被授权的文书使用者
- 真实权限要求：当前门店 medical read 或更高、对应患者的有效门店关系与来源访问权限；公司在账号允许范围。此处选临床来源；批量导出另需 export write。
- 对应需求／技术阶段及 TC：R17、R24；S08-T11、S12-T01–04
- 验收层级：L3
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；步骤依据 SOURCE，环境、账号、数据准备后方可验收。

## 业务作用与核心行为

保留生成时来源、模板和文件的快照，供以后对照；文字确认不是正式医疗签署。

## 页面与前置条件

通过已授权导航进入 `/ydental/documents`（文书工作台）。环境负责人准备独立测试门店、新合成患者及一份已确认文字的临床来源；使用该来源没有既有原件的新链，提供可用合成模板和PDF引擎。若来源或权限不明则 BLOCKED，不复用历史文书。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 选择已准备的当前门店并打开文书工作台，在 Patient name or number 输入合成患者编号，点击 Search documents。 | 页面显示该患者在当前授权范围内的候选来源；没有候选则停止检查权限和来源。 |
| 2 | 在 Source 选择对应患者的 Clinical text 及确认状态；Content template 选择合成测试样本。 | 所选患者、来源和状态与准备清单一致，模板为合成测试。 |
| 3 | 点击 Preview selected source。 | Reviewed source 预览显示所选合成内容，展开 Source and template trace 可见来源和模板摘要。 |
| 4 | 核对预览文字和患者标签，并核实 Previous original 显示新原件无前版；如果出现已有前版则停止交负责人核实。 | 预览与合成输入相符，且没有把已有原件作为新建对象。 |
| 5 | 点击 Generate and preserve original PDF 一次。 | 页面显示 Operation accepted；此提示本身不证明已保存，结果不明不重复提交。 |
| 6 | 在 Saved originals in the current authorized scope 查找该患者、类型和生成时间，展开 Source, template and file trace。 | 看到原件版本、生成时间、来源及 PDF SHA256；记录原件内部编号和版本供后续用例。 |
| 7 | 在该行点击 View original。 | 新标签显示保存的PDF，患者及合成文书内容与已审核预览一致；无法读取时记录并停止。 |

## 异常与权限负例

使用另一个无 medical 来源读取权限的合成账号时，不得读取该患者来源或原件；没有独立账号或来源时记 BLOCKED。来源变更或版本冲突时停止并请负责人核实，不借刷新后重发。

## 一次性提交及停止条件

生成会持久保存原件与附件并产生审计；预览和查看也会记录访问审计。点击一次后结果未知先由负责人核实原件链与提交状态，未确认前不重复或新建版本。

## 结束条件及后续衔接

仅原件可识别并读取后进入 UAT-DOC-002；批量原件导出、正式模板审批及签署未在本用例操作。

## 源码依据和证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不是运行证据，也不代表用户验收通过。

- [源码：ydental_document_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_print/views/ydental_document_templates.xml)
- [源码：documents.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_print/controllers/documents.py)
- [源码：ydental_print_original_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_print/models/ydental_print_original_service.py)
- [源码：ydental_print_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_print/models/ydental_print_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-DOC-001-001`、`RUN-UAT-DOC-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-DOC-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-DOC-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
