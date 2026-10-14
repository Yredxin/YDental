# S10 Native D1.2 双 GDB 并发只读窗口报告

## 授权、范围与结论

依据 [#34 GPT 授权 6160489830](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160489830)，本批从原分支固定 `48c09ca3e414ec771ab6ffc24bce77e030ee43c6` 开始。固定 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 均未修改。开工前通过 GitHub API 读取 #23/#34 当前正文和全部有效评论、#35 OPEN/0 评论；本地与远端 HEAD、origin、干净工作树、Ubuntu venv/PG/Docker 身份匹配。

**两个独立 GDB 父进程下的 Odoo shell 确实同时加载 registry，加载窗口重叠 0.787 秒；两者正常退出，未捕获 SIGSEGV。** 这一次缩小范围的窗口未复现原事故，不证明原生稳定性或根因修复。没有真实 Native C backtrace，根因 **UNKNOWN**。S10 全阶段与生产持续 **BLOCKED**，本批没有 D2、财务/库存业务竞态、Firefox 或产品开发。

## 模板源资格与差异

只读模板源 `ydental_s10_test_20261014034100_b9c74e20`，OID2078375、cluster `7694897083368259627`、configSHA `7f371fd1775aac4a10fdea92c467ff0ee504250856e6ae1e76f41aeef3e46dc8`、markerSHA `04d91a259f3368fe4f4b767f09fc9a9af228b49cd7a0489f3bf0415d7026bf2c`；克隆前活动连接0。原事故库 OID2056451仅校验身份，绝未作为模板。模板91个 installed 模块含 `ydental_settlement` 与必需依赖，原事故库92个，仅多 `ydental_settlement_test`；原事故库另含已执行的业务场景。本批克隆仅复制纯合成安装结构，**不是原事故环境的完全同态复现**，也不重新 install/upgrade。

只读审计265张 `ydental/account/stock/sale/purchase` 相关表，患者、治疗/检查、结算、账单/付款/核销、销售采购、库存流水/数量业务表均0。非空仅安装配置（如50科目、7日记账、4税、12仓位）、6张互斥锁记录及7条带安装 XML ID 的工位资源；`res.partner` 仅5条 Odoo 安装默认对象，无后续新增。70条 `ir.attachment` 全属 Odoo 系统对象，临床/结算附件0，创建时间均在上一轮安装窗口。filestore 124文件约389KB：62个未引用文件全部0字节，其余为系统安装图片、JSON、SVG 和文本；附件引用缺失0。源文件清单/逐文件SHA及附件元数据在克隆前重验，仅只读复制到新目录。源审计两次最初按旧schema选列触发`UndefinedColumn`，无PG写入，随后按真实列修正并通过；失败历史保留在私有审计记录和本报告。

在任何 CREATE/Odoo 前，已发表 [D1.2 强制检查点 6160673421](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160673421)，经 GitHub API 逐字读回，正文SHA `bc788e23a54b68e1361fa09af98c48aa26ebdfb9dc9ce0f9ed74aa719d76473c`。新私有工具目录 `.local/s10-native-20261014-6160489830-d12/` 权限700、文件600。上一轮修正版工具SHA `55b1ff71e5ab1435327baf60ef57676b2a264a04f514264a27f5efa8dc18448a`；本批克隆/并发工具SHA `9df4b841b59026e926de58442002060c5d31dd0e0b44d481fa2251b9c4310753`。`py_compile`、AST、fake连接负向测试均exit0：事务中/非autocommit/错误模板或目标/OID漂移/已有连接拒绝，仅auto+IDLE可组成一次双Identifier CREATE。两份 GDB 脚本曾以非Odoo `/bin/true` 验证预入口双屏障，同步释放且两个GDB exit0；这不算Odoo或SIGSEGV复现。

## 唯一克隆和双 GDB 窗口

准确包装命令各执行一次：

```bash
../.venv/bin/python .local/s10-native-20261014-6160489830-d12/d12_capture.py clone
../.venv/bin/python .local/s10-native-20261014-6160489830-d12/d12_capture.py run
```

`clone`在独立 `postgres` 管理连接、任何SQL前设置`autocommit=true`并检查`TRANSACTION_STATUS_IDLE`，通过 `sql.Identifier` 仅执行一条 `CREATE DATABASE "ydental_s10_test_20261014040500_d12a7c61" WITH TEMPLATE "ydental_s10_test_20261014034100_b9c74e20"`；**CREATE尝试1/1、exit0**，没有DROP/ALTER/覆盖或断开模板连接。新库OID**2100078**、cluster原值、端口18250、严格dbfilter/专属data_dir/filestore/网络guard；configSHA `555a0ed75dbd9753a7621b8cc6baf14bf2a0202372eb51cfdeadccc7cf60adb3`，markerSHA `cb45972670d3a260fc4d496c91101c4ea17185a3466aaf131231c9bf1efc5951`。124文件逐SHA复制一致；新OID、原模板OID2078375和原事故OID2056451均由独立只读PG复核。数据库UUID可能沿模板复制，因此身份守卫依赖新OID、cluster、config、marker与路径，不用UUID替代。

两份 GDB 脚本均在目标入口 `starti` 暂停，独立父进程到齐后按同一时间释放；各自目标均执行 `odoo-bin shell -c <新配置> --no-http`，只读 `env` 查询模块与 `SELECT pg_backend_pid()`，本地文件仅用于同步。GDB父进程私有`LD_LIBRARY_PATH`不传给目标，捕获点设SIGSEGV，真实触发时准备输出线程、完整C栈、共享库与映射。实际结果：

| Actor | GDB PID / Odoo PID / PG backend PID | Registry 加载 UTC | GDB/目标结果 | 私有GDB日志SHA256 |
|---|---|---|---|---|
| A | 2450736 / 2450752 / 411701 | 04:09:04.067—04:09:04.878 | exit0/正常、无signal11 | `af8e99acfae43d962ba5e0bd9b9baf4ab38b929e3cc66d93ba5ec60044fd39be` |
| B | 2450738 / 2450751 / 411702 | 04:09:04.091—04:09:04.897 | exit0/正常、无signal11 | `25928b590a4bfb1d90b43253323cf84a066c094d2426f101f10ef6538e3af128` |

两组Odoo目标OS PID不同、PG后端PID不同，registry日志时间段重叠 **0.787秒**；shell只读canary分别给出后端PID。总 Odoo 目标 **2/2**、GDB父进程2、模块安装/升级0、Firefox0、真实账款/库存业务动作0。日志中各有一行`Catchpoint 1 (signal SIGSEGV)`，只是捕获点设定；均无`NATIVE_CAPTURE REAL_SIGSEGV`，尾部为正常退出。守卫未发送SIGINT/SIGKILL，窗口exit0。初始可用内存约5.4GiB，窗口内最低约4.98GiB、磁盘最低约18.52GiB，未触发120秒/资源停止阈值。窗口后265表与模板逐表行数完全一致，原生交易表仍0，模板/新库deadlock0，所有自有GDB/Odoo进程已退出。

**取证限制：** 运行器的54次`pg_stat_activity`轮询全部为空，是监测连接误用`with psycopg2.connect(...)`事务上下文后即使设置autocommit仍持有`INTRANS`统计快照。只读PG对照实验证明独立管理连接可见临时新库backend，而原监测写法在连接存在时仍看不到。此项原始失败保留，不能拿空采样宣称没有PG连接；两个真实backend PID来自各Odoo shell的只读canary。另一次窗口后只读勾稽最初使用不存在的检查事件表名而exit1，按当前schema重做exit0；未启动Odoo重测。这些是取证工具限制，不涂改原始54条采样或声称监测全部PASS。

## 证据、事实边界与下一步

原始GDB日志、配置、逐文件源审计、附件、过程采样、同步时间、工具和失败记录只在上述私有工具目录及 `.local/ydental_s10_test_20261014040500_d12a7c61/` 保存（主目录700、文件600；Odoo自建缓存目录有更严格500权限）。公开 [脱敏机器索引](evidence/s10-native-d12-window/diagnostic.json) 提供新库/进程/信号/退出/哈希；不上传raw Native栈、配置、密钥或患者资料。原 S00—S10 库/卷/filestore/core/日志全保留；Odoo20 core、odoo-12、S10产品、Project与Issue状态未改，无合并、强推、S11或部署。

已证实：这一次在纯合成安装态、两个独立GDB/Odoo shell的registry重叠条件下未触发SIGSEGV。未证实：原事故的C栈、Native根因、与S07/S08-C/S09事故是否同源，以及更完整原业务环境的并发稳定性。下一步仅建议GPT评估是否另行授权针对原事故92模块及真实actor前置状态设计可证伪捕获；本批不得自行增加第三目标或重跑。**S10技术和生产继续BLOCKED。**
