# YD-N1 R1 S10-P0-22：存储元数据完整性风险硬停止

结论为 **S10_TECHNICAL_EXIT_BLOCKED**，五组必要退出缺口尚未补齐，不能申请S10阶段技术PASS。本批没有重复P021业务或改判其已采子证据。唯一新隔离副本的初始表/文件全等准入通过，但首次新会话检查点的提交后独立读回出现无法解释的stored字段变化，按正式授权的数据损坏风险边界停止。最终尾审该字段回到原值，原因仍UNKNOWN；这不是修复证据，不据此继续。

依据为 [唯一授权6230134070](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230134070)，P021正式裁定 [6230102263](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230102263)完整读取并继承，不重复裁定/运行。唯一父HEAD `f58d92046e14c77834a3ff12351a0010834e2da8`；原分支 `codex/s10-settlement-finance-r1-20261013`、origin及工作目录均匹配，起始工作树干净。core固定只读 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。#23/#34正文和全部有效评论3/260已API读取保存，与P021原正文/253旧评论逐字相同；新增仅P021四冻结/交付/裁定和本授权，未发现本批已有预检或交付。#35 OPEN/0，Issue/Project0修改。

正式唯一预检 [6230358883](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230358883)在首次DB/Odoo操作前发布，于2026-10-17T05:49:28.785203+00:00 REST GET全文逐字读回。正文SHA256 `21e4b07cd5a190047186ef1ca3bff99f834ee32c1898e184feb1bc1ac48f87dd`；冻结SHA256 `ff131b9731247e8a6d579de7b0e7a44cc4175cc901242ac12669dea28dbd3b47`。8份执行脚本及所有引用产品/core/旧证据/私有源输入共445项SHA在initial-freeze中，实际测试执行提交为 `219df2a8161f217abb2aa20cc446ffd2c68cd868`。本批产品0修改，仍为P021 be1d12a2d21771ca411ca8bdd510437980b68ef3内容；未改旧脚本/报告/证据、S01—S09/core或AGENTS。

纯文件预检已完成：全部新增脚本compile/symtable、真实catalog字段/返回值交接、四个文书动作生命周期正例及金额/患者/锁增量+2/错误审计actor反例、实际persist先保存全差异再拒绝，均exit0。准备阶段纠正了目录单位应取关联product.uom、slot返回不含version须读真实记录的两个API假设，均发生在正式预检和任何数据库操作之前；未计为运行修复轮。旧347文件SHA及引用私有marker/尾审SHA全核，未重跑旧测试。静态准备通过不代表实际文书、RPC/token或升级已运行。

|来源／副本|实际核验|
|---|---|
|唯一只读源|P021 `ydental_s10_test_20261017050000_21b0cafe`，OID2122140，cluster7694897083368259627；前/后各一条严格READ ONLY/REPEATABLE READ，均显式ROLLBACK/CLOSE。|
|源准入|源前读与已采P021最终645物理表/schema/全部stored列逐字段相同；源无其他连接，关闭后维护autocommit会话再次确认0连接，不终止他人。|
|唯一新副本|`ydental_s10_test_20261017060000_22b0cafe`，OID **2144126**，端口 **18323**；尾码22b0cafe标识P022且符合既存严格synthetic guard，独立config/data_dir/marker。|
|复制|maintenance1/CREATE1，固定TEMPLATE源，无其他旧库连接；645表初始完整物理行/类型/关系tuple与源全等。198份filestore真实copy2，内容SHA与P021已采索引、源/副本相同，inode不同、无软/硬链接或共享回写。|
|源最终保全|第二且最后源连接核645表/schema/所有stored行与复制前全等；198文件前后SHA全等。源从未运行Odoo/Web、业务、授撤权或升级。|

`created-lineage.json`、源/副本初始全差异与decision、源前/最终RO签名和filestore索引、`source-final-preserved.json`已固定。新副本是本次合法续接来源，未恢复P021旧运行窗口；W5及P013/14/18/19/P020 A/B均0连接/复用/写入。所有新旧库、日志、配置、文件和卷保留。

实际唯一Odoo native进程为A，PID **844851**，exit **1**，SIGSEGV=False。先在副本核OID/cluster和9个实际加载关键函数：文件来源均位于固定sd-addons，code对象与该固定源码重新compile相同，结果在 `r0-A-loaded-source.json`；这不证明整个环境无问题，也不作为新业务通过。

