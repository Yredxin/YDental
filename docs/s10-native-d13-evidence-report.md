# S10 Native D1.3：只读差异取证与 PG 观察器验证

## 范围和固定身份

依据 [#34 最新 GPT 授权 6160777256](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160777256)，本批只调查证据、修正监测工具并设计下一实验。已通过 GitHub API 读取 #23/#34 正文及全部有效评论、#35 OPEN/0 评论；起点为远端和本地同一 `bdc4a312466fe30e4cd142de55598ce73b4fc914`，原分支工作树起始干净。固定 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 均未改。Ubuntu 26.04.1/kernel 7.0.0-38-generic；本次可用内存约 5.4 GiB、根盘空约 19 GiB，仅为本次快照。PG endpoint `127.0.0.1:5432`、管理库 `postgres`、cluster `7694897083368259627`。CPython 3.12.15 ELF Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`、可执行文件 SHA `0886fb76ceec8ff568d23079b5da6342bb41675e216e11525d4d6a9e65988d10`；D0 的 47 个 venv native 扩展在当前逐 SHA 匹配、缺失0、已知 ldd 缺库0。这不证明事故时进程内映射/堆状态相同。

本批 **Odoo/GDB 下 Odoo/Firefox 启动均0；新库创建0；产品/固定测试 runner 改动0；Project mutation0**。唯一运行自检是获准的两个非 Odoo 管理库只读 PG 会话。S10 技术及生产持续 **BLOCKED**。

## 事故与 D1.2 差异矩阵

只读 SQL 逐项读取 `ir_module_module(name, latest_version, state)`：事故库92个 installed，D1.2库91个，共同91个名称、版本、状态逐项相同；唯一额外项 `ydental_settlement_test` 版本20.0.1.0.0。完整模块清单见[脱敏机器索引](evidence/s10-native-d13/diagnostic.json)，原始 SQL 输出保存在私有目录。三库数据库OID均重核：事故 `ydental_s10_test_20261014020300_8b6c1d4e`/2056451、模板 `ydental_s10_test_20261014034100_b9c74e20`/2078375、D1.2 `ydental_s10_test_20261014040500_d12a7c61`/2100078。

| 类别 | 原事故实际值 | D1.2实际值 | 可能影响复现、已知程度与下一次证伪 | 证据 |
|---|---|---|---|---|
| 模块注册 | 92 installed，多 `ydental_settlement_test` 20.0.1.0.0；其余91名称/版本一致 | 91 installed | **可能**改变模型类注册和缓存路径；作用方向 UNKNOWN。下一次在全新安全合成库按原 guard 合法安装第92模块后只读观察 registry，不能把缺模块直接当根因。 | 本次只读 PG 全清单、addon 源码 |
| 业务数据 | 患者10、治疗事件226/费225、检查结果2、结算源17、收款66、退款66、日结63；原生 move93/payment70/partial73、stock move238/quant38、sale/purchase 各1 | 所列业务/交易表均0；仅系统安装资料 | **可能**影响 `res.users.context_get` 读路径、ORM缓存与内存对象量；哪一项必要 UNKNOWN。先做纯92模块实验，再按授权只用新合成库逐项构建最小前置状态。 | 本次只读 PG 267表统计；104表行数不同、163表相同 |
| 配置与数据库 | OID2056451，config SHA `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`，端口18247，独立 filestore/dbfilter | OID2100078，config SHA `555a0ed75dbd9753a7621b8cc6baf14bf2a0202372eb51cfdeadccc7cf60adb3`，端口18250，独立 filestore/dbfilter；来自纯安装模板OID2078375 | endpoint/cluster及基本配置相同；具体库/数据目录不同是隔离要求，不可用原事故库作模板。 | 只读 PG、两份原配置字节 SHA及非敏感配置项 |
| Python/native | 同一锁定 venv 解释器路径；事故 faulthandler 列出17个已加载扩展，真实 C 栈和进程内映射缺失 | 同一锁定解释器；GDB退出正常，没有崩溃时扩展加载清单或 C 崩溃栈 | 当前47扩展 SHA 与 D0 清单一致；事故/D1.2运行时映射及堆布局 UNKNOWN。真 SIGSEGV 时才可用 GDB C 栈/ELF 比对。 | D0 native inventory、事故日志、D1.2 GDB日志、本次 SHA核对 |
| 环境变量/启动器 | 两个直接 Odoo shell；`PYTHONFAULTHANDLER=1`、项目网络 guard、`PGOPTIONS`、S10 actor/race 标记和私有路径；业务脚本送入stdin | 双 GDB `starti` 屏障后启动各自 Odoo shell；GDB私有 `LD_LIBRARY_PATH` 已在目标前 unset；相同类型的网络 guard/`PGOPTIONS`，另设 `PGAPPNAME=s10_d12_a/b`，只读元数据脚本 | GDB时序和启动环境微差可能影响偶发错误；目标共享库未被 GDB私有路径替代。需相同目标环境和独立实时监测；GDB扰动仍 UNKNOWN。 | `scripts/s10_r3_race.py`、D1.2 GDB脚本和原始日志 |
| 两进程/registry时间 | OS PID2383729/2383730；92模块；约02:08:25.313至26.116及25.313至26.114，两registry区间重叠；2383730在 registry loaded 后、stdin业务动作前 SIGSEGV/-11，另一因守卫 SIGINT/-2 | GDB父PID2450736/2450738，目标PID2450752/2450751，canary PG backend411701/411702；registry 04:09:04.067—04.878与04:09:04.091—04.897，重叠0.787秒；均正常exit0 | **已证**都曾双启动窗口重叠；原事故无独立实时PG监测。下次要用修正观察器与日志同轴核对，且区分真实 signal11 和守卫中断。 | 原 `race-bill-*.log` / crash marker、D1.2 `gdb-*.log` / window-result |
| 权限及探针边界 | `res.users.context_get` 等 shell 自身调用可见；actor付款/出账代码尚未执行；原业务用户和读取数据是否已经进入缓存 UNKNOWN | 只读 shell `env` 读取模块和 `pg_backend_pid()`，无业务动作 | 崩溃位于原 actor 动作前，不能说财务并发触发。下次须记录精确 stdin 开始边界及只读调用，不执行业务写入。 | 原 Python faulthandler、D1.2 canary |
| 资源/调试符号 | 事故时瞬时 CPU/RAM/shm/进程映射 UNKNOWN；无 core；无 Native C 栈 | D1.2初始可用内存约5.4GiB、窗口最低4.98GiB，未触阈值；GDB17.1有 glibc 调试符号，完整CPython/全部扩展 `.debug_info`不足 | 资源失压不能证实或排除；下次保留同时间轴资源与真实C栈。 | D0报告、D1.2窗口报告 |

`ydental_settlement_test` 静态审查：manifest 只依赖 `ydental_settlement`，声明 `pre_init_hook`。hook 检查独立 `ydental_s10_test_YYYYMMDDHHMMSS_hex` 库名、同名私有目录、marker中的数据库/OID/cluster/Odoo core与配置 SHA；**不得绕过**。其 `__init__` 导入 models，唯一模型 `ydental.supply.service` 的 AbstractModel 扩展重写 `_allow_demo_supply`，调用 guard 后返回 True。无 XML/测试目录/额外资产、无显式 ctypes/cffi/native wheel 导入；注册一个 Python 模型扩展可能改变 registry 对象图，但静态阅读不能证明其导致或排除 native 内存错误。pre_init 在安装期执行，D1.2 shell本身不安装模块。

旧事故对照各自独立：S07 PID1048392预览阶段（仅见 `_PyObject_Calloc` 附近）；S08-C PID1670701 upgrade后资产阶段（`dict_dealloc` 附近）；S09 PID1792405 registry/GC→contextlib 的 Python栈；S10 PID2383730 registry后 `field_computed`/`res.users.context_get`，真实signal11。原日志SHA依次 `5fc113a2524a4e383b895d8487164e71f917c2189b88ebcb380c9c85867a9e41`、`07e23e987e415a50255789fbe9721b1d10e8931977d77fe4761ec7b1819f6909`、`761e3cd6bfda2aef894fd7c413e532c28fcc853aa89b054452db4995b6132daf`、`f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`。**没有可比的完整 Native C 崩溃栈，不认定同根因。**

## PG观察器缺陷、修正和唯一自检

原 D1.2 runner SHA `9df4b841b59026e926de58442002060c5d31dd0e0b44d481fa2251b9c4310753`，原54条空采样SHA `4abb5090a41fece470a5b87045dacd16dd4b5cbb993b7fecf70592ccbbe593ad`，均原样保留。旧代码先进入 `with psycopg2.connect(...)` 的事务上下文再设 autocommit；上轮只读对照看到 INTRANS 并复现缓存空统计快照。54个空数组是**无效的在线证据**，不表示没有 PG 后端。新私有修正版 SHA `3d2e65aa0d771e91905ca932923523398760898e6c9225cf7658b3a1080e9ee7`、完整私有diff SHA `3871088f795603175b4c2d5f03d9b1f7bac8278a41a27c547c70d7619a268990`：在任何 SQL 前设置 autocommit，逐样检查 IDLE，限定合成标签，finally关闭连接。新提交的[独立安全观察器](../scripts/s10_native_pg_observer.py) SHA `cdb0df392419ad03f2f6976f8f497966a1c2edecdee99ff97f71c42b195f976d`，只连接明确的 `postgres` 管理库、仅选择自身唯一合成 `application_name` 的 PID/状态/时间，不读取 query文本、其他会话或业务数据库。旧runner及固定业务测试未改。

`py_compile`、AST、mock均exit0，mock验证非autocommit、INTRANS和外部tag拒绝；模拟不算PG实测。强制[#34检查点6160855913](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160855913)在运行前发布并通过API逐字读回，正文SHA `a73c50828f9ef7bbd4212f550807da0f3f86fc37e8017bd980fb1d53dd4f5fe7`。之后唯一执行：

```bash
../.venv/bin/python scripts/s10_native_pg_observer.py --selftest --application-name s10_d13_selftest_9f2a47c0e113 --output .local/s10-native-20261014-6160777256-d13/pg-selftest.json
```

命令 **1次、exit0**；恰好2个短时非 Odoo 只读管理库PG会话，subject backend PID414962、observer PID414961。subject只做 `SELECT pg_backend_pid()` 与 `SELECT pg_sleep(3)`，服务端 statement_timeout 5秒；observer采样前空、在 `active` 时看到414962、结束后空，且每次 autocommit+IDLE。结果原件SHA `beb8fa4cde7da3c583cf247a3abf54ee1e9da57411c9bfab75e4ea7b88b2393c`。这只验证修正观察器在这次非 Odoo 窗口确能看到一个自有后端；不是D1.2的回溯修补，也不是S10财务并发PASS。自检没有业务SQL、写入、数据库CREATE、连接终止或服务重启。

## 最多三个可证伪假设与下一次最小实验建议（本批不执行）

1. **H1 模型扩展与registry对象图相关。** 第92模块重写的模型方法/guard使对象图或加载顺序不同。未来先在全新合成库按现有hook合法安装92模块，但保持业务表纯安装态；用两GDB只读shell和有效PG观察器同轴捕获。若真实signal11和C栈在相同边界出现，支持模块状态关联；一次未崩溃只削弱确定性假说，不能排除低频问题。不得从事故库克隆或绕过hook。
2. **H2 已提交业务状态导致特定shell用户上下文/缓存路径。** 若92模块纯态无崩溃，另获授权后在另一全新合成库按最小依赖顺序构建人工用户/门店与必要记录，并逐项记录状态；两shell仍只做只读探针。真崩溃及C栈若只在某最小状态出现支持该路径；单次无崩溃仍不证明安全。绝不复制事故OID2056451、真实患者/资金或旧filestore。
3. **H3 CPython/native扩展或共享库的并发加载/内存安全错误，与S10业务无必然关系。** 需要真SIGSEGV时的各线程C栈、共享库/Build ID/映射，并与Python faulthandler、GC/registry时间和PG状态对齐；若C栈明确落在特定扩展或libc分配器，可缩小因果范围。仅凭最后Python帧、两次正常退出或目前相同wheel SHA不能验证此假设。

建议先获**新正式授权**建立一座全新受保护纯合成库，合法安装92模块，单独预算至少**1个Odoo安装目标**；若需其它初始化或状态构建，每个Odoo目标另计数并事前列明。完成可审计安装/只读OID、cluster、marker、config/filestore/guard核验后，进入**另一个明确授权的单一双shell窗口**，预算2个独立GDB下Odoo目标；总最少3个Odoo目标，不能把安装藏入2进程窗口。若未来先在新纯92库准备业务数据，准备进程数及合成交易范围须另定，不能借本建议执行。安装/guard/资源/权限/监测器异常即STOP；真实signal11立即停另一自有目标并保全完整私有Native栈、日志与哈希；无崩溃只报告本窗口未复现。实时观察器需要专用 Odoo application tag 的受控白名单、每采样新统计快照及不同PG backend PID，与GDB目标PID和registry时间线交叉核实。GDB调试符号仍有限；C栈若不可解读则根因继续UNKNOWN。

私有原件目录 `.local/s10-native-20261014-6160777256-d13/` 为700，输入、diff、全模块/表统计、自检输出与GitHub回执为600；旧原始日志、54样本、事故marker、库/filestore/volume/core/备份原位保留。本批仅公开脱敏报告与机器索引；无患者资料、密钥、原始栈上传。#34、#35保持OPEN，Project零写，不启动S11、不合并/强推、不部署。**S10全阶段和生产继续BLOCKED；D1.4/D2等待GPT另行裁定。**
