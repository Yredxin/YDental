# S05定向返工证据索引

需求只来自#29 GPT-REVIEW6115823569和本次用户指令的三个BLOCKER。product `754cc331386e8294225c6579c9b4daa555160f92`、test `68cbcdc3c5a7c0e16a8389e89a6ba44e9086bfc2`；final为本目录所属文档提交，完整SHA固定于#29修正交付评论。

|证据|用途|
|---|---|
|[来源](source.json)|完整读当前review、收口重读哈希未变；保留原76335d9|
|[Project唯一字段写及读回](project-state.json)|只将#29自定义执行状态从待启用改为返工；21字段/15条目/6视图/7公开workflow元数据读取，其他字段/条目/Status/views/workflows/实体状态不变|
|[最终隔离运行](isolation-attempts/ydental_s05_test_20261012014755_f53e6686.json)|新库端点/cluster/OID/config哈希/精确dbfilter/外发保护；install0/0/35、upgrade0/0/33、probe/export exit0|
|[实际模型/HTTP方法](model-http-cases.json)|21模型+12真实HTTP/RPC，新增4模型+4 HTTP；含跨法人trusted source和当地日边界|
|[最终13组真实竞争](probe-attempts/ydental_s05_test_20261012014755_f53e6686-20261012T015043612058.json)|全部双连接PASS，no deadlock、S03守恒、单位置、live task canonical|
|[原13组连续性](race-continuity.json)|与76335d9原证据核对同13个竞争名称/顺序/不变量；算法不改，T11接可信测试源|
|[最终Firefox](browser-attempts/20261012T015215824296/summary.json)|Firefox155默认sandbox，35项PASS、0 pageerror、11张合成截图|
|[翻译](translation.json)|原生POT268/268齐全，新增来源/营业日提示可翻译|
|[guard和静态](guard-and-static.json)|guard5项、compileall/diff检查、安全全模式扫查|
|[预览退出/人工图片/脱敏](preview-and-disclosure.json)|自建服务核对PID/config后退出；三张新截图人工查看、秘密值和图片哈希检查通过|

`isolation-attempts`保留本次所有失败/补交和中间新库；`browser-attempts`保留先29项通过后脚本FAIL的记录及最终PASS。原始日志/配置/凭据/数据库只在私有.local，公开只有合成摘要/哈希/截图。原[76335d9证据](../s05/README.md)和原报告/字典/失败链未修改。

测试permit是服务器冻结类型，普通JSON/context不能创建；它只模拟来源，真实S08和S06队列/叫号/租约仍NOT_RUN。正式价格政策、真实临床费款和生产/容量验收没有由本轮批准。
