# S10-P0-19 Web累计物理连接超预算 BLOCKED

**本批BLOCKED，真实工作台与当前内部PDF目标未完成。** 两项指定验证修正已通过33项纯文件检查及本批原生元数据提交前/独立提交后门禁；但Web阶段原生连接创建累计 **11条，超过冻结上限4**。执行器触发`NATIVE_CONNECTION_BUDGET`、exit1，停止后续动作并完成许可尾审。没有调预算、改冻结脚本、再建库、再次导入、登录或点击。

唯一授权 [6228355422](https://github.com/Yredxin/YDental/issues/34#issuecomment-6228355422)，P0-18裁定 [6228320925](https://github.com/Yredxin/YDental/issues/34#issuecomment-6228320925)保留原BLOCKED，不重判/重跑/复用旧窗口。唯一仓库Yredxin/YDental、目录`/home/redxin/code/odoo/odoo-sd/code/sd-addons`、分支`codex/s10-settlement-finance-r1-20261013`，执行父HEAD `432c06f1b3529eafd7f7610475cb11c9ea834b3c`，core只读固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。本批只新增P0-19许可文件，产品、ACL、core、AGENTS及所有旧文件不改；交付子SHA由正式回执固定。

## 事前权威与冻结

完整读取#23正文/3评论、#34正文/244评论、#35 OPEN/0及唯一授权，旧241条评论逐字相同，新增仅上批交付/裁定及本授权；无既有本批预检/交付或并行任务。origin、branch、本地/远端HEAD、旧文件工作树匹配，完整正文留私有，[开工与逐评论正文SHA索引](evidence/s10-p0-19/github-start.json)固定读取范围。P0-18全部23项SHA/字节数/固定Git内容及索引对象`9430b1ed99a75dc2ce48472155ad93c294501fb0`核对，不运行其旧测试或业务。

正式唯一[预检6228603990](https://github.com/Yredxin/YDental/issues/34#issuecomment-6228603990)于2026-10-17 **02:39:06 UTC**发表，**02:39:22.139 UTC** REST GET逐字读回；9736字符/14770 UTF8字节，body SHA256 `70e7291f8d1c9bb00f6f613125a269b59ffc6fe7446b6098e357cc94334d19dc`。读回前所有运行预算0；再次读取#34仅增加该预检至245、远端不变后才启动窗口。[原文](s10-p0-19-preflight.md)/[读回证据](evidence/s10-p0-19/preflight-api-readback.json)保留。

[执行冻结](evidence/s10-p0-19/execution-freeze.json) SHA256 `b916b620023321b7b74dcddd176d71a14e25f7a44d7a69e1ea5ec82e60300be0`；[SQL合同](evidence/s10-p0-19/sql-contract.json) SHA `78969e6a876dfa575db767676776f0b6eaa021bc0e955c08cde1a770829d6304`；[元数据合同](evidence/s10-p0-19/metadata-contract.json) SHA `a123eb53bcc5e2b193b4560638a977ffbc699480e3d04d297124a35950817f0d`。五个脚本和所有冻结依赖在运行后再次逐项SHA核对全等，未放宽合同。

## 指定修正及纯文件检查

原643表逻辑快照完整保留，包括不带ONLY的ir_actions。新增3条只读SQL限定pg_inherits/pg_class关系、tableoid→schema/table完整继承族投影和ONLY父表补验；现场确认5个直接子表、571条族记录、ONLY父表自身0行。比较键为`(schema, physical_table, id)`，显式拒绝重复物理键；普通表ID也拒绝重复，不以dict静默覆盖。所有共享字段逐项核对，原父表逻辑多重集须覆盖完整实际物理投影。

新增许可只限已先通过child字段门禁的`public/ir_act_url/571`在父表中的同物理记录投影；其它物理来源、同号异表、ONLY自身、业务字段、其它action等不豁免。当前真实父投影与child共享字段完全一致，实际仅write_date变化；这是**P0-19保存的新快照实测**，不能反推P0-18未保存的瞬时字段差异。

新实际`metadata_gate`和共享`guarded_import`直接用于纯文件正反例，最终 **33检查exit0**，无数据库/Odoo导入/Firefox执行。覆盖合法child与parent技术变化、parent/child不一致、同ID异表保留和变更拒绝、重复键、其它action、URL/name/type、额外view/XMLID/语言/模块/权限/金额、ONLY自身、提交后精确信号及超额拒绝。

共享事务路径以纯文件ledger覆盖成功、门禁拒绝、load/capture失败、落盘失败和commit未知：先fsync完整私有before/after/全diff及实际来源映射，再fsync并读回脱敏全变化索引；只有PASS才唯一commit，异常rollback/close。fixture的tableoid101..105及假cursor.commit明确不称原生测量/提交。[静态结果](evidence/s10-p0-19/offline-result.json)/[事务fixture证据](evidence/s10-p0-19/transaction-fixture-results.json)保留。未重跑P0-18或P0-17旧测试。

## 唯一原生窗口与完整元数据证据

| 步骤 | 真实结果 |
|---|---|
| W5源前 | 一条READ ONLY/RR连接，名/OID2100310/cluster7694897083368259627及643表签名与P0-18固定源后验匹配；实际继承族映射完整，无其它源活动连接；rollback/close先于CREATE。 |
| 唯一复制 | 一条显式维护连接、一次CREATE成功；新库`ydental_s10_p019_20261017021844_64f8a46b`、OID **2100330**，不同于全部旧catalog。独立目录/端口18319/config/data_dir/不可变marker；copy2复制152份文件，无硬链接或源回写共享。名称时间是冻结UTC标签，实际时刻由intent/日志固定。 |
| 副本加载前 | 独立READ ONLY/RR连接，643表及实际物理来源映射与本批源全等；完整差异在判断前落盘。 |
| 原生元数据 | 专用加载进程1、native backend **1389431**，官方convert_file固定XML调用1，显式idref={}、专用元数据env；exit0，完整证据保存并PASS后，唯一metadata COMMIT **1**。没有整模块升级或业务ORM。 |
| 独立提交后 | 第二条副本READ ONLY/RR连接；全部643表与物理投影通过原精确门禁，仅许可的default/templates各追加1条id/date。之后才启动Web。 |
| Web与Firefox | 各启动1，Web PID726717，Firefox engine PID726784。累计Web原生连接超过4即停止浏览器执行器并终止自有服务；Web exit0、Firefox engine日志exit0/signal null，控制器exit1。 |
| 停止尾审 | 第三条副本READ ONLY/RR连接；相较“提交后/Web前”全部643表及完整物理投影全等。W5后第二条只读连接与本批前643表/投影/文件封存全等；已用五条源/副本审计连接均rollback/close。 |

实际提交前差异已完整保存，原先P0-18取证遗漏没有重现：

| 实际记录/投影 | 提交前变化字段 |
|---|---|
| ir_act_url571 | write_date |
| ir_actions，物理public/ir_act_url/571 | write_date；与child全部共享字段一致 |
| ir_ui_menu320 | write_date |
| ir_ui_view1597 | arch_prev、write_date |
| ir_ui_view1598 | write_date |
| ir_ui_view1599 | arch_db、arch_prev、write_date |

五个ir.model.data原记录/映射不变；所有其它action、ONLY自身、关系/组/ACL/module state/version/schema/report action/template均原样。主view准确EN/ZH结构对应P0-17增量，两helper保持原语言键与业务结构。

[metadata-precommit全差异索引](evidence/s10-p0-19/metadata-precommit-diff-index.json)/[裁决](evidence/s10-p0-19/metadata-precommit-decision.json)、[独立提交后全差异](evidence/s10-p0-19/metadata-independent-diff-index.json)/[裁决](evidence/s10-p0-19/metadata-independent-decision.json)保留。私有完整before/after/全字段diff在gate及commit前已fsync保存，公开仅完整变化索引、列名及SHA，不上传原始行。

## 新阻断、实际连接与请求限制

原生HTTP日志有 **11条不同backend PID创建事件**，均标read/write pool/max4；冻结Web累计物理连接上限4被实际突破。池上限4限制池当时占用，不保证整个窗口累计只创建4条；固定core `odoo/sql_db.py:662–715`允许回收连接后再创建。日志确有回收及重新创建。本预检对此不足，不能把pool4当累计预算达标。

原生日志DSN还同时出现`postgres`和新副本。固定core `addons/web/controllers/utils.py:96–108`的新会话数据库选择可调用`router.db_list(force=True)`；`odoo/http/router.py:70–85`转到`odoo/modules/db.py:703–731`，dbfilter存在时可能连接db_system/postgres读取catalog。list_db=False及精确dbfilter不等于原生过程仅开新副本连接；该目录连接来源未在预检充分计入，不能宣称显式维护1就是全部catalog连接。

11条creation记录不含DSN，不能仅按线程日志上下文为每个PID精确归库。只实证累计11及两种DSN；不造每库物理连接数，不新增SQL补查，也未做PG/OS/网络专项。原生catalog读取不等于连接P0-13/14/18业务副本，日志未显示这些受保护副本DSN。

第5条连接创建在02:40:31.683，控制器保存停止错误的文件mtime约02:40:31.711，后续在途资源请求于服务正常停止前仍产生连接，最后一次在02:40:31.758；最终11是实际总数，不能截断为首次检测数或4。没有继续安排新业务步骤，也没有调预算/重试。

[完整连接事件及固定core依据](evidence/s10-p0-19/native-connection-events.json)、[脱敏失败片段](evidence/s10-p0-19/runtime-failure-redacted.txt)、[原执行结果](evidence/s10-p0-19/execution-result.json)保留。execution-result中的“metadata<=4/Web<=4”字符串是冻结上限描述，**不能当实际达标结论**；实际量在blocked-verification及连接事件中明确为Web11>4。

已完成的server日志只观察到login GET1和静态asset GET4，均200；没有观察到POST、工作台或PDF请求。浏览器执行器因预算异常被父进程终止，尚未保存finally中的完整浏览器request/response计数；这些内存计数不可得，故**没有完整浏览器/server核对，不能把已完成server5请求当全部已发请求，不能称精确实测login POST发起数0**。没有完成认证登录、工作台显示、真实链接点击或下载审计。没有截图/PDF文件，不能补用旧样张。

## 实际预算、业务不变量与未完成

| 项目 | 冻结上限 | 实际 |
|---|---:|---:|
| W5前/后独立只读连接 | 1+1 | 1+1 |
| 副本前/提交后/停止尾审只读连接 | 1+1+1 | 1+1+1 |
| 显式维护连接 / CREATE | 1 / 1 | 1 / 1；另有native Web postgres DSN，不能合并隐藏 |
| 原生metadata连接 / 原生Web连接 | ≤4 / ≤4 | **1 / 11（超预算）** |
| 元数据进程 / XML调用 / metadata commit | 1 / 1 / 1 | 1 / 1 / 1 |
| HTTP / Firefox上下文 | 1 / 1 | 1 / 1 |
| 完成认证登录 / 完成工作台 / PDF点击intent / PDF文件 | 1 / 2 / 1 / 1 | 0 / 0 / 0 / 0；浏览器发起计数缺失另列 |
| 新S01审计 / 身份session/device/user日志 / 技术附件 | 各精确预算 | 全0，尾审与源原行相同 |
| 经济/临床/库存/权限业务写、旧业务重放、执行者sudo、shell/install/upgrade/init/test、系统专项、产品修改 | 0 | 全0 |

物理连接合计18：源2+副本审计3+显式维护1+metadata1+Web11，不能以全部成功的只读门禁掩盖Web预算超额。metadata与Web之外的连接均不重试。

W5前后643表及物理投影全等；初始副本与源全等；已提交metadata涉及6张逻辑表（同一action物理记录在parent/child各有投影，加menu/view和两signal表），**其它637张表逐行全等**。副本提交后至停止尾审643表全等，旧152文件全等。account.move/line/payment/partial.reconcile、费源/价格/收退款/日结、文书/version、stock move/quant/lot、权限与旧附件全部原事实不变；740/0、既存500+240及20+40+80+600未重演、未重核销。

本批不能称“副本加载前与最终643表全等”：授权metadata已commit1并保留。也不声称PG序列、WAL或整库物理字节全等。[阻断核验](evidence/s10-p0-19/blocked-verification.json)固定所有比较口径。stopped-final-decision中的PASS只表示停止尾审捕获/索引完成，其detail明确not_a_success_gate=true，**不是Web或整个目标通过**。

原始快照/全差异/日志由[私有artifact索引](evidence/s10-p0-19/private-artifact-index.json)固定，仅留原机。冻结五脚本原字节保留；未把失败上限改成11，也未恢复旧窗口。P0-13/14/18不连接/复用/清理；refund14、close9/权限负向、refund13分页、旧文书确认、旧收500+240均未重放。

## 封存、撤回与交付

新OID2100330及独立目录/配置/marker/日志/全部差异保留，不DROP/覆盖/重置/复用。元数据1次合法commit保留，没有为Web失败另做逆向SQL或再次导入；无产品补丁需回滚。自有HTTP/Firefox PID均已不存在。后续只能在另有授权时先核原生数据库选择、catalog访问和累计连接预算，并使网络事件在中断前持久保存；本批不实施修复或启动P0-20。

原分支正常线性提交新增脚本/报告/脱敏证据，全部文件由[SHA256索引](evidence/s10-p0-19/sha256-index.json)固定，索引自身SHA与最终提交在正式回执中记录。脱敏失败片段用.txt明确纳入Git，旧P0-18文件与产品/core均不改。

在#34发布正式BLOCKED回执，REST GET正文逐字相等并保存后立即STOP，等待GPT独立复核。只请求如实BLOCKED证据复核，不申请UI/PDF限定PASS。S10技术/生产/T12仍BLOCKED；P0-18旧裁定不改，R3 UNKNOWN/W4 STOP/旧W5失败、历史原版PDF及生产政策缺口保留，不启动P0-20/S11、不合并部署、不改Issue/Project状态。
