# UAT-RPT-001｜按授权范围查询经营报表并回源

- 所属阶段：U06
- 参与岗位：经营报表使用者、收费员
- 真实权限要求：每个所选门店为账号允许公司中的活动门店，且有本指标来源的 read 或更高；本例选择 collections，需每个所选门店 settlement read 或更高。报表访问不授予源业务操作权。
- 对应需求／技术阶段及 TC：R21、R25；S12-T09、T11，S13-T05
- 验收层级：L1
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；步骤依据 SOURCE，环境、账号、数据准备后方可验收。

## 业务作用与核心行为

按来源日期查看收款事件并追溯到原业务记录；收款不是收入。

## 页面与前置条件

打开 `/ydental/reports`。环境负责人准备一个独立合成门店、一个合成线下收款来源及其日期、金额和唯一业务单号；此来源由 UAT-FIN-002 产生，不重复收款；备好该门店授权。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入报表页，核对当前账号和允许范围。 | 显示 Operating reports and source documents 和可选指标；无指标则停止核权限。 |
| 2 | Metric 选 Actual offline collections, not revenue，选择包含该来源的 Local start date / Local end date。 | 日期与合成来源的门店营业日期一致。 |
| 3 | 在 Authorized stores 选择唯一合成门店，点击 Query authorized sources。 | 已应用范围显示该门店、当地日期、币种和查询时间；选择门店不改变当前工作门店。 |
| 4 | 在来源明细表查找已记录的业务单号。 | 该行的门店、业务日期、状态和金额与准备记录一致；总额以全部匹配来源为准，不必等于单行金额。 |
| 5 | 点击该行 View source and allocations。 | 来源详情显示该来源及所选过滤条件；未经授权的来源不应出现。 |
| 6 | 查看详情的业务日期、状态、数额，点击 Return to the same report filters and page。 | 详情与来源记录一致；返回保留原过滤条件与页码。 |

## 异常与权限负例

对于没有 settlement read 的独立测试账号或未授权门店，不能查看该门店收款指标；无适用账号则 BLOCKED。跨店来源的业务页需要先正常切换至有权门店，报表权不等于处理权。

## 一次性提交及停止条件

查询与回源可产生访问审计，不收款、不退款、不移动库存。结果异常时保留筛选条件和来源编号，不重新执行业务。

## 结束条件及后续衔接

已能识别并对照合成来源后进入 UAT-RPT-002；正式经营政策及历史余额重建不在此用例。

## 源码依据和证据层级

固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不是运行证据，也不代表用户验收通过。

- [源码：ydental_reporting_templates.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_reporting/views/ydental_reporting_templates.xml)
- [源码：reporting.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_reporting/controllers/reporting.py)
- [源码：ydental_reporting_service.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_reporting/models/ydental_reporting_service.py)

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-RPT-001-001`、`RUN-UAT-RPT-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-RPT-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-RPT-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
