# YDental 当前执行入口

## 当前 S05定向返工 / #29

- 用户本次明确只修[GPT-REVIEW6115823569](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115823569)三个BLOCKER；沿用当前S05会话与分支，原`76335d9902cee8e8c24173f0b01fd9ba8b606a5c`及全部原失败证据保留。
- 用户单独授权本次Project #29自定义“执行状态”→“返工”。实施前已完整读取21字段、15条目、6视图、7公开workflow元数据，唯一字段mutation后完整读回及差异核对；原生Status=Todo、其他字段/条目/视图/workflows和Issue实体状态均未改。执行状态保持返工，不自行转待复核；未来其他Project写仍需单独授权。
- 只修集团catalog维护与门店price-write分离、独立资格report的门店当地营业日边界、默认fail-closed可信转诊server hook/跨法人目标/真实来源审计。无新字段，不重写S03账本、S04 merge、价格快照和position事务。
- 产品修正固定`754cc331386e8294225c6579c9b4daa555160f92`、最终测试固定`68cbcdc3c5a7c0e16a8389e89a6ba44e9086bfc2`，完整链记录于docs/s05-rework-report.md及#29修正交付评论；最终文档证据SHA固定于评论。补充契约docs/s05-rework-contracts.md、安全复核docs/s05-rework-security-review.md、证据docs/evidence/s05-rework。
- 仅全新隔离S05库、合成permit与队列；不补来源医生目标company_ids/membership，不引入真实S08来源。修正交付写回读回后停止等GPT复核，不称用户验收/生产政策通过，不进入S06。

下方“当前S05”记录为原交付基线；本次三个修正和Project唯一字段授权以本节及最新review为准。

## 原S05交付 / #29

- 本次用户明确启用#29/S05；唯一当前边界为[GPT-ACTIVATE6115298923](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115298923)。已完整读取#23当前正文/有效评论、#29当前正文/全部有效评论、#28最终技术复核6115295633及状态同步6115318214；[开工检查6115339128](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115339128)已写回并逐字读回。
- S04修正最终`174a70df2cf8de515d0e781c59e6ce3825146313`已GPT技术PASS，#28保持OPEN/待用户验收，不重做S04。
- S05独立分支`codex/s05-intake-r1-20261011`；固定产品`6818bc35c35e030976df71558b188844d4de1082`、最终测试`90d1a41f8559542aed36f4fc0ff22897c17fb392`，完整SHA及最终文档证据固定于#29交付评论。交付后停止等待GPT技术复核，不能冒称GPT或用户验收通过。
- 当前只实现目录/服务区域、版本化价目与演示不可变快照、预约/现场资格、真实到店、任务/受理位置、资格复用/取消返池/改期/换区、转诊双分支和S03/S04真实联动。容量只有S03账本，患者canonical/current relation和merge fence只有S04；统一锁序patient→supply→intake。
- S05受理位置不是正式队列；S06真实waiting/calling、叫号、号序、租约及真实下游临床/检查/费用仍NOT_RUN。仅固定server hooks和受新库guard保护的合成队列契约。生产锁价/承诺价政策未批准，只有明确demo_confirmation，缺有效价失败，不能默认为0或冒称生产收费。
- 当前运行仅`scripts/s05.py`及全新`ydental_s05_test_14位时间_8位hex`、合成数据；端点/cluster/OID/配置哈希/dbfilter/端口/进程外发保护均必须通过。S00—S04工具和数据库只历史保留，不接管。依赖仅复用已存在进程本地资产；不改核心/odoo-12/业务库/既有服务或系统依赖。
- 工程交付见docs/s05-contracts.md、docs/s05-data-dictionary.md、docs/s05-security-review.md、docs/s05-report.md和docs/evidence/s05。保留失败与补交链；product→test只有测试变更，test→final仅文档/脱敏证据。无Project写授权，不改字段/workflows，不关闭Issue、不强推/自动合并/生产发布、不进入S06。

## 已完成阶段与历史会话记录

以下原S04“本次/本批”指其历史会话，不覆盖上方当前S05授权与运行边界。

