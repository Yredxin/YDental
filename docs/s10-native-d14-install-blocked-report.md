# S10 Native D1.4：第92模块安装护栏拒绝，双GDB窗口未执行

## 结论与授权

依据[#34 GPT-REVIEW/AUTHORIZE 6160943711](https://github.com/Yredxin/YDental/issues/34#issuecomment-6160943711)，本批仅执行D1.4-0只读/离线预检与D1.4-A**一次**纯合成模板CREATE、**一次**GDB下Odoo安装目标。第92模块的未修改`pre_init_hook`在安装时拒绝新库marker，安装失败后按STOP规则停止；**D1.4-B双GDB并发窗口没有启动，Native根因仍UNKNOWN，S10技术和生产继续BLOCKED**。未修正marker后重试、未建第二座库、未增任何Odoo目标。

开始前用GitHub API读取#23/#34正文和全部有效评论以及#35 OPEN/0评论，最新授权仅6160943711。本地和远端基线均为`c0948c066f2bf64bd304be3fcbbd183b5c415fe4`、原分支起始工作树干净；固定S10 product`4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test`255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`均未改。Ubuntu venv CPython3.12.15、私有GDB17.1、PG Docker `postgres:18`健康、odoo-12独立。Project零写，#34/#35保持OPEN，不启S11、不合并/强推、不生产部署。

## D1.4-0：模板、工具与强制检查点

只读核对PG endpoint `127.0.0.1:5432`/管理库`postgres`/cluster`7694897083368259627`。唯一模板`ydental_s10_test_20261014034100_b9c74e20`仍OID2078375，事故库`ydental_s10_test_20261014020300_8b6c1d4e`仍OID2056451，D1.2库`ydental_s10_test_20261014040500_d12a7c61`仍OID2100078。模板configSHA`7f371fd1775aac4a10fdea92c467ff0ee504250856e6ae1e76f41aeef3e46dc8`、markerSHA`04d91a259f3368fe4f4b767f09fc9a9af228b49cd7a0489f3bf0415d7026bf2c`未漂移。其91个installed模块名称/版本/状态与D1.3清单逐条相同；患者、真实诊疗/资金/库存交易表全0，仅5个原生默认`res.partner`。70系统附件无临床来源，124 filestore文件逐SHA一致、62未引用文件全为0字节、缺失引用0；模板从独立管理连接看活动连接0。只读误断言第一次把自己连接算作外部会话而exit1，改用独立管理查询后通过；原失败保留。附件模型列表检查一度因`None`与字符串混排TypeError exit1，改用只读字符串表示后通过；不改变模板。

新私有目录`.local/s10-native-20261014-6160943711-d14/`为700、私有文件600。克隆器、安装GDB、双GDB脚本、只读shell、D1.4专属PG观察器均做`py_compile`、AST/模拟/静态检查exit0；GDB17.1可用。模拟覆盖非autocommit、INTRANS、错库/旧事故模板拒绝，合法输入只生成双`sql.Identifier`的CREATE；观察器只允许`postgres`管理库和本批两个Odoo application tags，不取SQL文本、用户或患者内容。**预检遗漏**：模拟只检查marker含`core_sha`，没有直接调用真实`ydental_settlement_test.pre_init_hook`所期望的`core`键；因此离线PASS不等于安装护栏会通过。工具源码、完整diff/私有日志SHA见[脱敏机器索引](evidence/s10-native-d14-blocked/diagnostic.json)。没有将D1.3非Odoo自检冒作Odoo监测。

任何CREATE/Odoo之前，在#34发表[第一强制检查点6161008700](https://github.com/Yredxin/YDental/issues/34#issuecomment-6161008700)，GitHub API逐字读回一致，正文SHA`132e0cebd4b8f1e588037e60f77b2cd6e1ce945378867e7967bc5bb2056c1c09`。准备命令、环境/guard、预算与STOP条件均在该检查点固定。

## D1.4-A：一次CREATE成功，唯一安装失败并停止

唯一命令`../.venv/bin/python .local/s10-native-20261014-6160943711-d14/d14_capture.py clone`，CREATE **1/1、exit0**。管理连接先autocommit=true、事务IDLE，实际语句仅：

```sql
CREATE DATABASE "ydental_s10_test_20261014043500_e41c7a2b" WITH TEMPLATE "ydental_s10_test_20261014034100_b9c74e20";
```

新库OID **2100079**、cluster原值、端口18251、独立data_dir/filestore/dbfilter、专属loopback+禁外发guard；configSHA`786a98733a09ed489c1d68231369d859e9014ac9bebe74861db0c39974571f90`、markerSHA`411f3636e8aabd9a21f5a41f0ee149dd5b5b270246ff2ebe65ffa85fa5fc4421`。复制124个经安全审计系统filestore文件逐SHA一致，源不写不删。创建后独立只读PG证实新库91模块与模板逐项相同，抽查10张患者/财务/库存交易表行数和为0。第一次独立核验脚本的Python动态导入缺`sys.path`，**exit1且尚未读目标库**；修正只读诊断脚本的导入路径后exit0，原失败不抹除。这不是第二次CREATE或Odoo目标。

唯一安装命令`../.venv/bin/python .local/s10-native-20261014-6160943711-d14/d14_capture.py install`，包装器**1次、exit2**。GDB父PID **2467378**，真实Odoo目标PID **2467385**（全批Odoo目标数**1/3**），GDB退出255、目标`exited with code 0377`即255，无signal11、无正常退出；日志SHA`6229f751c944585895615e7f1c7e75fc0c9018004e4026047f21385b350e64b7`。原生C崩溃栈**未获得，因为未发生SIGSEGV**。安装目标加载到`ydental_settlement_test (92/92)`时，原有`pre_init_hook`抛`AccessError: S10 synthetic adapter database identity changed`，registry初始化失败。没有执行任何结算、收退款、日结、临床或库存业务。

失败后只读PG确认新库仍**91个installed模块且逐项等于源模板**；`ydental_settlement_test`状态`uninstalled`，抽查10张业务交易表全0；新库OID2100079、模板OID2078375、事故OID2056451、D1.2 OID2100078、cluster均不变。GDB/目标进程已退出。只读逐项比较guard条件：数据库名、真实OID、cluster、configSHA均匹配；marker却只有`core_sha`而没有hook读取的`core`键，所以`marker.get('core')`为`None`，与固定core SHA不等。这是**本次克隆器marker字段与既有安装护栏的契约缺陷**，不是Native SIGSEGV的原因；`YDENTAL_S10_RUN_DIR`在GDB目标配置中指向新同名私有目录。原marker/配置、失败日志、源代码均保留原样。本批不得就地补键再安装，也不得建新库重试。

## D1.4-B状态、证据边界和下一步

D1.4-A必要条件“安装exit0、92 installed”未满足，因此第二检查点**未发布**、B两个GDB/Odoo shell目标**0/2、NOT_RUN**，PG在线观察器实际采样0，registry重叠/Native并发结果**UNKNOWN**。本批总Odoo目标1，Firefox0，业务写入0，新库1。旧D1.2的54次空采样继续原样保留，不能拿本批无B样本推出无PG连接。原事故PID2383730真实SIGSEGV及S07/S08-C/S09旧Native原因均未消除。

下一步仅建议GPT另行授权前先离线修正新克隆器marker契约：将真实`pre_init_hook`逐字段静态/模拟检查纳入预检，对新配置/OID/cluster/core/configSHA逐项做同构校验；不得修改/绕过hook。若再次授权，须使用**全新唯一库和独立进程预算**，因为本批CREATE1与安装1已消耗；本批不能继续D1.4-B或自行恢复D2。原始GDB日志、config/凭据、完整SQL/filestore目录和所有失败材料仅在700/600私有目录及新库目录，GitHub只有脱敏摘要与哈希。历史S00—S10库、卷、filestore、core、日志/备份不删除不覆盖；Odoo20 core、odoo-12和venv不变。**S10技术及生产持续BLOCKED。**
