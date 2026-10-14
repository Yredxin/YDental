# S10 Native D1.5-L1 有界取证报告

## 1. 授权、范围与固定身份

唯一执行授权为 [#34 评论 6161475560](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161475560)。本批只执行一座纯合成库的 S01 最小状态准备及一次双 GDB 下只读 Odoo shell 窗口。第一、第二强制检查点分别为 [6161576259](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161576259) 和 [6161608003](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161608003)，均在相应 CREATE/B 窗口前通过 GitHub API 逐字读回。

固定分支 `codex/s10-settlement-finance-r1-20261013`，开工本地及远端 HEAD `abdd047b2c777fb6d86510409875950142d2ff9f`；product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`，Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。完整读取 #23 正文/3 评论、#34 正文/38 条开工前有效评论，最后裁定即本次授权；#35 OPEN/0 评论。工作树开工干净。PG `127.0.0.1:5432`、cluster `7694897083368259627`；Ubuntu venv Python 3.12.15、私有 GDB 17.1。

## 2. 纯合成模板及新库保护

唯一模板 `ydental_s10_test_20261014044700_4f6a8d2c`/OID2100080：92 installed 模块名称/版本与固定清单相等，模块清单 SHA `c1bbaa9395bd01d9e11912d56b73155d2b6cd63d3fbf1f58de0404d58e66b8a0`；16 类患者、临床、结算、原生账、库存、采购和销售交易表均为 0；70 条系统附件及 124 个 filestore 文件与安全清单逐 SHA 相同，模板无活动连接。configSHA `582f73fdee28cac3d9f63d116bb934e0def3b19fa5ddb7e10c054ba1ef20cb43`、markerSHA `df8ff92d38499745b6ecfffaecb7eaff739ff29066c243b13b15b3a1bf99bb7b`。

只执行一次 `CREATE DATABASE`：新库 `ydental_s10_test_20261014052222_5457e39f`/OID2100086，专属端口18253，configSHA `1b97e9c77e4588061a5655313b96f18a255aab854bb59cf9dba7635d3f3c4fba`、markerSHA `0acfbb966a1746db3e79506971dbd00ecfea5767009ea0c967eea6eda4957529`。管理连接在任何 SQL 前开启 autocommit 并核对 IDLE，以 `psycopg2.sql.Identifier` 引用目标和模板。新库独立 dbfilter、data_dir/filestore、marker、权限700/600、loopback Python 网络策略、SMTP 127.0.0.1:1、cron0。克隆 124 个安全文件并逐 SHA 验证；实际新OID下以独立只读PG连接运行原 guard 验证通过。非 Python native 外发不能由进程内 socket policy 单独证明；L1 代码无外部接口调用，mail_mail 实际为0。

原事故库OID2056451、纯91模板2078375、D1.2库2100078、D1.4失败库2100079及纯92源2100080全保留且OID不变。原事故 configSHA `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、SIGSEGV 日志SHA `f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、markerSHA `d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78`在本批核查时相同。

## 3. L1 准备与实际记录

原未授权草案 SHA `6ebecb71c39358485b28ffff15ae009686a36a1a15f754923729658f3e5d0c28`未改。私有一次性副本 SHA `7f77aa33257af94f1316007e3a05ff6f1c83cb21e856343f06bf07840ef1db15`绑定本授权、唯一新库和随机 key；保留 database/OID/cluster/core/core_sha/configSHA/source_oid/network-policy/egress/fixture-key全部 guard，在自有ORM cursor写前再次验证实际OID/marker。尝试文件以 O_EXCL/fsync 落盘，禁止第二次准备。`new_test_user`使用`.invalid`合成邮箱和禁重置通知上下文。离线 py_compile/AST/mock 正负通过，模拟不冒充Odoo运行。

A 的唯一 GDB/Odoo 目标：GDB PID2495186、Odoo PID2495194、PG backend427937，app `s10_d15l1_prep`；registry UTC 05:26:41.435—05:26:42.106，GDB及目标 exit0，真实 signal11=false，私有日志SHA `9b71811c7115178a22792a4ee3bbb5896864d188634408ab8a9a83965d90b68c`。只提交一次自有 cursor 事务。独立只读SQL显示相对模板新增：一个合成门店、一个 manager 用户及 partner、一个 hr.employee、一个 membership、一个登录会话、frontdesk:write 和 medical:write 各一条。原生自动副作用为4条S01审计、5条内部通知、10条合成 partner/employee 系统头像附件；mail_mail仍0。两个新增 filestore 文件为相同系统SVG和0字节 checklist，来源已按附件模型和ID验证。**会话已创建但未选店**，所以此窗口不能证明“已选店会话”条件。患者、治疗/检查、费用、结算、原生 account.move/payment/partial、stock.move/quant、销售采购交易仍均为0；92模块不变。

## 4. 一次双 GDB 只读捕获

第二检查点读回后只执行一次 B，两个独立 GDB 父 PID2496741/2496743，目标 Odoo OS PID2496758/2496757，PG backend PID428521/428520，app `s10_d15l1_a/b`。两目标都仅加载registry并读取已安装模块、`pg_backend_pid()`、`application_name`，没有运行 `concurrency_actor.py`、bill、收退款、日结、库存或其它业务动作。两者 GDB/目标均 exit0，未捕获 signal11；日志 SHA分别 `a399d3021e1aeab1adfefd04eeb8470c7b908ab16658b4480aa26bc7643986f2`、`90c5b3e30fa1d974378568ab156be412f4fc9aeed07e39039036a0ffec9554ef`。GDB日志中的 `Catchpoint 1 (signal SIGSEGV)` 是捕获点设定，**不是事故发生**；均有 `exited normally`，无 `NATIVE_CAPTURE REAL_SIGSEGV`。

registry窗口A为05:29:21.107—21.912，B为05:29:21.107—21.917 UTC，重叠约0.805秒。只读PG观察器在postgres管理库 autocommit/逐样 IDLE，54次采样中22次同一样本同时见两个白名单 backend，真实观察器日志SHA `3dff96cb7ebd0b1e2c22b79aaa51566341c022ac4af65e87ceac325ab4148a79`。B前后完整L1聚合JSON逐值相同，SHA均 `e2916c5524ef13a1cb1eb4096536eb8d9471dcaef29252d4f1d9a0008e5f271b`。停止信号发往自有进程组次数0；无遗留本批目标。

这一次L1有限窗口未复现原SIGSEGV。因没有真实 signal11，**没有产生 Native C 崩溃栈或事故时共享库映射**，不得将正常退出称为根因修复。离线 ELF Build ID：Python `7713d416ece8f53a2b37e61dd06defd7bf795954`、psycopg2 扩展 `58c8f5ff9bcddcb79c4fded8945032a13b308488`。

## 5. 命令、退出码与失败历史

|实际命令或动作|退出码/结果|
|---|---|
|`gh api`完整读取#23/#34/#35、两条检查点POST及API逐字读回；`git`/core/PG身份|0；末次评论列表核对首次误用`-f`触发无body的POST而HTTP422/exit1，未产生评论，改`--method GET`后exit0|
|`../.venv/bin/python .local/s10-native-20261014-6161475560-d15l1/audit_source.py`|首次因脚本排序假设/旧表名分别exit1；只读修正后exit0，源身份92/16表0|
|`py_compile`/AST、原/激活guard fake、clone/PG观察器fake、GDB命令静态检查|0，全部SIMULATED|
|`../.venv/bin/python .local/s10-native-20261014-6161475560-d15l1/l1_capture.py clone`|0；CREATE一次|
|`.../l1_capture.py prep`|0；GDB/Odoo目标各一，signal11=0|
|A后通用filestore验证器|首次exit1，误以为Odoo自动头像是来源漂移；独立只读查明10附件/2文件，保存首版并严格限定修正后exit0；**A未重跑**|
|两条独立只读SQL元数据探针|分别因Odoo20 `res_users.email`/`mail_message.res_model`列名误用exit1；按实际schema修正后exit0，未发生写入|
|`../.venv/bin/python .local/s10-native-20261014-6161475560-d15l1/l1_capture.py window`|0；两个GDB/Odoo目标正常、有效重叠和PG观察|
|`.../audit_after_a.py` A后与B后两次只读聚合|0/0，结果相同|

私有捕获器检查点首版SHA `119d48a0945de009235ae12bb542538507f8b83a3eee1fa5c8efa75bc29bb3a1`，仅诊断验证器收紧后的SHA `3080dfc2bcb1028014f7f145756c64391308234bce4a3a55996f671d6b2b0ec5`；原失败和源码均保留。没有修S10产品或重新运行A。

## 6. 已证、UNKNOWN 与可证伪建议

已证：纯92零业务模板安全身份；一座新合成库、一次CREATE；一次A准备真实S01最小图；一次两目标真实registry重叠与同采样PG后端；本批三个Odoo目标均exit0且无真实SIGSEGV；B前后L1数据不变。**只说明本窗口未复现**。

UNKNOWN：原PID2383730的C栈/共享库实时映射、具体native根因和复现概率，L1已选店会话或更大用户数量的作用，原事故临床/库存/confirmed fee与账款规模的相对作用，以及非Python native外发的全局证明。本批不能排除任何低频时序故障。下一次若GPT独立批准，应先只读核对原事故业务actor前的会话选店事实；再选择一个新隔离库和**一个**可区分“会话选店”与“临床费/库存状态”的最小假设，不复用本库或自动进入L2；分别明列准备目标与两个GDB目标预算。只有真signal11及完整C线程栈可推进归因。

## 7. 证据、权限及保全

[机器可读脱敏索引](evidence/s10-native-d15-l1/diagnostic.json)含授权、数据库、PID、退出、SHA、记录类别、采样与UNKNOWN。原始配置、GDB日志、PG全样本、文件清单和私有激活脚本仅保留 `.local/s10-native-20261014-6161475560-d15l1/` 与 `.local/ydental_s10_test_20261014052222_5457e39f/`，目录700/文件600，不上传凭据、原始栈/core、患者或支付数据。所有历史S00—S10数据库、卷、filestore、日志、备份不删除、不覆盖；仅新增这一座授权纯合成库。Odoo20 core、odoo-12、历史venv与S10产品/固定业务runner未改。

## 8. 结论与复核请求

本批 CREATE **1**、A Odoo **1**、B只读Odoo **2**、总Odoo **3**；Firefox **0**、install/upgrade **0**、Project mutation **0**。#34/#35保持OPEN，本批只发表两个授权检查点和最终复核评论；未改Project、未关闭Issue、未合并/强推、未启S11、未部署生产。请GPT按GitHub固定证据独立复核这一次有界反例及仍缺的C栈。本报告**不申请自动恢复S10 D2或任何后续Native进程**。S10全阶段BLOCKED，生产BLOCKED，原Native SIGSEGV根因UNKNOWN。