- 当前需求 YD-N1 R1。唯一来源是 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、[S00 #24](https://github.com/Yredxin/YDental/issues/24) 至 [S13 #37](https://github.com/Yredxin/YDental/issues/37) 当前正文和有效评论。先读取 GitHub，再执行明确启用范围；代码、卡片及历史验收不授权开工。
- S00 已按 [GPT-CLOSEOUT](https://github.com/Yredxin/YDental/issues/24#issuecomment-6107583497) 最终收口，#24 CLOSED/completed；固定技术交付 `6dbf0a0a8be966bee7b2250b2a77e5b4d70540d8`。历史失败和补交证据保留，不重做 S00。
- S01 已按 [CODEX 收口完成](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108974493) 收口，#25 CLOSED/completed。固定产品修正 `740c42bbf611baa8713758fba38c1411d6b966c9`，产品与最终测试 `f1ce22df7002e40391ce16fd59093d60c4522b2e`，最终文档证据 `37ccd3af4c6af390506eb9229e2f1cc145e951b9`；原证据与失败链保留，不重做 S01。
- S02 已按 [GPT-REVIEW 6110161675](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110161675) 技术复核PASS，固定产品 `9653ca2d25fde16ac791dd499197703c18ef18ce`、测试 `00c76b55f205ee032534b7a3b8cda27bd1d7764d`、最终证据 `e97f721270a991bd4a737c15808896b286e488e9`。按[最新流程决定](https://github.com/Yredxin/YDental/issues/23#issuecomment-6110178328)和[状态同步完成](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110222109)，#26保持OPEN/待用户验收，最终统一验收，不重做S02。
- S03已按[最终技术复核6111270280](https://github.com/Yredxin/YDental/issues/27#issuecomment-6111270280)与[状态同步6111303932](https://github.com/Yredxin/YDental/issues/27#issuecomment-6111303932)技术PASS，#27保持OPEN/待用户验收。固定产品`ac34c247c35e531567871ae2d8da065826833fe9`、测试`31d69ccaf2ef4e7ce7c49c7d8e0acce3c5f903d6`、最终`a8c0d5a2f5963e1f3dd2c31e4d363115453d2be3`。原S03及返工失败证据保留，不重做。
- 本次用户明确启用#28/S04，唯一边界为[GPT-ACTIVATE6111275379](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111275379)。已完整读取#23当前正文/有效评论、#28当前正文/全部有效评论及#27最终技术复核/状态同步；[开工检查6111333171](https://github.com/Yredxin/YDental/issues/28#issuecomment-6111333171)写回逐字读回后实施。
- S04原固定产品`eb607750a4b35885f37acfb07d504f758b877b73`、测试`a35af92ef89465dbbf71cb6f88297e4c097b43c7`、最终`3b74b33987252d59033ae4b9d6757ad609818216`及docs/evidence/s04全部保留。[GPT-REVIEW6114781429](https://github.com/Yredxin/YDental/issues/28#issuecomment-6114781429)要求仅修patient-owned partner原生读取旁路和canonical current relation作为care/clinical前置，不重写患者号/合并/并发内核。
- 本次在原S04会话/分支定向返工。产品修正固定`887d0a9772a9ee165992ccd77af87fbb2c287d93`、最终测试`f3dc3dcb188511b19f9f2d898f45fbfdd6280663`；最终文档证据SHA固定于#28修正交付评论。补充契约docs/s04-rework-contracts.md、报告docs/s04-rework-report.md、安全复核docs/s04-rework-security-review.md、证据docs/evidence/s04-rework；原字段字典继续适用，无新增字段。写回读回后停止等GPT技术复核；不能冒称GPT或用户验收通过。
- S04只做统一患者/旧号/门店关系/行政联系人监护/重复提示/真实首次到店/本店政策/集团确认合并及并发事务/真实患者care只读审计和跨店写拒绝。S05/S06/S08/S09/S10/S12真实业务尚未启用，下游只有固定私有服务器契约与合成验证，真实联调NOT_RUN。不进入S05。
- 不从撤销任务、四份旧文档、旧计划、旧 AGENTS 或历史验收补业务规则。文档仅记录当前 Issue 的工程落地与证据，不另立计划。工程约定见 [docs/contracts.md](docs/contracts.md)，事实与阻塞见 [docs/s00-a-report.md](docs/s00-a-report.md)。

## 工作区和保护

- 核心 Git 根 `/home/redxin/code/odoo/odoo-sd/code`；本仓库为其独立 Git 根 `sd-addons/`，远端 Yredxin/YDental。每次仍核实实际路径、远端、分支、HEAD 和未提交改动。
- 不改 Odoo 核心、odoo-12、既有未提交内容、既有业务库，不停止/重配既有服务。当前批次只实现和验证 #29；新增运行只在全新隔离 S05 库中使用合成数据。系统依赖安装和既有服务变更需具体授权。
- 父目录 AGENTS.md 是既有未跟踪文件，保留原样；其中 sd-addons 为空、仅本机数据库映射等描述已陈旧，不作为实际现状或本批运行授权。
- 底座锁定 Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，本地声明20.0；Python 用核心 .venv/bin/python。此为 fork 无父根快照，不能冒称已核对同 SHA 官方上游。调用 API 前查实际源码；兼容性需所属批次实测。

## 后续工程和交付

- 原生+自研，不引入 OCA，不创建未来空壳、不机械改名或重授权许可证。命名、依赖、翻译、时间、编号、字典与动作契约见 docs/contracts.md；生产参数按 #23 第3.2节和责任阶段发布。
- 修改 addon 前读取适用 odoo-guidelines；static/ 使用 odoo-web-guidelines；安全审计用 odoo-security。技能不替代当前需求和授权。
- 本批及未来获启用的运行批次仅使用全新隔离允许范围数据库与合成数据。先验证端点/唯一库名/创建记录及OID/独立配置、data_dir、日志/精确dbfilter/端口/外发禁用；拒绝业务库、历史库与错误端点。S04使用scripts/s04.py和`ydental_s04_test_14位时间_8位hex`；S00—S03工具与库仅历史保留，不接管。演示策略不能用于生产容量分配，测试模块不得用于业务库。
- 仓库和 GitHub 只放虚拟/脱敏材料，不发布凭据、患者资料、签名、备份或原始运行日志。长期保留失败与补交证据，未执行记 NOT_RUN，能力/权限阻塞记 BLOCKED。
- 独立分支提交；S04 PR如需创建用Refs #28，不强推、不自动合并/关闭任务/启动下一阶段。本次用户明确覆盖初次S04的Project禁写边界，仅授权#28自定义“执行状态”→“返工”：已在实施前完整读取字段/条目/视图及公开workflow元数据，唯一字段mutation后完整读回及二次核对。原生Status、其他字段/条目、workflows、Issue/PR实体状态未改；执行状态保持返工，不自行转待复核。#27仍待用户验收，#28修正交付后等待GPT复核。未来独立Project写授权仍须完整读取元数据并读回；不得导出token/cookie或关闭安全控制。
