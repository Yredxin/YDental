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

产品候选 `12f3f299b07ab324f7279413a928097b7ce858a8`，以下是 **SOURCE** 依据：[ydental_space/views/ydental_space_views.xml](../../../../../../ydental_space/views/ydental_space_views.xml)、[ydental_space/models/ydental_space_floor.py](../../../../../../ydental_space/models/ydental_space_floor.py)、[ydental_space/models/ydental_space_area.py](../../../../../../ydental_space/models/ydental_space_area.py)、[ydental_space/models/ydental_space_station.py](../../../../../../ydental_space/models/ydental_space_station.py)、[ydental_space/models/ydental_space_version.py](../../../../../../ydental_space/models/ydental_space_version.py)。源码存在不证明本环境已部署、实际操作成功或用户验收通过。环境、权限和历史证据由环境负责人单独确认。

截图目录：`../images/UAT-SPC-001/`。截图使用如 `03-用途.png` 的相对路径，不覆盖原图，私有副本保存；不要把真实患者、凭据、Session 或未授权信息上传公共仓库。

## 用户填写区（可暂时留空）

- 测试日期：
- 实际使用版本或测试环境：
- 实际岗位及门店：
- 浏览器、窗口宽度、缩放：
- 用户验收结果：**NOT_RUN**（可改为 PASS / PARTIAL / FAIL / BLOCKED / N/A）
- 实际观察：
- 与预期是否一致：
- 失败步骤：
- 问题描述：
- 具体复现步骤：
- 复现次数／是否稳定：
- 问题等级（P0 / P1 / P2 / P3）：
- 是否阻断下一项验收：
- 截图相对路径：
- UI 满意程度（满意 / 基本可用但需优化 / 需要重新设计 / 不适用）：
- 不满意的页面、位置和原因：
- 希望如何调整：
- 是否涉及需求变更：
- 用户最终意见：
- 修复后复测结果：
