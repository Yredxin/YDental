# S10 Native D1.0 修正与 D1.1 有界窗口报告

## 授权、边界与结论

本批依据 [#34 授权 6160318169](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160318169)，从固定 `a0c579e0840eba3681b252afc8ecbcbb91365e9b` 在原 S10 分支正常前进。固定 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 未改。先完整读取 #23/#34 正文及有效评论和 #35 状态；开始时 #34 最新裁定仍为本次授权，#35 OPEN/0 评论，本地和远端 HEAD 一致且工作树干净。

**本次 GDB 窗口未复现 SIGSEGV；未取得原事故或新事故的 Native C 栈，根因仍 UNKNOWN。S10 技术与生产继续 BLOCKED。** 本批只做 D1.0 建库工具离线纠错及 D1.1 一次新库、两个 GDB 下的 Odoo 目标进程。没有 D2 业务测试、Firefox、S10 产品变更、Project mutation、S11 或生产部署。

## D1.0：故障定位与离线验证

旧工具来自保留的 `.local/s10-native-20261014-6160027673/native_capture.py`，SHA256 `e3de7c8781887bf98fc42bb44620c62938c4ee376c40ad0e63c7d20ea9168c66`。新权限 700 的 `.local/s10-native-20261014-6160318169-r2/` 内保存 600 权限原样副本和清晰 diff；修正版 SHA256 `55b1ff71e5ab1435327baf60ef57676b2a264a04f514264a27f5efa8dc18448a`。旧工具以 `with psycopg2.connect(dbname='postgres', ...) as db` 包裹 `CREATE DATABASE`，后续设置 `autocommit=True`；上轮实际 CREATE 在事务内失败 `ActiveSqlTransaction`。修正版把实际 CREATE 放在独立、显式关闭的管理连接；任何 SQL 前设 autocommit，检查 `TRANSACTION_STATUS_IDLE`，以 `sql.Identifier` 引用唯一合成库名，只执行一次 CREATE；新 OID 用后续独立只读连接查。前置拒绝已存在库/目录、端点/cluster/guard 异常，无 DROP、重命名或覆盖路径。

`py_compile` exit0。首次编写的 AST 检查误把 CREATE 后只读 OID 核验连接当作 CREATE 事务，exit1；此测试定义错误已修正并在私有目录留记录。最终 AST/fake 连接测试 exit0：autocommit=false、ACTIVE 事务、错名、重名库、重名目录、错误 endpoint/cluster、缺 guard、七类 marker 篡改均拒绝；合格 auto+IDLE 路径仅构造一条带 Identifier 的 CREATE。**模拟测试不等于 PostgreSQL 运行验证。** 独立只读 PG 查得 `127.0.0.1:5432`、cluster `7694897083368259627`、账号可建库；原事故库 OID2056451仍在，旧失败计划库 `...6160a273` 不存在而失败目录保留；新拟定名称未占用，端口18249空闲。原事故 config/log/marker SHA 分别仍为 `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、`f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、`d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78`。

私有 GDB17.1 SHA `e5272927fc1b40345748dfa4133ec2a50caeb5f209a44099dd2c48679911c59c`，保留匹配 glibc 调试符号；目标 GDB 脚本 SHA `58e8c4c67d63319586b02d5403d3bbeadc296778f2529ecc411d8be915282f6f`。GDB 自身用私有共享库启动，脚本在目标环境明确取消 `LD_LIBRARY_PATH`，不替换 Python/venv。真实 CPython3.12.15 ELF Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`；完整解释器/扩展 `.debug_info` 覆盖不足。D1.0 强制检查点 [评论6160387186](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160387186) 在建库前已发布，并经 GitHub API 逐字读回：正文 SHA `2da9e09f921ed1c4d40fcb10fc6c4d92082b43aa786f5beb7ce59de45ebe5d85`。

## D1.1：一次 CREATE 与最多两个 Odoo 目标

单次执行：

```bash
../.venv/bin/python .local/s10-native-20261014-6160318169-r2/native_capture.py create
../.venv/bin/python .local/s10-native-20261014-6160318169-r2/native_capture.py install
../.venv/bin/python .local/s10-native-20261014-6160318169-r2/native_capture.py shell
```

`create` exit0，唯一新合成库 `ydental_s10_test_20261014034100_b9c74e20`，OID2078375、原cluster、HTTP端口18249、configSHA `7f371fd1775aac4a10fdea92c467ff0ee504250856e6ae1e76f41aeef3e46dc8`、markerSHA `04d91a259f3368fe4f4b767f09fc9a9af228b49cd7a0489f3bf0415d7026bf2c`。独立只读核验 strict dbfilter、专属 data_dir/filestore、guard/config/marker 及 700/600 权限；旧事故库仍 OID2056451。纯合成库没有真实患者或支付数据。原生安装后 `ydental_settlement=installed`；只读统计显示 settlement 的 source/payment/refund/close/receipt/trade 等业务表均 0，安装元数据 mutex 1。

| 目标 | GDB PID / Odoo PID | 退出与信号 | 日志 SHA256 | 结果 |
|---|---:|---|---|---|
| 安装 `ydental_settlement` 与 manifest 必需依赖 | 2436308 / 2436314 | GDB exit0、目标正常退出、signal11无、timeout=false | `694ffb07cdd132ffa1197a2fe2e586b1a4ae032800affb488076e72f406ad2af` | 只读 SQL 验证 installed |
| Odoo shell 现有 `env` 只读 registry/模块探针 | 2436998 / 2437004 | GDB exit0、目标正常退出、signal11无、timeout=false | `c1461b1fb227e641ecf257a922a32fe0ce48d5f288cab090ac8feb5be9b9061c` | `S10_NATIVE_READONLY_CANARY` 返回正确库与 installed |

GDB 两份日志都含 SIGSEGV catchpoint 的**设定行**，均无 `NATIVE_CAPTURE REAL_SIGSEGV` 或真实信号触发，尾部显示目标正常退出。shell 有两个非 Odoo 的 vfork 辅助进程，未作为额外 Odoo 目标；实际 Odoo 目标合计 **2/2**、CREATE **1/1**、Firefox0。没有真实 Native C 栈；不能把 catchpoint 设置、旧 Python faulthandler 帧或窗口未复现当作根因证据。

## 事故对照、证据保全与复核建议

原 S10 PID2383730 的 signal11 与守卫中断 PID2383729 的 signal2 已分别核定；历史 S07、S08-C、S09、S10 崩溃阶段和可见栈不同，不能推定同一根因。已证实本次固定命令安装与只读 shell 正常退出；解释器、native 扩展、共享库或资源时序哪个导致旧 SIGSEGV 仍属推测。可证伪的下一步是由 GPT 独立评估是否另行授权针对原并发路径的隔离捕获；本批没有该授权，也不追加 Odoo 进程。

原始 GDB 栈命令、日志、私有调试符号、配置、差异、模拟脚本与失败测试记录保留在 `.local/s10-native-20261014-6160318169-r2/` 和 `.local/ydental_s10_test_20261014034100_b9c74e20/`（700目录、600文件），旧 D0 目录和失败现场不覆盖。公开 [脱敏机器索引](evidence/s10-native-d10-d11-window/diagnostic.json) 仅含身份、退出码、哈希和结果；不上传原始 GDB 日志、配置或密钥。没有删除历史库/卷/filestore/core，未改变 Odoo20 core、odoo-12、S10 产品、Project、Issue 状态；无合并、强推、S11、部署。S10 与生产继续 **BLOCKED**。
