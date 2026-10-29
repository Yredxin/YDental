# P14 W2 C：QWeb 证据与独立 scratch 可行性（只读调查）

P13 `scripts/s13_dl_p13/runtime_bill_contract.py` 在 Odoo shell 的只读事务中，从数据库组合视图 `_get_combined_arch()` 取片段，以 `ir.qweb._render` 和明确标记的内存上下文渲染，并 rollback。其硬编码历史数据库身份、P13 目录和 P13 候选，不能直接作为 P14 运行或证据。内存值、权限条件和假 token 不证明真实财务或授权。

无历史库升级的两条路径：

1. 新建独立 scratch 集群和数据库，在固定 P14 候选上 `-i ydental_settlement`，随后核对数据库身份及实际已加载 QWeb、资产，仿 P13 使用只读事务和内存合成场景。正常普通岗位 GET 需单独建立合法账号、岗位与门店，不能因空库合成数据声称真实账单。模块安装产生 scratch 数据库变更，应明确只在新目标发生。
2. 从候选 XML 抽取原始 section 直接交真实 `ir.qweb._render`，依赖可访问的已安装模板供 `t-call`。这能够验证源架构在 QWeb 引擎中如何渲染，但必须标记为 source-arch QWeb，并确认被调用模板版本；不证明数据库已加载候选、资产整合、真实用户权限。该方法仍需适当 Odoo registry 和安全只读事务，并非纯静态 HTML。

只读检查 Docker 可访问，`postgres:18` 镜像与锁定 Odoo 核心、venv 存在。`.local/s13-e2e-r1/scratch-receivable-r3/run.py` 可作为新集群参考：网络 none、私有随机口令、Unix socket、新数据库身份核验、安装 settlement；该旧执行 exit 0、约 59 秒，r6/r7 exit 0。另一个 r5 exit 1，不可混为通过。脚本绑定旧目录、候选及测试，需逐项审查并为 P14 创建新工具，不能原样调用。现场磁盘约 13 GB 可用、内存约 5.3 GiB available；旧 r5 数据目录约 213 MB、运行目录约 64 MB，仅供资源估算，不保证新运行。容器与历史数据不能清理或覆盖。

本调查未启动数据库、Odoo 或浏览器，未提交业务，也没有执行 QWeb 渲染或新安装。真实性和验收只由后续具体运行证据确定。
