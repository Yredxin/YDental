# UAT-SPC-001｜楼层、区域和工位

- 所属阶段：U01
- 参与岗位：门店空间配置人员
- 真实权限要求：当前门店 space=write 新建；space=read 查阅；员工账号须有有效门店会话。工位业务能力与16类授权不是同一概念。
- 对应需求／阶段／TC：R05、R06；S02-T01–10、S03-T11–13
- 验收层级：L2
- 当前可验收准备状态：**ENVIRONMENT_NOT_READY**；须由环境负责人核实固定候选、账号及数据后再执行。用户结果初始为 NOT_RUN。

## 业务作用与核心行为

把就诊空间组织成楼层、可报到区域和工位，供排班及叫号引用。

## 入口、前置条件

YDental → Clinic space → Floors / Areas / Workstations；楼层表单有 Open floor plan。显示名称可能随语言变化。

测试环境备有单独合成门店和测试账号；准备互不冲突的测试楼层、区域、工位名称和位置参数。请环境负责人确认可写权限和当前门店。

## 操作及逐步预期

| 步骤 | 操作 | 预期结果 |
| --- | --- | --- |
| 1 | 进入 Floors，查看当前门店并新建一层，填写名称、门店及正数宽高后保存。 | 楼层列表中出现该门店的新名称；重开记录可见相同门店和宽高。 |
| 2 | 进入 Areas 新建区域，选择同一门店和新楼层，填写名称、用途和矩形位置；用于排队的区域勾选 Separate reporting queue，并填写约定的队列前缀和测试参数。 | 保存后区域属于该楼层；独立报到区域显示为自身的 Reporting area。 |
| 3 | 进入 Workstations 新建工位，选择同一门店、该楼层和区域，填写名称、类型、位置，按测试用途设置 Enabled 和 Can call patients。 | 重开记录显示所选楼层、区域及开关；Reporting area 与区域的报到归属一致。 |
| 4 | 在工位表单的 Added capabilities 中选择预先准备的业务能力，保存并查看计算出的 Capabilities；也可由已放置资源提供能力。 | 显示结果来自已放置资源的能力与 Added 的并集，再扣除 Removed；它不是用户权限等级。 |
| 5 | 从楼层打开 Open floor plan，查看已保存的楼层、区域与工位。 | 平面可识别刚建立的区域和工位，位置与表单值对应；记录具体视口和看见的错位。 |

## 异常、权限负例和停止条件

仅在隔离测试记录上，用只读账号确认无写入能力；若表单可见而提交失败，以实际提示记录。不同门店的楼层与区域不能拼接；遇到拒绝记录，不改真实配置或提升权限。

保存楼层、区域、工位都是持久提交；只使用新合成记录。结果未知先刷新列表核对，不能连续新建或覆盖历史；已有业务占用的空间不得改动。

## 结束及衔接

三个新对象均可在当前门店重新查看，或将阻断步骤记为 BLOCKED/FAIL。

排班见 [UAT-SCH-001](UAT-SCH-001.md)，容量见 [UAT-SCH-002](UAT-SCH-002.md)。

## 源码依据及证据层级

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_space/views/ydental_space_views.xml](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_space/views/ydental_space_views.xml)、[ydental_space/models/ydental_space_floor.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_space/models/ydental_space_floor.py)、[ydental_space/models/ydental_space_area.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_space/models/ydental_space_area.py)、[ydental_space/models/ydental_space_station.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_space/models/ydental_space_station.py)、[ydental_space/models/ydental_space_version.py](https://github.com/Yredxin/YDental/blob/12f3f299b07ab324f7279413a928097b7ce858a8/ydental_space/models/ydental_space_version.py)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SPC-001/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区：每次执行分别记录

以下内容可暂时留空。先复制一份“执行记录”及需要的问题和 UI 意见模板，保留旧记录，再为本次使用未占用的 RUN-ID，例如 `RUN-UAT-SPC-001-001`、`RUN-UAT-SPC-001-002`。桌面、平板、手机及修复后的复验分别使用新 RUN-ID。一个 RUN 可关联多个 ISSUE-ID；不要为了截图或复现而重新提交治疗、库存、收费、退款等已提交来源。结果不明先停止并由负责人核实。

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

本用例截图放在私有副本的 [截图目录](../images/UAT-SPC-001/) 下，按 RUN 分目录，例如先创建 `RUN-001`，然后在本文件写 `![步骤3：用途](../images/UAT-SPC-001/RUN-001/03-用途.png)`。不同轮次用不同目录；原图和失败图不得覆盖，标注图另存。实际图片、账号、口令、Session 或未经授权的患者及财务信息不得上传公共仓库。
