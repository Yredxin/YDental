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

- [源码：ydental_document_templates.xml](../../../../../../ydental_print/views/ydental_document_templates.xml)
- [源码：documents.py](../../../../../../ydental_print/controllers/documents.py)
- [源码：ydental_print_original_service.py](../../../../../../ydental_print/models/ydental_print_original_service.py)
- [源码：ydental_print_service.py](../../../../../../ydental_print/models/ydental_print_service.py)

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

截图目录：[本用例截图目录](../images/UAT-DOC-001/)。例如 `![步骤3](../images/UAT-DOC-001/03-用途.png)`；保留原图，失败截图不覆盖；填写内容和截图保存在私有副本。
