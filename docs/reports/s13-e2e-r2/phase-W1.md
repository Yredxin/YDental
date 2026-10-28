# R2-W1 库存互斥升级及竞争

结论：**scratch 升级及库存 MODEL 竞争限定通过；历史目标升级 NOT_RUN，BUG-002 保持 OPEN／目标层级未完成**。未修改产品代码。源码为 R1 最终产品 `dca4e1d2821b20df7b4b940d28d461270c310225`，实际运行报告 HEAD `d0b79a9edfeb725a5a7706ef3f60232be725288c`，产品文件与该候选一致。

原升级 revision 13→0 与旧 XML 指定零且可更新、升级日志重载 XML 相符；缺逐 SQL 捕获，不称直接捕获原因。修复去掉 XML 中的 revision 值并置 noupdate；原提交 `411d6e6` 的对应 cherry-pick `c483464` 已包含在产品。

A 创建 network none、Unix socket 的独立 PostgreSQL scratch，cluster `7701479549972365342` 与历史 cluster 不同。通过真实 `_lock()` 三次形成 revision 3，ORM 设置旧式 XMLID 标志；实际 `-u ydental_supply` 退出 0，日志确认 inventory XML 被加载。B 另物理只读连接核 mutex ID 1、revision 3、XMLID res_id 1／noupdate false 升级前后不变，两模块 installed。B 回执 SHA256 `dbb245d34dd78737b036ec49d67efc20c78b4183441c6e1a5b6be8a3cbdf54d7`；升级日志 `5912f85ab697615ebb86fc191fbbf6faa9a99c89e68a9bacddbc9b9cadf2b61b`。

A 使用正常合成岗位授权、产品库存 `_operate` 和两物理事务做不足库存与相同请求竞争，均实见 advisory lock 等待；各一方提交、另一方原生 `40001` 回滚。已知中止请求在新事务续试分别被 `insufficient_balance` 拒绝或返回 `already_accepted`；B 独立核来源、事件、库存移动和收据，无重复出库，内部余量 4。供应商虚拟位置 -10 为供货来源，不能误认内部负库存。竞争日志 SHA `cb1b0c7b3f68c91f4d2e7d9444c3930c10844f8e47393d1b0f8b63b53b2bc67c`，B 读回 `d91ebd644e142464e5c8e9fce93b847a3d74f98913d3af74bc5ae6996fcabba9`。该证据是 MODEL／真实连接和提交，不是 HTTP、浏览器或容量竞争。

首次竞争准备因缺多仓及库位设置退出 1；B 独立确认未提交测试门店或用户、revision 仍 3，回执 `26da3fa64556bb151a75e7d84918c4a9cf588bbb0d0538961742c776aaa08e31`；按测试环境前置错误保留，非产品 BUG。正常配置后再执行，未抹掉原失败。

A 正常停止自建容器，运行及 Docker stop 均退出 0，结果 SHA `d604d3ca3d6ea37d2a37d641f7980fdb0bc031a54b150f64dcfd4d0d483883f3`。B 独立核容器 Running=false、PID 0、退出 0、socket 和测试进程不存在，回执 `cef677ea440ef421e8fbbebe8f42a35c292c704890e2cd763c0d1eef6d323ee0`。本机私有原始证据在 `.local/s13-e2e-r2/`，团队共享 OS。
