# UAT-PAT-001｜合成患者档案与门店关系

- 所属阶段：U01
- 参与岗位：前台／患者资料维护者
- 真实权限要求：当前门店 patient 或 frontdesk 至少 write 用于建档与关系；只读搜索可由 patient、frontdesk、medical 或 exam 的 read/write 满足。临床背景读取另需 medical 或 exam，写入需 medical write；本用例不写临床背景。
- 对应需求／技术阶段及TC：R04、R22；S04-T01–10、S12-T12
- 验收层级：L2
- 当前可验收准备状态：ENVIRONMENT_NOT_READY；以下为源码支持的预定操作，待独立环境和数据准备后由用户执行。

## 业务作用与核心行为

建立可被当前门店识别的患者身份并区分门店关系与实际到店。

## 页面与前置条件

YDental → Patients（源码 `/ydental/patients`）；页面含 Search、Create administrative patient identity，详情有 Store relationships and actual first arrival。页面显示语言可能因环境翻译不同。

独立测试环境、有效门店和上述权限；准备未使用过的合成姓名与非真实联系方式。不得使用历史患者。

## 有序操作和预期结果

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 打开 Patients 并核对 Current store。 | 门店名称与本次被授权门店一致；不一致即停止。 |
| 2 | 输入合成姓名或号码并 Search。 | 列表显示匹配结果；没有匹配时不把其他人的记录当成测试对象。 |
| 3 | 展开 Create administrative patient identity，填合成 Name 及必要资料，点击 Create patient 一次。 | 出现新档案并可在列表中找到；号码与姓名可识别为本次合成记录。 |
| 4 | 打开该档案，查看 Possible duplicates 和 Traceable patient numbers。 | 重复提示仅为提示；新号码可见，不因共享电话自动合并。 |
| 5 | 在 Store relationships and actual first arrival 查看当前门店；若尚无关系且提供 Establish this store relationship，点击一次。 | 当前门店关系出现；首次实际到店仍显示 Not yet recorded，建立关系不代表到店。 |
| 6 | 展开 Add contact or declared guardian，填写合成姓名、选择 Contact 或 Declared guardian 并填写 Relationship；不勾选 Verification recorded，点击 Add contact 一次。 | Contacts and declared guardians 出现该合成联系人及关系，显示 Pending verification；声明监护人不等于已核验。 |
| 7 | 记录新患者编号供预约用例使用。 | 后续仅复用这个新合成患者，结果记录不包含真实联系方式。 |

## 异常与权限负例

用只读或无患者管理写权限账号观察建档控件不可用或服务拒绝；无医疗权限不可据此获取医疗内容。不得尝试合并真实档案。

## 一次性提交和停止条件

创建患者、联系人及建立关系是持久动作；响应未知先查列表和关系，禁止重新创建。实际到店只由 UAT-INT-003 执行，不点击本页 Confirm actual arrival now。

出现数据、资金或严重权限异常时停止受影响操作并记录，不在不明状态下重试。

## 结束条件及后续衔接

保存合成编号、门店关系和观察；下一项 UAT-INT-002。

## 源码依据与证据层级

源码依据为固定候选 `12f3f299b07ab324f7279413a928097b7ce858a8` 的 SOURCE；不证明环境已部署或用户验收通过。
- [ydental_patient/views/ydental_patient_views.xml](../../../../../../ydental_patient/views/ydental_patient_views.xml)
- [ydental_patient/views/ydental_patient_templates.xml](../../../../../../ydental_patient/views/ydental_patient_templates.xml)
- [ydental_patient/controllers/patient.py](../../../../../../ydental_patient/controllers/patient.py)
- [ydental_patient/models/ydental_patient_service.py](../../../../../../ydental_patient/models/ydental_patient_service.py)

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

截图目录：[本用例截图目录](../images/UAT-PAT-001/)。例如 `![步骤3](../images/UAT-PAT-001/03-用途.png)`；保留原图，不覆盖失败截图，实际填写及截图放私有副本。
