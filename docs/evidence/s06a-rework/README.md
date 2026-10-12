# S06-A定向修正证据

唯一范围为#30 review6117074066的BLOCKER-1—4；原840df89、docs/evidence/s06a及原失败/补交链均保留。本目录只放合成、脱敏摘要与截图，不放access/password/SID/token、原始配置/log或备份。

- `project-state.json`：实施前完整读取21字段/15条目/6视图/7公开workflow元数据；唯一mutation将#30执行状态从待启用改返工，两次完整读回其他值不变，原生Status=Todo；后续不自行转待复核。
- `github-boundary.json`：最新review6117074066、原启用及当前分支/原final索引与hash；交付前重读结果。
- `isolation.json`：最终新库端点、cluster、OID、独立配置hash/data/log/dbfilter/端口及外发边界。
- `runtime-history.json`：本批所有新库的action、commit、退出码/测试数及私有日志hash；失败/补交不覆盖。
- `continuity.json`及`model-http-cases.json`：原32方法AST未改；安装/升级日志确实执行全部新增/原方法；原16竞争名称/顺序连续。
- `probe-attempts/`：真实独立同时存活的两个backend PID、barrier/有序持锁、RR重试、结果和不变量。最终21组，含新增人员verify/跨店围栏/mixed missed/自动审计竞争。
- `browser-attempts/`：原26项路径及新增verify全局状态、错误执行区、未发布N；失败目录与最终目录并存，默认Firefox sandbox。
- `translation.json`：真实导出词条覆盖、code metadata及HTML提示DOM ID检查。非空译文不再被当成运行时元数据正确。
- `final-verification.json`：最终固定commit动作、guard/compile/diff及产品树一致性。
- `artifact-manifest.json`：本目录其他全部文件SHA256（不含自己）。

命令使用核心`.venv/bin/python`：`scripts/s06a.py install --db NEW`，同新库依次`upgrade`、`probe`、`export`，再`scripts/s06a_translation.py --db DB`、`scripts/s06a_rework_continuity.py --db DB`和`scripts/test_s06a_guard.py`。`scripts/s06a.py serve --db DB`后运行`scripts/s06a_browser.py --db DB`。复现必须生成另一个全新合规库名；不能复用已执行probe的夹具或接管历史库。

runner端点/cluster/OID/配置hash/精确dbfilter/PID/端口/外发guard原样；不提供drop/reset或依赖安装。浏览器仅复用既有进程本地资产，默认sandbox，不开放外部访问。只在核对本批PID和精确config后停止自建预览，既有服务不动。
