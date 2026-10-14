# S10 Native D1.4-R1：真实 hook 合法安装与双GDB窗口

## 结论和执行边界

依据[#34唯一授权6161077626](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161077626)，本批在一座全新纯合成库中修正**诊断克隆器**的marker字段，直接执行未修改的真实`ydental_settlement_test.pre_init_hook`函数体做离线契约验证，然后仅一次安装第92模块、一次双GDB只读shell窗口。**安装92模块exit0，两个registry加载窗口实测重叠0.792秒，PG实时观察器有效，两个目标均正常exit0，未发生SIGSEGV。** 这只证明本次纯92模块、零业务数据的有界窗口未复现；原PID2383730的Native根因、业务状态差异及低频风险继续UNKNOWN。S10技术、生产持续**BLOCKED**，不恢复D2。

开工前GitHub API完整读取#23/#34现行正文和有效评论，特别是6161077626，#35 OPEN/0评论；固定原分支远端和本地起点`c8907f65cd3c89d25d2732c8d2024266cf02a1ff`、工作树起始干净。固定S10 product`4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test`255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`不改。Ubuntu实际venv CPython3.12.15、私有GDB17.1、postgres:18及odoo-12独立身份已核对；无Python/native包或全局参数替换。

## D1.4-R1-0：原失败保全、真实hook离线验证

旧失败库`ydental_s10_test_20261014043500_e41c7a2b`/OID2100079及原markerSHA`411f3636e8aabd9a21f5a41f0ee149dd5b5b270246ff2ebe65ffa85fa5fc4421`、安装日志SHA`6229f751c944585895615e7f1c7e75fc0c9018004e4026047f21385b350e64b7`原样保留。旧克隆器SHA`d8687790fbdc168ccca6fb28541295f936169daba26654059ab758f6ad173ad0`，新私有修正版SHA`3ee57ed8c86c5cbfaf54418f5aa4ed196e08e35f1b63d4b2a14693b6f4f31308`，完整私有diff SHA`b28462acbfff220a90dce2c21fce1eb7b91acfe34e27e07c96af031d7cb596ce`。仅新诊断器marker生成函数增加hook要求的`core`，并保留`core_sha`，两个值均固定为锁定Odoo20 core SHA；旧hook/产品源码未改。

实际hook源码SHA`cb90e4a300486066049677d4b1cf0b98ac4fb3052e5d59a6646403d147d3cbcd`。私有`hook_contract.py`用AST直接抽取、编译、执行这个**原函数体**，用FakeEnv/FakeCursor模拟其唯一`SELECT oid FROM pg_database WHERE datname=%s`及真实配置/marker字节SHA。离线13例exit0：合法1接受；12负向分别为缺core但留core_sha、错core、database、OID、cluster、configSHA、目录名、符号链接目录/配置/marker、缺marker、错误`YDENTAL_S10_RUN_DIR`，全部由原hook抛AccessError。离线结果SHA`007d5b8e0883cd7c05e22ca50caf45d92918a5de830b2811745d0a34227007da`。`py_compile`、AST、fake连接/双Identifier CREATE、GDB脚本/只读探针/白名单观察器静态模拟均exit0；模拟不冒称安装PASS。

仅允许的模板`ydental_s10_test_20261014034100_b9c74e20`/OID2078375在原cluster`7694897083368259627`，configSHA`7f371fd1775aac4a10fdea92c467ff0ee504250856e6ae1e76f41aeef3e46dc8`、markerSHA`04d91a259f3368fe4f4b767f09fc9a9af228b49cd7a0489f3bf0415d7026bf2c`再次匹配，91个installed模块同名/版本/状态、业务交易0、70系统附件/124逐SHA一致filestore文件、外部活动连接0。事故库OID2056451、D1.2窗口OID2100078及旧失败OID2100079均只读保全，不作模板。新目标名/端口未占用。任何CREATE/Odoo前发表[第一强制检查点6161126211](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161126211)，GitHub API逐字读回；正文SHA`0c6073595f430c9fe6017b6f4224eb8299d927601c8bb671396a1c0af83bf24a`。

## D1.4-R1-A：一次CREATE、真实marker护栏、一次安装

唯一CREATE命令`../.venv/bin/python .local/s10-native-20261014-6161077626-d14r1/d14_capture.py clone`，**尝试1/1、exit0**；独立`postgres`管理连接在任何SQL前autocommit=true/事务IDLE，通过双`psycopg2.sql.Identifier`执行：

```sql
CREATE DATABASE "ydental_s10_test_20261014044700_4f6a8d2c" WITH TEMPLATE "ydental_s10_test_20261014034100_b9c74e20";
```

新库`ydental_s10_test_20261014044700_4f6a8d2c`/OID**2100080**/原cluster/端口18252，独立严格dbfilter、config、data_dir、filestore和loopback/禁SMTP guard；configSHA`582f73fdee28cac3d9f63d116bb934e0def3b19fa5ddb7e10c054ba1ef20cb43`、markerSHA`df8ff92d38499745b6ecfffaecb7eaff739ff29066c243b13b15b3a1bf99bb7b`。124个安全系统文件只读复制并逐SHA核对。创建后独立只读PG证实真实新OID、91模块及抽查业务交易0。再对**真实新OID和实际配置/marker文件**执行原hook的AST函数体，`YDENTAL_S10_RUN_DIR`指向新同名目录，hook接受、FakeCursor SQL一次、exit0，私有结果SHA`6fa808c9f1f5fab63b48693371687dbc90ad1299dfc8493bef23061f1c4acefb`；这是安装前闸门，不是假装Odoo已经安装。

唯一安装包装命令`../.venv/bin/python .local/s10-native-20261014-6161077626-d14r1/d14_capture.py install` **一次exit0**；GDB父PID**2473357**、真实Odoo目标PID**2473364**，两者正常exit0，signal11=0、timeout0。安装目标仅`-i ydental_settlement_test --stop-after-init --no-http`，无其它测试addon、无实际业务动作。原始GDB安装日志SHA`a5c542ed1c8a08dd5442e13050794002948d1f6eb07560d0bc4238706d0b884f`。安装后独立只读SQL完整比对：92个installed模块，原91名称/版本/状态逐项不变，唯一新增`ydental_settlement_test@20.0.1.0.0`；12张患者、治疗、会计、结算、库存交易表均0，私有完整模块/计数清单SHA`6f694f949f2c1107143b4f8c7cca2f696ba16d542e974615bd09e642e65dd731`。源模板和所有旧OID未变。随即先发表[第二强制检查点6161144552](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161144552)，列全92项及B命令、PID和STOP规则，API逐字读回；正文SHA`4596b1185db517cf0c579287a66e9996c0af91cc10bd6b5a274f717e983ff6ed`。

## D1.4-R1-B：唯一双GDB只读窗口

准确包装命令`../.venv/bin/python .local/s10-native-20261014-6161077626-d14r1/d14_capture.py run` **仅1次、exit0**。两个独立GDB父进程使用`starti`屏障近同时放行各自Odoo`shell -c <新库配置> --no-http`；shell只读现有`env`的测试模块状态与`SELECT pg_backend_pid(), current_setting('application_name')`，本地同步文件不写业务。GDB目标前unset仅供GDB父进程使用的私有`LD_LIBRARY_PATH`，不更换目标共享库。实际进程与日志：

| actor | GDB父PID | Odoo OS PID | PG backend PID / application_name | registry UTC | GDB/目标退出、信号 | 原始日志SHA |
|---|---:|---:|---|---|---|---|
| A | 2474282 | 2474324 | 420300 / `s10_d14r1_a` | 04:50:15.846—04:50:16.638 | exit0/正常，signal11=0 | `bb8bc7510d0b3ff47505d27561d88adddfca6f534939a31ee3b31781ca830836` |
| B | 2474285 | 2474327 | 420299 / `s10_d14r1_b` | 04:50:15.840—04:50:16.638 | exit0/正常，signal11=0 | `f12b2d42148bb5208acd2369a35c0910db7b6a73fdbe3bd3df6894ca7aa86224` |

registry加载区间确实重叠 **0.792秒**。D1.4-R1专属观察器只连已核实`postgres`管理库，任何SQL前autocommit、逐样事务IDLE；严格限定新库名和`s10_d14r1_a/b`，只选择PID/application_name/state/backend_start/state_change，无其它会话SQL/用户/患者内容。54次实时采样分别22次见A、23次见B，**22次同一采样同时见两者**；两个shell自己的PG backend PID均能在独立样本中找到，观察链本次有效。原始采样SHA`1a29f1a66afee68c08b697b787fff3e5541036d73e0f3ff28b8ef4ef45d53fb1`，窗口结果SHA`a8649e80e5f5e5aa518739fbdac6ce96532ecd9d53da72b5d29aa5989e8541cb`。运行中未触120秒/512MiB阈值、未发送守卫SIGINT/SIGKILL，所有本批自有GDB/Odoo进程已退出。

两份日志的`Catchpoint 1 (signal SIGSEGV)`只是设置，没有`NATIVE_CAPTURE REAL_SIGSEGV`；**没有真实signal11，所以没有本次Native C崩溃栈或触发时共享库映射**。静态CPython ELF Build ID仍按既有D0证据`7713d416ece8f53a2b37e61dd06defd7bf795954`，不能替代事故时C栈。B后只读PG再次确认92模块原样、12交易表全0、源及事故/旧失败OID不变，filestore逐SHA匹配；私有后验SQL清单SHA`c77fd125edbfc0da219f5fab5d30550d6cc4f2675cabb2704cdc06d1b35400df`。全批累计**CREATE1、安装Odoo1、B只读Odoo2=3/3目标**，GDB父进程合计3；Firefox0、业务交易0、额外重跑0。

## 证据保护、已知/未知和停止

已证：原hook对新marker真实接受，合法安装92模块；本次纯92模块、零业务数据下双registry确实重叠且PG在线采样可核对，两Odoo目标正常结束。未证：原事故PID2383730的Native C根因、当时进程内堆与扩展映射、旧S07/S08-C/S09是否同源、以及原事故已提交大量合成业务状态的作用。一次未复现不代表稳定性修复。下一步若GPT另行授权，应先决定哪些原事故前置状态是必要变量，在**另一全新合成库**按明确定额构造最小状态并捕获真实C栈；不能复制事故OID2056451或拼接本批未覆盖的业务PASS，本批不自行进入D1.5/D2。

私有原始GDB日志、配置/凭据、完整hook stub和全模块SQL、PG过程采样、失败历史及SHA仅放在权限700的`.local/s10-native-20261014-6161077626-d14r1/`及新库同名目录内，文件600；GitHub只提交脱敏报告与[机器索引](evidence/s10-native-d14r1-window/diagnostic.json)，不上传原始栈、core或患者材料。原事故库、纯模板、D1.2库、上轮失败库以及全部S00—S10数据库/卷/filestore/core/日志/备份保全；Project mutation0、#34/#35保持OPEN，不关闭Issue、不合并/强推、不启S11、不生产部署。**S10技术和生产持续BLOCKED。**
