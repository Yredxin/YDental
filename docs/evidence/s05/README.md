# S05合成证据索引

固定product `6818bc35c35e030976df71558b188844d4de1082`，test `90d1a41f8559542aed36f4fc0ff22897c17fb392`；final为本索引所属文档提交，完整SHA记录于#29交付申请。队列只有测试适配，真实S06/S08/S09/S10均NOT_RUN；正式价格政策待发布。

|证据|说明|
|---|---|
|[最终隔离运行](isolation-attempts/ydental_s05_test_20261012003654_1b657de3.json)|全新库`ydental_s05_test_20261012003654_1b657de3`，端点/cluster/OID/配置哈希/精确dbfilter/外发边界；安装27项及升级25项0失败0错误|
|[最终真实并发](probe-attempts/ydental_s05_test_20261012003654_1b657de3-20261012T003848177525.json)|13组双连接竞争，含两种停接交错、取消/consume、改期末额失败、定时转诊、merge/预约与登记、调价/恢复；无死锁、S03守恒、单位置|
|[最终Firefox](browser-attempts/20261012T003922681586/summary.json)|Firefox155.0默认sandbox，24项PASS、0 pageerror及8张虚拟截图|
|[翻译](translation.json)|原生POT 266词条，zh_CN 266项有译文|
|[隔离负向和静态](guard-and-static.json)|5项隔离拒绝回归；compileall/diff检查通过|
|[来源与开工读回](source-and-preflight.json)|#23/#29当前正文哈希/有效评论、activation/S04前置、开工评论逐字读回；收口来源未变|
|[预览和脱敏](preview-and-disclosure.json)|自建预览核对PID/config后退出、三张截图人工查看、公开材料秘密值扫描通过|

`isolation-attempts/`、`probe-attempts/`和`browser-attempts/`保留原失败及补交；不能只挑最终PASS覆盖历史。原始配置、访问凭据、日志和数据库仅保存在私有`.local/DB/`，不上传。本目录只含白名单摘要/哈希和虚拟截图；已扫描所有S05私有access值、校验所有截图哈希。未上传患者资料、签名、原始日志或备份。

`collect.py`只对新S05名式和已记录端点/cluster/配置哈希的本会话运行生成脱敏摘要，无数据库写入或采用旧库行为。
