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

- [源码：ydental_reporting_templates.xml](../../../../../../ydental_reporting/views/ydental_reporting_templates.xml)
- [源码：reporting.py](../../../../../../ydental_reporting/controllers/reporting.py)
- [源码：ydental_reporting_service.py](../../../../../../ydental_reporting/models/ydental_reporting_service.py)

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

截图目录：[本用例截图目录](../images/UAT-RPT-001/)。例如 `![步骤3](../images/UAT-RPT-001/03-用途.png)`；保留原图，失败截图不覆盖；填写内容和截图保存在私有副本。
