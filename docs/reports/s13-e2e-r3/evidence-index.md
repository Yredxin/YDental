# R3 证据索引

所有哈希指向本机私有回执或日志的原始字节，不意味着原始敏感数据可公开；公开仓库不含凭据、Session、私有数据库、真实附件或完整敏感日志。阶段报告记录命令层级、角色、退出码及限制。

| 证据 | SHA-256／固定标识 | 层级 |
| --- | --- | --- |
| W0 历史采集基线 | `898ecb25717caf121e6a0ec510abec051310d7bc2b28f947c86d9f9de308286d` | 新物理 RO/RR；所采范围 |
| W1 A 岗位观察 | `d4303485acb83e00ec517089bc93e608fdc61022caaf59c128294ae91f6428e2` | 原服务真实浏览器 |
| W1 B 持租约独立复现 | `d2eb85be3db0b7a1ee8a2dde2f56f57547ee715f9cbde7ebda3c31b40bd49596` | 原服务真实浏览器 |
| W2 D1 正常离职独立读回 | `575b3c6321a2ee3448778d53bc0b28a93a09f6e392a95b0c9516222302d8b2ca` | 原服务已提交／独立物理读回 |
| W2 责任转派原请求 | `513b568833c3702d9252bf2d1b4158a1fe646e70a6799b8be3c3e7e455f75521` | 浏览器 HTTP200；响应正文 UNKNOWN |
| W2 转派及全量对照 | `716ef9202f7683f09e1ac5f9b4ffe6e6575cf877b99894fe39ff5a0cba027d79` | 独立已提交读回／采集范围 |
| W2 补记及释放全量对照 | `c28a6f9dfedeca147c1325e8d483a0ec9b628c2babe92f582058d29b376ec87d` | 浏览器／独立读回 |
| W2 无医疗权403对照 | `a744c7d02164cb8c79a4ba8d637d1c63e36aa10ffe415b51a8d5ce1e9efcf83e` | 真实 HTTP／独立读回；服务日志拒绝，不冒数据库审计 |
| W3 A 六项 | `52ebd2cdad138b18f5236100cdb0f34dbc3f25f6eb5a5bd9f1a7e749267b8218` | 固定候选、MODEL／HTTP、供给替身 |
| W3 B 九项 | `0f1534bd71290386c1abe6da4f9ea4551ab65a4bd02a72a1441ebc803cc2ceec` | 独立 scratch MODEL、供给替身 |
| W3 经济专项首轮 | `a3ba682d912745621b853d1625e3a6ed71fab9b42e8a9c1e5d31ca1f6fd04e69` | exit1／0 post-test；B 归类测试环境错误 |
| W3 经济专项成功 | `d21a5dbd6745af35bae08afbb7ff7f0b0d0852fdd38cfb35639f07666e233a25` | MODEL 事务、供给替身，非浏览器／持久提交 |

固定产品与测试源码 `c50688ba806c69a624c3bf9b171b10ea164bfeec`；历史浏览器运行服务为旧候选，不能混签。最终收尾回执见 [W4](phase-W4.md)。
