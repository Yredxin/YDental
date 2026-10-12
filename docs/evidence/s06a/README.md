# S06-A 固定证据

只包含合成、脱敏材料。产品/测试/最终证据提交以#30交付评论固定；这是Codex自测与复核申请，不代表GPT或用户验收。

- `github-boundary.json`：#23/#30正文和启用评论交付前重读一致，#29技术PASS/状态同步指令索引；未代改Project。
- `isolation.json`：最终新库创建记录、OID、端点/cluster/配置hash、独立端口/data/log/精确dbfilter及外发边界；不含原始配置。
- `runtime-history.json`：全部本批创建库的动作/commit/退出码/测试数及私有日志hash。保留失败/补交，不覆盖原始材料。
- `model-http-cases.json`：实际定义并执行的26模型+6真实HTTP/RPC方法；TC映射见报告。
- `probe-attempts/`：真实两连接交错；最终结果16组。每组初始同时存在的backend PID不同，各次RR重试PID独立列出；不能以重试后池复用否认原始并发，也不能只凭最终PID宣称并发。
- `browser-attempts/`：每次独立目录；真实Firefox默认sandbox，失败摘要/通过检查/合成截图及SHA256。
- `translation.json`：实际导出135项对本模块PO逐项覆盖，带HTML的连接提示ID仍完整。
- `final-verification.json`：固定最终数据库的install/upgrade/probe/export、测试数、证据路径与commit。
- `artifact-manifest.json`：本目录全部其他文件SHA256，不包含自己。

复现命令均从本仓库使用核心`.venv/bin/python`：`scripts/s06a.py install --db NEW`，随后同新库`upgrade`、`probe`、`export`、`scripts/s06a_translation.py --db DB`；`scripts/s06a.py serve --db DB`后执行`scripts/s06a_browser.py --db DB`。新库命名、端点、cluster、OID、配置hash/端口/PID和既有依赖guard全部保留。Playwright/Firefox/GTK/字体仅复用既有进程本地资产，不安装系统依赖、不关闭sandbox。

runner拒绝业务/历史库及未记录库，不提供drop/reset。现有S00—S05数据库不接管。本次预览验证后只终止匹配本批PID/config的自建进程，既有服务不动。密码、SID、token、原始日志/配置和备份只留私有.local，不进入GitHub。
