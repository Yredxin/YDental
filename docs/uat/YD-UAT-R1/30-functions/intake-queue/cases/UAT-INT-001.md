# UAT-INT-001｜服务目录、门店映射及演示价版本

- 所属阶段：U01
- 参与岗位：集团主数据维护者、门店价目维护者
- 真实权限要求：添加集团服务需集团主数据权限及有效门店；映射、价格草稿、审核和发布需当前门店 price write；普通人员打开价目页需 price read 或 write；集团主数据权限允许目录入口，具体映射及价格仍依 price 等级。
- 对应需求／技术阶段及TC：R21；S05-T10/13、S10-T01–16
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；以下为源码支持的预定操作，待独立环境和数据准备后由用户执行。

## 业务作用与核心行为

为合成服务准备可查的价目，不把演示价当正式收费政策。

## 页面与前置条件

YDental → Service catalog and prices（`/ydental/intake/prices`），可见 Group catalog、Store service mappings、Price versions。

专用测试门店、合成服务、币种、有效区域与业务能力；报到区域必须启用并允许报到，报到和执行区域都必须包含所选服务的确切业务能力，且本店该服务与报到区域此前未映射；确认不会替换或覆盖历史价。准备不重叠的 UTC 有效时段和正数演示价；正式价政策未批准。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开价格页，核对门店和生产价格政策警示。 | 页面标明当前门店及演示快照不代表确认费用。 |
| 2 | 集团主数据维护者检查 Group catalog 是否已有本次专用合成服务。 | 能辨认代码和名称；无集团权限或无合成服务时停止并交由合格人员准备；本用例只查现有合成服务，新增集团服务尚未验收。 |
| 3 | 价目维护者在 Map store service areas 选择该服务、报到区域与执行区域，点击 Map service 一次。 | Store service mappings 显示所选服务及执行区域。 |
| 4 | 在 Create price version 选择该服务、币种，填写正数 Unit price、UTC 开始结束和 Reason，点击 Create draft price 一次。 | Price versions 出现该服务的草稿、价格与有效区间。 |
| 5 | 该草稿填写审核原因并点 Review 一次。 | 该版本变为 reviewed，出现 Publish 条件控件。 |
| 6 | 确认所选是本次合成版本且不替换既有价格，填原因并点 Publish 一次。 | 版本状态变为 published；重叠有效版本不得当作成功发布。 |

## 异常与权限负例

无 price write 不应获得上述门店修改权限；缺少集团权限不能添加集团服务。零价、重叠或无效区间应拒绝；以独立合成数据测试，勿改历史价。

## 一次性提交和停止条件

映射、草稿、审核和发布均持久提交；结果未知先查原版本和状态，不盲点。不要点击演示快照或替换历史价。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

记录合成服务、币种与有效期，交 UAT-INT-002；不得记录为正式价格政策。

## 源码依据与证据层级

源码依据为固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明环境已部署或用户验收通过。
- [ydental_intake/views/intake.xml](../../../../../../ydental_intake/views/intake.xml)
- [ydental_intake/controllers/intake.py](../../../../../../ydental_intake/controllers/intake.py)
- [ydental_intake/models/ydental_intake_service.py](../../../../../../ydental_intake/models/ydental_intake_service.py)

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

截图目录：[本用例截图目录](../images/UAT-INT-001/)。例如 `![步骤3](../images/UAT-INT-001/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
