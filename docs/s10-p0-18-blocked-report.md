# S10-P0-18 原生元数据白名单门禁 BLOCKED

本批 **BLOCKED**，停止在一次原生 XML 导入后的提交前精确差异门禁：`AssertionError: ('METADATA_TABLE', 'ir_actions')`。导入进程 exit1、事务回滚、元数据提交0；Web、Firefox、登录、工作台、PDF渲染及下载全部0/NOT_RUN。没有扩大白名单、修脚本重试或第二次CREATE。等待GPT独立复核，不申请原生UI/PDF限定PASS。

唯一授权 [6227951775](https://github.com/Yredxin/YDental/issues/34#issuecomment-6227951775)，P0-17裁定 [6227904194](https://github.com/Yredxin/YDental/issues/34#issuecomment-6227904194)已完成，未重判或重跑。唯一仓库Yredxin/YDental、工作目录`/home/redxin/code/odoo/odoo-sd/code/sd-addons`、原分支`codex/s10-settlement-finance-r1-20261013`。唯一父/执行产品HEAD `68c9096246464f9ab1c3ec9c014fe7dc1be6d04b`，core只读固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。交付子HEAD由正式回执固定。产品、ACL、core、AGENTS、旧脚本/报告/证据均未修改。

## 事前门禁和冻结

完整读取#23正文/3评论、#34正文/240评论、#35 OPEN/0及唯一授权；所有237条此前已读评论正文逐字相同，新增为P0-17交付/裁定及本授权。没有已有P0-18预检/交付或并行任务。origin、远端HEAD、branch和旧文件工作树匹配。完整正文已私有保存，[逐评论正文SHA索引](evidence/s10-p0-18/github-comment-body-index.json)和[开工索引](evidence/s10-p0-18/github-start.json)固定读取范围。

核对P0-17全部18项文件SHA256、字节数及固定Git内容，索引自身SHA `e1082ddc013e0708363791d6a88ecc8e19cab9e2c2db8c115e4783c8dd1f3598`，Git对象`11becf8361bf8e38096e6c4e51398afd35838adb`；没有重跑3954项P0-17检查。纯文件预检最终14项exit0，包含元数据正例与经济/权限/无关视图/menu action/module/XMLID/旧arch/语言越界反例。[静态结果](evidence/s10-p0-18/offline-result.json)保留此前两次纯文件exit1：误假定tokens还有zh_CN，以及负向fixture写入原有write_uid1而未实际改变值。另记录系统Python无lxml、PATH无PDF命令行工具，改用既有3.12.15 venv及既有PyMuPDF；未安装依赖或改环境。

唯一正式[预检6228148599](https://github.com/Yredxin/YDental/issues/34#issuecomment-6228148599)于2026-10-17 **01:49:38 UTC**发表，**01:49:48.688 UTC** REST GET逐字读回；8028字符/12268 UTF8字节，body SHA256 `86db1d60560917b1081c27d4687b5a1997d1bc83f8c96aca9637d7fbb0f80449`。读回前所有运行预算0；[原文](s10-p0-18-preflight.md)及[读回证据](evidence/s10-p0-18/preflight-api-readback.json)保留。

[执行冻结](evidence/s10-p0-18/execution-freeze.json) SHA256 `0887efa9ab7f009644e02e057a2f6fc9ec60841b709982c673da728c4ceea0a5`，冻结五个脚本、产品/core/依赖SHA、命令、身份、请求/审计/连接预算及停止条件；[SQL合同](evidence/s10-p0-18/sql-contract.json) SHA `723a27d87bf3a00c87544d98bb6b7de02d9ab530b3c73479a6c5c77ed1541c09`，包含643表全部字段及字面SELECT；[元数据合同](evidence/s10-p0-18/metadata-contract.json) SHA `4fd82604d0ccbc466042bde0b78eac6d12be039353d1a974cbf2393dbc92aa26`，固定五记录原值/预期语言结构与逐列白名单。运行后五脚本及全部冻结依赖SHA再核对全等，没有修正或放宽冻结合同。

## 实际执行与停止边界

| 门禁 | 真实结果 |
|---|---|
| W5源前只读核验 | 一条READ ONLY/REPEATABLE READ连接；名称/OID2100310/cluster7694897083368259627、catalog643、P0-16已封存全部643表签名匹配，源无其他活动连接。只引用已封存身份/权限/来源，不运行P0-16资格脚本。ROLLBACK/CLOSE先于CREATE。 |
| 唯一维护/复制 | 一条autocommit维护连接，源无连接、名称不存在、cluster正确；一次CREATE成功。唯一新名`ydental_s10_p018_20261017020000_8e21bc49`，新OID **2100327**，不同于完整旧catalog所有OID；独立目录及不可变marker、配置SHA绑定。名称中的时间为冻结标签，实际动作时间以intent文件mtime及原生日志为准，不能把名称标签当实测创建时刻。 |
| 新副本加载前 | 独立READ ONLY/RR连接，全部643表与源逐行相等。152份合成filestore经copy2复制，独立目录、无硬链接或源回写共享。 |
| 原生加载 | 一个专用元数据进程PID696121，原生PG backend **1377390**；固定registry加载92个已装模块，不是install/upgrade/test。一次`convert_file(env,'ydental_settlement','views/ydental_settlement_templates.xml',idref,mode='update',noupdate=False)`，显式idref，专用元数据环境uid1，无执行者sudo或直接业务ORM。 |
| 提交前门禁 | convert_file返回、flush后捕获同一事务643表；精确比较首次拒绝`ir_actions`表。exit1，执行rollback/close；唯一业务元数据事务COMMIT **0**。没有执行独立“成功加载后/Web前”连接。 |
| 新副本停止尾审 | 使用第二条独立副本READ ONLY/RR连接，643表与本批加载前、W5源逐行全等；changed_tables=[]。旧152文件全等。 |
| W5最终后核验 | 第二条独立源READ ONLY/RR连接，643表与本批前全等，源config/marker及152文件封存再核正确，ROLLBACK/CLOSE。 |
| Web/UI/PDF | 后续全部未启动，无页面截图、PDF字节、响应SHA或下载审计；不以静态模板或旧样张替代真实证据。 |

执行器命令 `PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python scripts/s10_p0_18_control.py` 最终exit1；元数据子进程exit1，无SIGSEGV。只读尾审均完成。历史R3 Native SIGSEGV根因仍UNKNOWN，本次Python断言失败不是该原生崩溃的复现或修复。

## 阻断依据与证据限制

冻结白名单仅列`ir_ui_view`三记录、`ir_ui_menu320`、`ir_act_url571`及对应五个`ir_model_data`，没有列`ir_actions`。真实比较器 `scripts/s10_p0_18_contract.py:188` 因该表变化拒绝；`scripts/s10_p0_18_metadata.py:36` 在保存precommit证据及commit之前调用该门禁，异常路径rollback/close，控制器立即停止后续动作。[脱敏原生失败片段](evidence/s10-p0-18/metadata-failure-redacted.log)保留实际异常与连接/registry日志；完整原始日志和原始快照留私有并由[私有artifact索引](evidence/s10-p0-18/private-artifact-index.json)固定SHA/字节数。

纯文件后续定位查明：固定core `odoo/addons/base/data/base_data.sql:5–13` 明确`CREATE TABLE ir_act_url ... INHERITS (ir_actions)`；`odoo/addons/base/models/ir_actions.py:90–103`说明这些原生动作表的PG继承关系，424–435定义act_url。冻结快照语句使用`FROM public."ir_actions"`而没有ONLY；因此子表原生更新可反映在父表查询行集中。加载前保存的两表均含action571，技术字段相同。实际源码段和固定SHA在[阻断核验](evidence/s10-p0-18/blocked-verification.json)中。

**预检遗漏了该原生父表投影，静态fixture也只模拟子表而漏掉父表反映。** 这是本批执行方案的不足；门禁按冻结合同拒绝是正确停止，不能在运行后补列白名单继续导入。

完整未提交after快照只在进程内存中，冻结代码把持久化放在门禁通过之后，因此本次异常前没有落盘完整瞬时row/column diff。能实证的是原生门禁拒绝`ir_actions`，以及回滚后的全部643表和filestore全等；**不能声称已测得瞬时差异仅为action571的write_date，也不能声称五XMLID所有瞬时差异已验证通过**。该字段级解释只能留给后续独立授权的更精确合同，不能重跑本窗口补证。

643表全等是业务及元数据行事实核验；不是PG序列、WAL或整座数据库物理字节全等测量。没有新增SQL越过既定连接预算检查这些内容。

## 实际预算、费库款及未运行

| 项目 | 预算 | 实际 |
|---|---:|---:|
| W5前/后只读连接 | 1+1 | 1+1，均rollback/close |
| 维护连接 / CREATE | 1 / 1 | 1 / 1 |
| 副本加载前/成功加载后/停止尾审只读连接 | 1+1+1 | 1+0+1，已用均rollback/close |
| 原生元数据连接 / Web连接 | ≤4 / ≤4 | 1 / 0，原生backend-create日志计数；全部物理PG连接合计6 |
| 元数据进程 / XML调用 / 元数据commit | 1 / 1 / ≤1 | 1 / 1 / 0 |
| Odoo HTTP / Firefox上下文 / 登录 / 手工切店POST | 1 / 1 / 1 / 0 | 全0 |
| 工作台GET / PDF GET / render / download | 2 / 1 / 1 / 1 | 全0 |
| 新S01审计 / 技术assets附件 | 6 / ≤5 | 0 / 0 |
| 经济/临床/权限业务写、历史重放、直接业务ORM、shell/install/upgrade/init/test、执行者sudo、系统专项 | 0 | 全0 |

[source-before](evidence/s10-p0-18/source-before.json)、[source-after](evidence/s10-p0-18/source-after.json)、[target-before](evidence/s10-p0-18/target-before.json)、[target-after](evidence/s10-p0-18/target-after.json)分别固定643表签名、backend及实际只读断言；[执行结果](evidence/s10-p0-18/execution-result.json)及[停止差异](evidence/s10-p0-18/stopped-target-table-diff.json)保留原始BLOCKED口径。独立纯文件尾审补充核对四份实际快照全等，见blocked-verification，未追加数据库连接。

核对范围包含原生account.move/line/payment/partial.reconcile、YDental source/fee/price/payment/refund/close、clinical document/version、stock move/quant/lot、授权/公司/员工和业务附件；全部原事实不变，invoice1仍posted/out_invoice/paid/740/residual0，既存500+240和20+40+80+600只是原封存事实，没有再登记、核销或重放。

P0-13/OID2100325、P0-14/OID2100326没有连接或复用；离线准备只读取其历史批次保存的**W5源元数据**，未读取或操作受保护克隆。refund14、close9/权限负向、refund13分页、旧文书确认均未重放。没有产品变更、OS/PG/Docker/网络安全专项、Issue/Project正文状态修改、合并部署或P0-19/S11。

## 保全、撤回及交付

唯一失败副本OID2100327、私有配置/marker/原始日志与所有源/尾审快照保留，不DROP/重置/覆盖/复用；元数据进程已退出，无本批HTTP或Firefox需要停止。没有产品补丁或数据迁移需回滚；元数据事务已rollback，数据库与filestore继续封存。不能删除失败副本或改旧证据来“撤回”。

只正常线性提交新增脚本、报告及脱敏证据；[SHA256索引](evidence/s10-p0-18/sha256-index.json)固定全部新增文件，索引自身SHA及最终提交由正式GitHub回执固定。冻结五脚本保留为实际失败执行版本，禁止直接再次运行。

后续只有GPT另行正式授权才能修正执行合同，先纯文件核清PG继承父表投影及逐记录技术字段，并在断言前固定完整候选差异；不能从本报告推导重开本批、复用失败副本或扩大权限。当前只请求BLOCKED证据复核。

在#34发布正式BLOCKED回执，REST GET正文逐字全等并保存后立即STOP，等待GPT独立技术复核。真实页面、PDF字节/中文视觉、真实多页、权限负向、整模块升级、F4/T08/T11/T12均NOT_RUN或原阻断；S10技术/生产和T12仍BLOCKED，R3 UNKNOWN/W4 STOP/旧W5失败、历史原版PDF及生产财税到账政策缺口保留。最终S13统一用户效果验收边界不变。
