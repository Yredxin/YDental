# S06-C 交付报告

来源：[S06-C 唯一启用边界 6118760114](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118760114)，#23 当前总计划/有效评论、#30 当前正文/全部有效评论，以及 A 最终技术复核 6117519348、B 原技术复核 6118213551 与修正 PASS 6118669357 均完整读取。基线 `a32ab4c6bab76aaabc45e1917ad06444d6a2b71c`；新分支 `codex/s06-c-day-push-r1-20261012`。独立当前 C 会话，不从已撤销计划或旧聊天补业务规则。

[开工条件检查 6118793557](https://github.com/Yredxin/YDental/issues/30#issuecomment-6118793557) 已写回逐字读回。完整 Project #4 的21字段/15条目/6视图/7公开workflow元数据在实施前读取；#30 已为 S06/进行中/Todo/OPEN，按授权 0 mutation；#29 保持 S05/待用户验收/Todo/OPEN。完整读回深比较无差异；没有修改workflows/其他条目/Issue状态。交付不自行转待复核或用户验收。

## 固定代码与边界

|固定点|SHA/含义|
|---|---|
|B baseline|a32ab4c6bab76aaabc45e1917ad06444d6a2b71c|
|C product|776d4dfb67ccdb61d4fa98f7dbf09ac943b091d9|
|C test|cce0aa2ec04ac590fc182f7279b36812e4e4760a|
|C final|固定于 #30 `[CODEX] S06-C交付验收申请`；包含本报告与脱敏证据，避免自引用SHA|

product→test 只变更测试脚本/测试模块；test→final 仅文档、AGENTS 当前执行记录及脱敏证据。原 A/B 产品、测试及失败链完整保留。82 个原 A/B 测试方法 AST 连续性检查未修改/未删除。

实现复用 S03 营业事实与 capacity-write；open→draining→closed、已有队列清队与 closed append/hold 例外。多业务日 queue segment 保留旧身份及 missed，真实 upgrade 兼容旧task唯一约束；当地00:00/00:10、幂等清理水位、延迟补跑、执行/hold/verify 跨日。原生 bus transactional outbox/最小版本通知、DB snapshot 校准和高熵摘要凭证区域屏。详见 [契约](s06c-contracts.md)、[字典/动作表](s06c-data-dictionary.md)、[安全自审](s06c-security-review.md)。

## 隔离环境

锁定核心 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明 Odoo20；fork 无父根快照，不冒称官方同SHA核对。核心 `.venv/bin/python`，PostgreSQL `127.0.0.1:5432/odoo`、cluster `7694897083368259627`。仅 `scripts/s06c.py` 新建的 `ydental_s06c_test_14位时间_8位hex` 合成库；创建记录/OID/endpoint/独立config哈希/data_dir/log/精确dbfilter/localhost18136/PID和外发guard每动作重验。无旧库接管、删除/重置命令、核心修改、系统依赖安装或既有服务停止/重配。

最终全新库 `ydental_s06c_test_20261012070143_6a254bfc`。固定test的 install **103**、upgrade **101**（**78模型+23真实HTTP/RPC**）全部通过；真实 A21+B16+C16=**53/53**、deadlock=0；Firefox A36/14图+B29/10图+B返工18/9图+C34/9图=**117项/42图**，pageerror=0。guard **5**、翻译 **282/282**（代码metadata无缺）、B形态真实upgrade迁移均通过。新增最终C的9图已逐张目视核验。

最终只读数据库核对：live patient/execution、水位、清理审计均无重复；**682** committed outbox 每个版本恰有一个实际原生bus消息，invalid digest=0、deadlock=0。该核对在停止匹配PID的本次预览后执行，没有修改数据库。

证据汇总：[final-runtime.json](evidence/s06c/final-runtime.json)、[test-breakdown.json](evidence/s06c/test-breakdown.json)、[final-concurrency.json](evidence/s06c/final-concurrency.json)、[final-browser.json](evidence/s06c/final-browser.json)、[final-database-invariants.json](evidence/s06c/final-database-invariants.json)、[visual-review.json](evidence/s06c/visual-review.json)。原始日志/配置/登录/lease/screen明文token只在受控私有运行目录，访问文件0600，仓库仅摘要、合成截图与哈希。

## 验证映射

|需求/TC|实际验证|
|---|---|
|S06-T11|report先提交→draining、draining先提交→report、非空close拒绝、start清队后close、closed append vs普通report；独立backend/barrier/锁交错与RR重试|
|S06-T12/T20|23:55/00:00/00:09:59/00:10，start-first保留实际执行、cleanup-first拒绝旧call/start，active/verify hold与verify execution首次cron清理保留，disabled station不启用|
|日终水位|两worker仅一成功水位/最终事实；失败savepoint回滚后重跑；00:30补清不影响今日新report；昨日task/entitlement/claim/容量事件保留|
|今日历史|昨日entry/date/number/missed保留，terminal不复活；昨日permit expired；当前S05合法派生任务今日实际到店+report产生新段、missed/priority重置；不是搬日期|
|迁移|全新C库构造B旧task唯一约束/行形态，真实 -u 后旧identity保留、missed回填、新task/day约束；不称完整B源码树安装升级|
|S06-T13|实际原生 bus `_poll` 消息版本精确等于 committed outbox；flush=False savepoint和整txrollback不发成功；真实 WebSocket frame 与 socket关闭重连，gap/旧version校准|
|screen|digest/只读/无普通ACL/撤销下一请求/绑定scope；真实 revoke vs snapshot RR读；masked_name多字符/单字/空白/不可见字符；实际lease station与capacity来源不同|
|撤呼/settlement|真实撤呼后旧快照retry、旧version/gap/重连不复活或重播；settlement类型不能call，不入screen，页面无raw patient/task/电话/临床/金额|
|A/B回归|A21+B16真实竞争、原82方法及原Firefox36+29+18项，verify现场处理/hold可信目标/restore/handover/continuation/append/revoke与S05/S04/S03连续性|
|环境/语言|guard5、实际export PO中所有源词无漏译/代码metadata正确；Firefox中文可读且0 pageerror；C新增截图逐张人工目视核验|

## 中间失败与修正

保留 `intermediate-runtime-history.json`、每次唯一命名 C probe/browser attempt 与原历史 A/B 证据，原始日志留私有目录并记录哈希。

- 最初install的两处测试夹具错误：停用station写缺version，settlement夹具默认callable与业务类型冲突。修正夹具后真实upgrade通过；最初运行期间有源文件编辑，明确不作最终固定证据。
- 初次C竞争准备资格时营业已closed，S05合法拒绝；改为先准备资格，未放宽产品资格。
- revoke-first与撤呼-first分别暴露RR旧读，增加token和scope `FOR SHARE` 只读fence；重新完整竞争通过，未把失败改写为PASS。
- 两次16组竞争已完成，但浏览器夹具在23:55申请早先时段资格/缺queue_bind导入使整进程失败；区分“竞争组通过”和“完整probe通过”，修正合成准备顺序/导入，保留两次进程非零结果。
- 首次Firefox营业表单误用lease confirmed引发pageerror；修正业务表单与lease确认/holder存储列表。第二次浏览器旧夹具仍持原lease，不能凭新浏览器强抢，保留失败并创建新独立夹具，不篡改旧lease/history。
- 通过截图目视发现serving行误显示day_closed资格提示，修正仅waiting/calling计算call资格提示，并增加浏览器回归断言。
- 补强首次清理active/verify hold/verify execution，以及昨日permit/missed的午夜UI检查；重新使用全新最终库、固定test验证，不沿用旧test的安装结果代替。

## 未执行与交付状态

上述 PASS 仅 Codex 隔离合成自测，不代表 GPT技术复核、用户验收或生产通过。实际 S08 保存/文书/医嘱/发药、S07库存、S09检查结果、S10收费队列、S13 50会话性能及生产部署均 NOT_RUN。保存及可信目标hook继续默认fail-closed；没有管理员remote force-release。心跳/超时/N未生产批准，合成2秒/20秒或7200秒/N=2不当生产值；00:00/00:10为确认业务语义，cron频率/worker/WebSocket proxy仍待部署发布。

完成 #30 `[CODEX] S06-C交付验收申请` 写回逐字读回后停止等 GPT 技术复核；不启用S07、不关闭#30、不强推/合并/生产发布。

## 复现入口

使用同一核心/既有本地依赖、全新合成库名及未占用隔离端口；不能把以下流程套到历史库/业务库。固定test checkout 后顺序执行：

```text
../.venv/bin/python scripts/s06c.py install --db <全新C库> --port 18136
../.venv/bin/python scripts/s06c.py legacy_seed --db <本次C库> --port 18136
../.venv/bin/python scripts/s06c.py upgrade --db <本次C库> --port 18136
../.venv/bin/python scripts/s06c.py migration_check --db <本次C库> --port 18136
../.venv/bin/python scripts/s06c.py probe --db <本次C库> --port 18136
../.venv/bin/python scripts/s06c.py export --db <本次C库> --port 18136
../.venv/bin/python scripts/s06c_translation.py --db <本次C库>
../.venv/bin/python scripts/test_s06c_guard.py
../.venv/bin/python scripts/s06c.py serve --db <本次C库> --port 18136
```

预览仅绑定本机；运行 `s06c_a_browser.py`、`s06c_b_browser.py`、`s06c_b_rework_browser.py`、`s06c_browser.py`，参数同 `--db/--port`。C browser 调用固定 `time_midnight/time_cleanup/time_delayed` guard 步骤，仅写本次 C 午夜合成 clock，同一服务实际清理；JSON客户端不能传可信时钟。preview PID/config 精确匹配后只停止本次进程。组合probe先完成C跨多日时钟竞争，再建立A/B活跃UI夹具，避免全局真实timeout扫描受到合成未来时钟干扰；所有原竞争仍完整执行。
