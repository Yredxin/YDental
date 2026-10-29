# P14-T09 F0 C：真实加载方案只读调查

P14 原结果 PARTIAL，T09 FAIL；既有已加载 QWeb 合成分支和浏览器使用简化外壳，既未完成真实岗位 GET，也仅解析资产路径而未证明完整 HTTP bundle。既有 WebKit 768 情况输入右缘 767px、滚动框右缘 744px；Chromium 极窄 200% 条件亦有焦点裁切，详见原独立复核。早期静态外壳遗漏 border-box 及误用 Home/End 等工具失败不应冒称产品缺陷，原证据保留。

本轮可按 `.local/dl-p14/w3-final2/run.py` 的隔离方式重新编写独立 scratch 运行器：全新目录和数据库容器、随机私有凭据、network none、Unix socket、核实不同 cluster/OID、固定候选 worktree、loopback 专属 Odoo、安装 `ydental_settlement`。该脚本硬绑定旧候选、路径、端口和测试，不能原样执行或覆盖旧证据。新安装完成后还须确认前端 bundle 真实编译、浏览器实际收到 HTTP 资产和内容，而非仅核资产路径。异常退出或未知提交须先读回，不能盲重试。

真实岗位 GET 依赖 `ydental_settlement/controllers/settlement.py` 中的已认证 Odoo session、原生门店绑定、membership 及 settlement/export 等权限。应在新隔离 scratch 内通过合法对象和正常登录、切店建立最小场景；只准计划所允许的合成账单数据，核账单/门店/患者及权限来源，不能将虚构 context 或内存 QWeb 布尔值冒为真实岗位权限。`ydental_settlement/tests/test_synthetic_receivable.py`、`test_synthetic_finance_setup.py` 可作为 ORM 接口线索，但事务回滚与 patch 不是已提交数据的证明。严禁发送 waive/pay/refund/close 等经济业务 POST；登录、切店与 GET 的原生副作用应另行记账并在实际保护范围内独立读回。

当前只读资源检查：文件系统可用约 12GB，内存 available 约 5.4GiB；Odoo 核心为 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，已有 postgres:18 镜像 `74935e722416`。旧新库安装曾约一分钟，不能保证本轮运行结果。旧历史库和前次 scratch 均不应被覆盖、删除或重放；本次调查未启动服务、连接数据库或更改产品。