A仅执行普通原责任人user7的新S01绑定会话，`fresh-owner-scope`完整前后存储差异已保存并通过对应S01行新增判据。随后自有cursor记录COMMIT intent/returned、保存完整precommit，并用新的严格RO/RR连接全表读回。**该检查点的最终门禁失败，没有发布成功marker；acquire尚未调用。** 不能把COMMIT返回、会话创建成功或静态模型正例写成文书完成。

|异常字段证据|实际观察|
|---|---|
|物理来源|`public.ir_ui_view` / ID929，key=`account.portal_my_journal_mail_notifications`|
|列|stored Text `arch_prev`；schema和其余全部表/行/列相同|
|长度|before／失败独立读回／最终尾审均2022字符|
|唯一差异|字符offset1992（从0计），`v` / U+0076（118）→`6` / U+0036（54）；对应闭合标签片段 `</div>`→`</di6>`|
|before字段SHA256|`776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664`|
|失败读回字段SHA256|`75cf739577c6a1977bdd25ddfc4df3a930255243916765abd79b248819248050`|
|最终尾审字段SHA256|`776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664`，与before相同|
|未变事实|该view的active `arch_db`、write_uid/write_date不变；全部stored经济事实、患者/价源/公司/门店/款项/核销/批次及原件/附件不变。|

完整before/after/full-diff先保存，再在冻结 `committed_gate` 拒绝 `COMMIT_READBACK_DRIFT`。公开完整逐字段索引见 `A-owner-scope-readback-diff-index.json`，原失败decision原字节保留；全值645表快照和该完整view行留在0700私有目录。最终新副本尾审又先保存完整差异，证明所有stored表/行/列与本次scope precommit相同；`failed-readback-vs-final-tail`仍按未解释瞬时变化保存FAIL，不把恢复原值追认为修复或旧PASS。汇总 `integrity-stop.json` 同时记录三份字段SHA及唯一字符差异。

固定 `odoo/addons/base/models/ir_ui_view.py:667–671` 的正常write分支会把self.arch_db作为arch_prev并走普通write；这里不是已解释的整段派生架构写入或技术时间变化。当前证据不足以确定变化的来源、发生/恢复机制或责任主体，**根因UNKNOWN**。不将它归为纯展示/比较器错误，不扩大元数据白名单，不修正该字段、改核心或使用修复额度强闯。没有调查或改动OS/PG/Docker/网络等专项，也没有用“无SIGSEGV”声称历史Native风险解除。

|五组|本批结果／实际执行|
|---|---|
|A 同源文书和原件重取|BLOCKED_BEFORE_DOCUMENT_ACTIONS；只有新会话scope提交返回，独立读回门禁FAIL。acquire/confirm/correct/release均0，真实原件GET0，doc1仍pending/v2/editorNULL。|
|B 六项不可改删|NOT_RUN_STOP_BOUNDARY；6项MODEL负向0。350的静态交接校验通过不能代替实际负向。|
|C 额外原件隔离/真实附件图片/RPC/token|NOT_RUN_STOP_BOUNDARY；MODEL夹具、真实HTTP/RPC、有效token构造、图片像素验证全0。P021那次6078字节不追补为PASS；19项旧断言的MODEL层级纠正按正式裁定保留。|
|D T05 failed/丢响应/防重|NOT_RUN_STOP_BOUNDARY；独立新患者/事件/fee6/invoice6/receipt6/refund2全部0，丢响应注入0、同键重复0，不涉及旧资金。|
|E 带业务升级|NOT_RUN_STOP_BOUNDARY；S10-only upgrade0、升级后入口0，不能用成功复制或Registry加载代替升级。|

完整 [22行新增退出表](s10-p0-22-exit-table-final.md) 和 `exit-table-final.json`逐行保留P021完整历史对象及确定性SHA，只增加本批层。已采P021财务/库存/原件子证据按原来源、版本、正式裁定继承，不重新收付、不重建主链、不复核P020 A。F4/T08/T12/T15同源文书、T16六项负向、T10/F6/T14隔离与网络、T05恢复以及升级必要缺口均尚未补齐；**S10阶段技术退出条件未满足**。

