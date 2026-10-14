# S10 Native D1.7-R2-F：唯一 L2 准备被诊断夹具基线断言阻断

## 授权与固定身份

唯一授权为 [#34/6164999858](https://github.com/Yredxin/YDental/issues/34#issuecomment-6164999858)。从固定远端及本地 HEAD `4f7e4415e9dfa3b373530b549fd4af8aaf46b97c`、原分支 `codex/s10-settlement-finance-r1-20261013` 的干净工作树开始。固定 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 均未修改。venv Python 3.12.15，PG `127.0.0.1:5432`、cluster `7694897083368259627`。显式 GitHub API GET 取得 #23/#34 正文及各 3/57 条全部评论，授权逐字匹配且是开工时最新裁定；#35 OPEN、0 评论。

原事故 OID2056451、唯一纯 92 模块模板 OID2100080、L1 OID2100086、L2 失败 OID2100087、R1 失败 OID2100096 均只读核对匹配。原事故配置 SHA `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、崩溃 marker SHA `d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78`、原 SIGSEGV 日志 SHA `f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6` 在事前、事后仍匹配。

## F0：旧孤立文件来源

两座旧失败库各比 124 文件的纯模板多 6 个文件。权限 700/600 私有证据逐文件记录相对路径、大小、mtime/ctime、MIME、SHA；公开证据仅给分类和私有清单哈希。每库有 3 个 305 字节 SVG 及 3 个对应的零字节 `checklist` 文件。SVG 文件哈希逐个等于锁定 Odoo20 `avatar_mixin.py:79-88` 根据合成用户名首字母 D 和其 32 种允许色生成的完整字节；SHA1 扇出路径也一致。原生 `res_users.py:663-680` 在创建无图内部用户时自动写头像；`ir_attachment.py:155-162,230-242` 在文件写前建立零字节 GC checklist。独立只读 PG 用固定 OID/cluster 和 5 秒超时核对，两库均仅有 70 条原系统附件、对所有新增 SVG 的 `ir_attachment.store_fname` 引用数为 0。文件 mtime 均落在 registry 加载以后、相应夹具报错以前；旧夹具恰创建三名合成用户。**文件字节为原生合成头像模板、checklist 机制、零附件引用是 PROVEN；逐个文件的具体 ORM 调用堆栈没有保留，归因于该批用户创建是 LIKELY。** 无原始 SVG 内容被打印、导出或上传。旧文件、日志、attempt ledger 保留，未删除或修改。

由此建立新 filestore 的严谨边界：124 基线文件逐 SHA 不变；每个新增文件必须是可解释的合成用户头像或有合法 `ir.attachment` 来源且内容类型受控；不明或未引用文件一律阻断后续窗口。新库事后也按此规则保全和归类，没有把孤立文件静默视作成功附件。

## F0：依赖、工具与第一检查点

按[上轮全链矩阵](s10-native-d17-r2-dependency-matrix.md)复核 S01 身份、S07 唯一仓库/材料/入库、S03 能力/营业日/发布槽、S05 目录/价、S06 显式队列参数和报到/租约、S08 文书/执行/费用。新私有夹具中仓库 setup 仅一次且先于 S05 受控价目表；合成 `heartbeat=2`、`timeout=600` 由原生 `ir.config_parameter.set_str` 显式写入，并在首次 report 前用原 `ydental.queue.service._settings()` 读回 `(2,600)`。这是合成测试参数，不是生产批准。预计最多 180 秒准备目标时限小于 600 秒租约，但实际动态时间边界仍由现有服务判断。S05 受控价目表 × S07 事后新增仓库的产品级兼容问题继续 **UNRESOLVED**。

模板事前读回 92 installed 模块、业务表 0、70 系统附件、124 基线文件、外部模板连接 0。`py_compile` exit0；未修改队列 `_settings` 真函数 AST 3 正 12 负 exit0；未修改 `ydental_settlement_test.pre_init_hook` 真函数体 1 正 12 负 exit0；私有 FakeEnv/FakeCursor/clone/guard/PG observer 16 正 26 负 exit0；专门顺序及 GDB/PG 白名单静态检查 exit0。模拟结果全部标记 **SIMULATED**。GDB 17.1 只在私有库环境可启动，目标 GDB 脚本显式 `unset environment LD_LIBRARY_PATH`，signal11 时配置全线程 C 栈、共享库和进程映射；CPython Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`，完整 CPython/部分扩展 debug_info 缺口未消除。一次离线工具目录替换/断言失败、一次模拟脚本路径失败、一次静态检查引号失败和一次只读摘要脚本误把模块数当列表的 exit1 均保留为诊断工具失败历史，修正后仅离线复核，不计 Odoo/CREATE。GDB 裸启动因缺私有共享库失败，使用既有专用 `LD_LIBRARY_PATH` 验证版本 exit0；未污染 Odoo 目标。

在任何 CREATE/Odoo 前，[第一强制检查点 #6165199842](https://github.com/Yredxin/YDental/issues/34#issuecomment-6165199842) 已发布并通过 API 逐字读回，正文 SHA `14019ae2087f75b81c5c579de325cf551b330c2b35cca4586015e799451ca0b1`。检查点给出准确 CREATE、准备及条件双 GDB 命令、预算、STOP 和旧文件匿名分类。**该预检漏掉了诊断夹具对模板 `mail.message` 的绝对数量断言；这是本轮事实揭示的静态覆盖缺口。**

## F1：唯一克隆与准备目标的真实失败

唯一新库 `ydental_s10_test_20261014092245_1d9a6dd0`，OID **2100105**，原 cluster，独立端口18256；使用独立 postgres 管理连接、任何 SQL 前 autocommit、IDLE 状态、`psycopg2.sql.Identifier` 从唯一纯92模板 `CREATE DATABASE … WITH TEMPLATE …` **一次 exit0**。独立配置 SHA `f93df8abd56e2a0e8eba291fd9201fabb98975651704c7d1f9e2c2c4f078a01e`，marker SHA `6973b84e3626c478111082c13b946e2c3a6d00cd786445fbae716970d2513095`，124 个安全源文件逐 SHA 复制。真实新 OID 下原 hook 函数体离线 stub 与私有 config/marker/loopback/禁 SMTP/cron0/严格 dbfilter guard 均通过；准备前92模块及交易表0。

仅启动一次 GDB 父进程 PID **2631663** 下的 Odoo shell PID **2631671**，registry 92 模块加载于 `2026-10-14 09:26:59.517` 至 `09:27:00.177` UTC。真实目标正常异常退出码 **1**、GDB exit **1**、外层准备命令 exit **2**；signal11 **0**，无 Native C 栈。原始日志 SHA `f16dc1d22971bd14e2cc48f4e84378cacb2a1cc36a678775f49614ce4bd30555`。私有一次性准备 ledger SHA `25cb9777a87df46961cbfe23f7e1e7cc42292b402aec82884e39adc7ba654e09` 保留。

失败位置是私有 `l2_fixture.py` 的 **`mail.message` 全库计数 >100** 拒绝，发生于真实治疗/库存服务调用之后、唯一事务 commit 之前。独立只读 SQL 证明纯92模板本来就有 **851** 条 `mail_message`，失败新库回滚后仍是 **851** 条；`mail_mail` 两库均 0。因此这是诊断夹具把全库总数误作本次新增上限的**必然失败断言**，不能推为产品配置或 Native 故障，亦不能把此前内部服务调用当作已提交的 event/fee/stock 事实。事后新库患者、治疗 event/fee、库存事件和 stock.move/quant、account.move/payment/partial、S10 source/payment/refund/close、sale/purchase 交易表均 0；没有达到允许 B 的已提交 L2 状态。事后独立只读 OID/cluster 复核旧库和模板不变，模板无外部连接，原进程已退出。

新 filestore 为 124 基线 + 4 新文件：2 个头像 SVG（逐SHA精确匹配同一 Odoo 合成头像模板及SHA1路径）+2 个对应零字节 checklist，4 个均无提交后 `ir.attachment` 引用；124 基线文件逐SHA仍等于模板。这些文件及新库、日志均原样保全；私有分类清单 SHA `a5c5a54819f6e54fec8ee3421d50001db95a57bc74b71817b20c425a31f0c0a6`。未删除、移动、清理或补写任何文件/DB记录。

**A FAIL，第二 GitHub 放行检查点未发布，F2 双 GDB/Odoo目标 0，PG 并发观察器 NOT_RUN。** 本批实际 CREATE 1/1、准备 Odoo 1/1、B Odoo 0/2、总 Odoo 1/3、Firefox0，安装/升级0，重试0。不能称 L2 或 Native 测试 PASS。虽然这次是诊断夹具基线断言而非缺少队列参数，仍按“失败即停”和不继续第四次同类 L2 建库试错处理。旧产品/固定 runner/Odoo20/venv/历史数据库与 filestore 不修改；Project mutation0，#34保持OPEN，#35/S11未启用，未合并/强推/生产部署。

## 证据、已知与后续复核范围

私有原始证据目录 `.local/s10-native-20261014-6164999858-d17r2f/` 及 `.local/ydental_s10_test_20261014092245_1d9a6dd0/` 权限700、文件600。旧文件逐项清单 SHA `ed16e49739d0855b6a3947edaa82e0393fd6cda083f1747e702307436cf8de09`，旧库只读引用结果 SHA `a1b53e3c0cffbb26f70ed82d4670822385e90d8915bbe93dd7eaec10956eb172`，Odoo精确头像模板哈希匹配清单 SHA `cee2cb74c3a805f5dd9105039958d4b3879b2ca3b7399ce9680668e19b874981`，新库事后只读聚合 SHA `26b86fd446af8d2f7206483ccc0b0c272f476600e8e64d3928123db714b7cbb9`。所有原始 GDB 日志、配置、文件路径和可能敏感内容不上传。脱敏[机器证据](evidence/s10-native-d17-r2f-blocked/diagnostic.json)记录命令、退出码、身份、SHA及预算。

已证实：旧 6+6 文件为合成头像模板与GC checklist；新库唯一 CREATE 与 A 失败；`mail_message` 模板基线851导致错误绝对阈值；事务业务记录回滚；无本次 SIGSEGV。推断：每个旧头像对应哪一次具体 ORM 用户创建缺逐条trace，但时间及合成用户名吻合。UNKNOWN：原 PID2383730 的 Native C 内存根因；S05×S07 产品级反序兼容；这次已回滚的最小L2图若排除错误断言是否完整合法。下一步须由 GPT 另行决定是否停止该 Native L2路线，转向 S05/S07 产品兼容及 Native 符号/堆栈调查；本批不改断言、不复用新库、不追加进程。**S10技术和生产持续BLOCKED。**
