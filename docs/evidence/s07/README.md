# S07 脱敏证据索引

固定 baseline `46833f0ac4bd37b778f3a5a80d51be430e4ebde6` → product `916492719e5d299fa0326330ac798cd6cda237bd` → test `be4a282dc0ebb54fc32dfafa7ac05cfa7535d939`；final固定于#31交付评论。所有最终测试均执行于test，证据在仅文档/AGENTS提交保存。本文链接可由最终commit直接读取；本机原日志/private config/密码/cookie不发布。

|证据|实际内容/结果|
|---|---|
|[environment.json](environment.json)|最终全新S07库、端点/cluster/OID、config哈希和无密码安全配置、锁定底座及提交|
|[version-boundaries.json](version-boundaries.json)|baseline祖先、product/test产品树相等、只测试差异、核心/既有阶段源码保护及私有凭据扫描|
|[actions-summary.json](actions-summary.json)|37次真实runner行动，完整命令/数据库/提交/退出码/失败计数/原日志sha256；首次失败/修正链，原日志均hash复核|
|[final-tests.json](final-tests.json)|install42、两次upgrade40，40个S07方法逐项PASS（29模型+11HTTP/RPC）；每项实际Starting存在、总计0failed/0errors|
|[最终并发probe](probe-attempts/ydental_s07_test_20261012085648_03913c2a-20261012T085932040823.json)|12组独立backend竞争、barrier/锁交错、有界序列化重试、native动作完成后异常原子回滚；12PASS、deadlock0|
|[最终Firefox](browser-attempts/20261012T090243076439/result.json)|36项真实操作PASS、10张截图sha256、0pageerror，默认安全sandbox|
|[逐张目视核验](visual-review.json)|10张最终图均view_image检查；数量、pending/原move、责任人、权限、中文和无敏感信息|
|[最终SQL不变量](invariants/20261012T090457119112.json)|29个已提交事件；7类错误计数全0、五组native/来源签名|
|[持久数据真实升级](persistent-upgrade.json)|probe/Firefox后audit→真实-u→audit，event/batch/move/move_line/quant五签名不变|
|[native-trace.json](native-trace.json) / [查询](native-trace-queries.json)|最终Firefox夹具7事件/7move/7move.line/9quant/9事件审计；直接原生记录和原价，均合成资料|
|[中文](translation-ydental_s07_test_20261012085648_03913c2a.json)|真实导出218/218、无缺项、代码前缀和odoo-python元数据正确|
|[guard.json](guard.json)|5项PASS，历史/业务库名、服务端口、错误端点、外发DNS和其他loopback服务均拒绝|
|[preview-stop.json](preview-stop.json)|仅停止匹配本次独立config/PID的预览|
|[preview-recovery.json](preview-recovery.json)|最终版本首次预览SIGSEGV，库存动作前仍10份；重启同一专属预览后36/10通过；底层原因未确定、不称已修复|
|[failure-chain.json](failure-chain.json)|初始错误/修正、Firefox实际已提交而脚本误判、错误commit元数据及最后安全收紧均保留|

## GitHub 唯一边界与 Project

- [sources/](sources/) 保存交付前#23/#31正文与全部有效评论、S06最终复核/状态回执；[source-final-check.json](source-final-check.json)记录正文未变及评论ID、读取时间/哈希。
- [project-before.json](project-before.json) → [project-after.json](project-after.json) → [project-second-check.json](project-second-check.json)，[project-diff.json](project-diff.json)仅一次#31执行状态变化。全部21字段/15条目/6视图/7公开workflow，分页已穷尽。
- [project-final-check.json](project-final-check.json)交付前完整重读，与second-check深相等，不改变其他条目/workflows。
- [start-readback.json](start-readback.json)为[开工评论6120104358](https://github.com/Yredxin/YDental/issues/31#issuecomment-6120104358)逐字读回。project-read-attempt1-empty.json为TLS失败空文件，project-read-attempt1-second.json为下一次读取；未重复mutation。

## 历史尝试不可充作最终通过

所有browser-attempts、probe-attempts、invariants和previous-*原文件保留。20261012T082247135168 Firefox因303预期错误FAIL，动作已提交，未重置；随后探索库及3675f1d版本通过，最终只有上表test/数据库/Firefox属于本次最终回归。previous-3675f1d保存当时的完整通过汇总，previous-9a9555f保存当时的版本核对；最后产品收紧直接factor/parent_path写入后，另建新库重跑，不沿用旧通过冒称最终。

早期两个probe/invariants的tested_commit错误记录核心SHA f0c5a9b，这是脚本cwd错误；对应actions明确实际addon提交ccdfd84/71e54e7，禁止把这些元数据称为最终测试证明。688f800修正git -C后最终新库所有相关证据已重跑且正确记录test SHA。没有覆盖、删除旧失败。

F1/F2/F3及T01—T09逐项范围和角色、重放步骤、未执行边界见 [报告](../../s07-report.md)。S08真实临床/发药、S10实际费款/跨法人成对交易、S11真实扫码加工来源均NOT_RUN；PASS只限S07真实库存侧+明确合成来源/真实S05演示快照。
