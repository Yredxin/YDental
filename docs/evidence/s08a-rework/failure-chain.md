# S08-A 定向返工复现与失败链

此前S08-A原交付、原失败和S07 SIGSEGV证据全部保留；本文件仅补本轮。**本轮最终状态BLOCKED，没有最终全量PASS**，不把中间PASS拼成最终结果。

1. baseline `f0f17e633a3421386d0a0bdf2b63a5f9709bde96`，本轮新库 `ydental_s08a_test_20261012121209_305ee956`，端口18160：install30，真实Firefox正常流程28项/17图/pageerror0，并分别真实复现handover、confirm、correct。路由先实际发送POST/取得服务器200，再扣住响应；主诉、病史、37/M可继续录入；放行响应、接受离页警告后，服务器文书只有快照A，新增B/37不在其中。**原代码确有通用beforeunload警告**，不是“完全没有任何浏览器提示”；它没有说明临床提交范围及已交还/确认事实，也无本页保留/合法核对出口。复现6张前后图已逐张目视核对，正常流程其余11图一并保留。
2. 首次产品 `382cd18c1f15670819f62fd3ea3a5b2065ed0afc`、测试 `d717c8dd27af4ce4d197eea37b5c5a605b9d6acc`，新库 `ydental_s08a_test_20261012122021_e556dccb`，端口18161：install30/upgrade28/probe16及8类审计不变量通过，但Firefox停在原离线中文检查（24项/10图/pageerror0，退出1）。只读诊断确认隐藏提示仍是英文。Odoo把相邻span合并为一个QWeb翻译块，单独新增PO词条无法匹配扩大的整块。随后实际export151词条，翻译检查FAIL（missing1/metadata1）。保存JSON和原始日志hash，未把模型PASS当完整通过。
3. `3246877240f78d5cd1c08d82ea4767a82aa1bff3`仅增加失败trace/可见状态证据；`d63322a70a011e193ed700168947c82199beb2e2`按真实POT替换完整合并词条；`a28b364691791214becf4909e9ecf1bc0be3555c`补保护，较早发出的心跳错误不能覆盖终态待核对说明。
4. 测试 `a0014c590e27ce1dc6812e36124b0bfa7282e22c`，另一个新库 `ydental_s08a_test_20261012123045_d399a600`，端口18162：install30/upgrade28/probe16及预览前审计通过，中文/原离线流程已恢复，普通自动保存期间新输入追赶至版本3；新增用例在读取持久内容时调用产品并未暴露的`read`动作而失败（29项/12图含失败画面、pageerror0）。这是测试脚本接口假设错误，不新增后端接口解决。
5. `3a4a5be827c3215a755ecd7343dda39fdfec94b4`仅把比较改为真实授权GET工作台，解析服务器渲染的版本/字段/结构化牙位。当前本轮失败库内只新增一组调试合成前提，原业务行/失败证据不重置、不删除；调通后最终完整验证另建全新库，不把这个调试库当最终数据。

所有预览均仅在核对自己的专属config/PID后SIGTERM，进程退出0；未发现崩溃后掩盖重跑。测试/调试不接管任何此前S00—S08历史或业务数据库。全部本轮新库、动作、失败和原始日志hash见execution-history.json；正式部署仍因历史SIGSEGV未知根因BLOCKED。
6. `3a4a5be`调试回放：原有流程及confirm/correct终态冻结、程序触发input后的本地保留和核对入口已通过；但GET页面投影与请求原始结构直接比较并不可靠，45项/15图含失败画面，退出1。没有改产品来迁就断言。`1bec52a970f497a1c01d5be98f1e4919bcd907d1`改用既有受保护原生RPC只读文书JSON，并按既有后端契约规范化牙位/牙面顺序比较；同时新标签页仍实际验证GET核对出口。该调试库后续88项/21图/pageerror0通过，仅记调通，不当最终安装升级验证。之后另建候选 `ydental_s08a_test_20261012124648_038d989e`，其失败结果见下一条。
7. `1bec52a`候选新库 `ydental_s08a_test_20261012124648_038d989e`：install30/upgrade28通过，原probe在7组PASS后出现空AssertionError，完整probe退出1；未运行浏览器，更不能称最终PASS。随后的只读审计8类不变量全0，deadlock0、无崩溃。旧探针catch未保留原异常位置，**不能事后声称已确认该断言的确切行或根因**。审查发现旧探针比较重试后PID，连接池复用空闲连接时这一判据不能证明初始两个并发连接相同。
8. `a39dbd58e293297eece66186905b103a7ec8d225`仅验证脚本修正：在barrier前记录两条真实首轮连接的PID，严格断言初始PID不同；继续保留重试最终PID和完整轨迹、原accepted/rejected及所有版本/后继/回滚业务断言，六次有界重试及有界短暂退避；失败增加原trace。产品仍为`a28b364`，没有改后端、S06锁序、权限或业务事实。再次从零创建候选库 `ydental_s08a_test_20261012125331_e66dbaaf`，后续安装资源失败见下一条，不当最终PASS。

9. `a39dbd5`新候选 `ydental_s08a_test_20261012125331_e66dbaaf` 在原生/上游模块建表阶段出现 PostgreSQL `DiskFull: could not resize shared memory segment to 33554432 bytes: No space left on device`，正常退出255，测试数null。没有SIGSEGV或crash记录，未进入临床模型测试；模型/HTTP/并发/Firefox均不能称通过。主机/dev/shm空闲不等于已核对端点PostgreSQL所在namespace空间，未宣称服务端环境根因修复。失败库/原日志hash/只读设置诊断保留。
10. `7d1f6b5`/`e8b2247609e51d7fbe268b94082e8fd3259db9d3`只改验证runner/probe/audit：为本轮子进程设置libpq PGOPTIONS，要求连接内串行查询/维护及16MiB维护内存；probe/audit新增SHOW断言，但**未运行到该断言，不能称实际设置验证通过**。没有ALTER DATABASE/SYSTEM、系统安装、改核心或重启服务。新marker固定这个进程会话profile，拒绝接管旧profile数据库。
11. 固定test `e8b2247`的全新候选 `ydental_s08a_test_20261012125922_18e705b1`，端口18165，仍在base原生建表阶段出现同类32MiB共享内存分配错误，install退出255、tests null；未出现SIGSEGV，未运行后续upgrade/probe/Firefox/export/audit。停止数据库重跑，保留两次环境失败，不通过改服务/核心/系统依赖排除；最终回归和本轮技术交付状态为**BLOCKED**。guard5和静态审查在固定test执行，不代替运行时回归。21张调试成功截图已逐张目视核验，仍仅属`1bec52a`调试证据。