|实际预算|使用|
|---|---|
|source strict RO/RR|2／2：复制前和最终，均关闭|
|全部独立strict RO/RR|5／24：上述2＋clone initial、scope独立读回、final-tail各1|
|maintenance／CREATE|1／1，各一次|
|native Odoo|A一进程，PID844851，exit1，无SIGSEGV；源码身份检查9项相同；实际backend1436159，日志中仅新副本DSN，池观测1／8|
|COMMIT|明确returned1，仅新绑定scope；其独立readback失败、成功marker未发布；未知资金提交0|
|文书／业务|doc四动作0，六项负向0，C模型/RPC/HTTP0，T05经济0，旧已采交易重放0|
|Web／PDF／升级|HTTP0、Firefox0、原件GET/生成0、PDF render0、upgrade0|
|修复|0／最多2轮；本次触发完整性硬停止，不能用剩余额度放行未知风险|
|边界|其他旧库0，executor sudo0，产品/core/S01—S09/AGENTS/旧证据0修改，Issue/Project0写，P023/S11/合并部署0|

累计native backend创建1和池峰值1分别记录，不相互混淆；逐PID无DSN创建字段时保持UNKNOWN，不补造映射。五条独立RO连接都有intent、真实backend身份及ROLLBACK/CLOSE，maintenance也有关闭记录。冻结金额上限没有消耗；尚未运行脚本仅可静态阅读，不作为实测结果。

数据/原件迁移仅为被授权的template复制和独立filestore复制，无schema迁移、无新原件或附件替代。副本内旧original1/2、attachment161/630、源/费用/账款/退款及库存表与初始副本全等；scope precommit与最终尾审645表全等。原件文件SHA保全属于复制/只读核验证据，不是“合法文书更正后真实页面取回”证据。没有生成任何本批PDF或截图，因而不宣称新增视觉或网络层PASS。

以下7步仅回看固定材料，**不是重启窗口、继续数据库或点击付款的指令**：

1. 看 `created-lineage.json`：核源2122140→新副本2144126及198份文件独立复制。
2. 看源/副本初始decision和源最终保全：645表逐字段及filestore前后相同。
3. 看 `r0-A-loaded-source.json` 和进程result：9函数来源/编译一致、真实PID和exit1。
4. 看 `A-owner-scope-precommit`私有全值、公开readback索引和FAIL：唯一列arch_prev/row929。
5. 看 `integrity-stop.json` 的三个SHA和offset1992：明确瞬时差异及尾审恢复原值，原因未知。
6. 看 `offline-seal-verification.json`：doc1 pending/v2/editorNULL、invoice1 740/0及旧原件/资金库存保全，不是新业务通过。
7. 看完整22行表及五组NOT_RUN/BLOCKED，确认没有把只读保全当阶段退出。

回滚与最低动作：未部署或合并，本批产品0修改，无线上回滚。保持停止状态，保留原源、新副本、原件、所有失败/尾审和冻结证据，不删库/附件、不修arch_prev、不reset/clean/force-push。最低是GPT独立复核该完整存储差异与三份快照，先明确异常来源/安全继续条件及后续有界授权；不能直接重启旧窗口或重新创建副本、重放已提交业务。本次不自行提出或执行OS/PG专项。原P021历史Native及生产风险仍未解除。

最终纯文件核验exit0：9份新增脚本compile、445项初始冻结及347项P021清单SHA全部相同，原22行完整对象相同，产品/core无修改；256份私有文件共1249150563字节已哈希封存，两个私有根目录模式0700。公开配置秘密/具体session cookie扫描未见匹配，完整快照和日志不进Git。核验结果见final-offline-verification.json，结果不替代实际业务验证。

固定执行测试SHA为219df2a8161f217abb2aa20cc446ffd2c68cd868；纯离线封存脚本提交为cc17a6a6f4160c99c7810a2cc0aafd78d6965a88；最终报告/证据SHA由线性提交和正式回执固定，逐文件SHA清单排除其自身并在回执另给清单SHA。所有原始全值、完整日志、配置、源private marker和HTTP计划秘密在0700私有目录；公开仅脱敏列差异/哈希/实际预算及报告。完成正常推送后，在#34发表具体BLOCKED回执，REST GET正文全文逐字全等保存后立即STOP，等待GPT独立裁定，不自行启P023/S11、改Issue/Project状态、合并或部署。
