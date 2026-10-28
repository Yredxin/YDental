# R2-W0 只读接管

限定准出：历史目标仅允许只读；W1 使用新建独立 scratch，实建及隔离须现场确认。W2–W4 写入依赖完整保护基线及测试身份与环境核实，不能因本抽查视为准出。

- 起点 R1 报告 `d0b79a9edfeb725a5a7706ef3f60232be725288c`，产品 `dca4e1d2821b20df7b4b940d28d461270c310225`；R2 正常从该报告提交建分支。#36 CLOSED、#37 OPEN。
- A 独立只读事务：目标 OID 2171423、cluster 7694897083368259627，原 1541–1551 inactive、1229–1238 suspended、45–55 pending、mutex revision 26，其他连接 0。私有回执 SHA256 `cf339c95c35f410eae616d6820e8aa706606e7c18ae0a46639c7c690cfb7b53d`。首次查询列名错误退出 1，修正后退出 0；不改变历史 UNKNOWN。
- B 独立物理只读核同目标身份、11 inactive、10 suspended、指定 12 个讨论成员不存在、其他连接及 prepared transaction 0。回执 `fab33df897f128ea7715f9347ca07288b78d57fafc33d9afe2194b1bc2a64c87`。W7 投影新快照 SHA `a373317cf00841d8c9ee83eb4ffb2dc1c4fbfafed51eb206500a157582b4db77`，与停用后前像一致；关键账务、库存和文书抽查 `beeca1788b7151d3d2097fb84b6960606e1c6207eac2f4c200a044c5dc31a6bf`。不是全部历史对象的完整前像。
- C 复核 R1 报告、原回执 SHA 及有效增量。BUG-002 原修复 `411d6e62a3b1d7f6bf5eb19439e81e6956cb0243` 经 cherry-pick `c483464` 纳入产品；此前真实升级 revision 13→0 与旧 XML 重载相符，但未逐 SQL 捕获。旧 scratch 仅 MODEL；旧 Session、缺失紧邻升级前像仍 UNKNOWN。C 首次猜错日志路径，修正后哈希核对成功。
- 旧 scratch OID 2144130 不作为本轮可写目标。既有独立 Docker PostgreSQL `--network none` 方案和本地固定镜像存在，实际创建、身份及隔离未验证。未创建 R2 用户或业务记录，也未升级历史库。
- 新旧团队共享主机，线程独立不代表 OS 隔离。完整 W0 原始回执位于本机忽略目录 `.local/s13-e2e-r2/`，不得公开私有配置或凭据。
