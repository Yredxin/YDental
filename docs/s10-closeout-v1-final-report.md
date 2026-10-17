# YD-N1 R1 — S10-CLOSEOUT-PLAN-v1.1 最终交付：BLOCKED

本包不能申请S10技术通过，不能进入S11。最后一轮出现新的Native SIGSEGV，随后副本
终审保存读回不一致；按硬停止边界结束。A有已提交、独立读回的有限成果；B—E未运行。
不是“离线修复通过”交付，不声称完整五组、页面、PDF或全阶段PASS。

## 依据、版本及同步

项目负责人直接批准v1.1及本轮补充；不是GitHub P0-25 GPT授权。原完整计划、确认记录、
新补充见s10-closeout-v1-plan.md及evidence/s10-closeout-v1/R1-user-supplement.json。
原分支codex/s10-settlement-finance-r1-20261013，origin=Yredxin/YDental。
本次接管本地/远端c58dd6809b7f384be72b63785c7594990f428551，工作树干净。
#23/#34正文和有效评论重新核对，无他人新交付；#35 OPEN/0评论，不修改Issue/Project。
固定core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，产品内容与基线7d52d9e保持相同。

执行版本：R0 53665a184893e7056c20cb1d1241f4117a2be809；
R1 a9afc6173c87740014ae45db3f3e24d137ce8674；
R2 00e6c4a1d8e1c7f46c411de62aba18511defed0f（最后允许修复轮次）。
最终材料提交SHA由Git提交对象及正式回执固定，避免报告自引用。

三个实际预检均REST逐字全等读回：

- R0 https://github.com/Yredxin/YDental/issues/34#issuecomment-6231682329
- R1 https://github.com/Yredxin/YDental/issues/34#issuecomment-6231990732
- R2 https://github.com/Yredxin/YDental/issues/34#issuecomment-6232029326

各freeze、逐文件SHA、合同、实际评论和读回索引均保存。同步与业务结果分开：
预检同步成功；业务BLOCKED来自实际Native崩溃/证据门禁，不是GitHub同步问题。
最终材料先线性提交并实际push，再发表正式交付；最终评论/REST读回及该次push的实际SHA/
退出码保存在私有delivery-*和final-push-*材料，读回保存即STOP，不继续任何业务。

## 环境、保护及实际预算

唯一源P021 ydental_s10_test_20261017050000_21b0cafe/OID2122140，
cluster7694897083368259627。R0两次RO只代表R0时点；本次获用户明确批准的第3次
仅在R2硬停止、全包真正终点使用。三条均严格READ ONLY/REPEATABLE READ，ROLLBACK/CLOSE。
真正终点645表schema/全部存储行与源前相等，198份源filestore字节相等。

只用R0已创建的唯一副本ydental_s10_test_20261017080710_2494c102/OID2144127，
同cluster、独立18325/config/data_dir，原件真实复制无硬链接。R1、R2均独立完整RO/RR
准入对比各自上一有效尾审完全相同。无再次CREATE、换库、删scope、重建740或旧资金重放。
W5/P013/P014/P018/P022等其他受保护库0连接；源未启动Odoo或业务。

|项目|全包实际/上限|
|---|---|
|显式RO/RR|14/28，14次均ROLLBACK/CLOSE|
|源RO|3/3，最终额外额度已真正终点使用|
|维护/CREATE|各1/1，均R0，R1/R2新增0|
|Odoo进程|3/6：R0 exit1，R1 exit1，R2 exit-11|
|native最大连接池观测|1/8，每进程仅观测本副本DSN|
|COMMIT返回/独立核回|5/5（R0 scope、R1 scope、R2 acquire/confirm/correct）|
|COMMIT异常|0；release未到COMMIT，不能写成提交成功|
|HTTP/RPC/Firefox/原件GET|全部0|
|原件生成/旧件重渲染/新退款PDF|全部0|
|新D来源/费用/入款/退款、临时权限修改|全部0|
|S10升级|0/1|
|Issue/Project状态、S11、合并部署|全部0|

所有剩余额度封存，不自动继续或转作诊断。数据库和失败文件均保留。

## 修复与实际执行

R0和R1均拒绝了doc1.write_uid=1；不放宽为合法actor，不修改字段冒充7。
R0修复后显式actor.flush仍太晚：产品_operate内部savepoint退出已触发默认环境flush。
固定源码路径：clinical_service._operate:116→sql_db._FlushingSavepoint._close:178→
Cursor.flush:301→environments.Transaction.flush:744；default_env按environments.py:704
选择首个有效uid，本执行器最初为1。core tests/common.py:686在切测试身份时也显式绑定default_env。

R2只改新收尾脚本：每个业务调用以延迟lambda进入真实actor默认flush环境后才执行；
成功actor.flush清洁后恢复旧环境；dirty异常不切uid1刷新。产品/core零修改，
不手写write_uid，不改作者、版本、审计、四mutex、锁、不可变性或经济门禁。
实际core savepoint和Transaction.flush离线隔离测试7/5/6/41均通过；旧writer1仍拒绝。
R0/R1 acquire分别独立证明全部回滚，已提交scope107/108及各两条审计保留。
原始异常先保存、第二快照失败不能遮蔽第一异常，四路径实际observer离线测试通过。
首版离线测试选错secondary文件exit1保留；修正测试定位后exit0，不计业务PASS。

R2于2026-10-17预检逐字读回后执行，native PID965603/backend1483029。
合法责任人7使用scope109：acquire、confirm、correct门禁及独立提交核回均通过。
最后有效检查点r2-A-correct-committed：doc1 confirmed/v4/write_uid7/editor7；
新增版本9=v3/confirm/author7/previous2；版本10=v4/correct/author7/previous9，
原因CLOSEOUT wording only, no economic action。只改chief_complaint预定合成文字。
每次文书动作四固定mutex各+1；临床审计actor7；原版/更正版链和内容门禁通过。
三次正常心跳按原API执行；最后一次心跳和release未独立提交。

release业务调用已返回并完成actor flush和after snapshot，但在persist保存before文件的
读回阶段Native SIGSEGV。Python栈为json.decoder.raw_decode→json.loads→contract.read→
save→persist(runtime.observe)。这是Python faulthandler栈，**不是Native C根因栈**。
原始日志9964字节，SHA256
52e5ef4b7691b2eacf0b729358d0473ad8b3c2c270f8b77b99d5d81ea0a01fc1。
进程exit-11、SIGSEGV=true；release无decision、无COMMIT、无成功marker。
没有继续任何Odoo/浏览器，也没有启动GDB或扩大OS/PG/硬件专项；根因UNKNOWN。

## 五组实际结果

|组|实际成果|尚缺及结论|
|---|---|---|
|A|同源责任人acquire、confirm v3、纯文字correct v4已提交并独立读回；逐字段费库款不变|release未提交、真实工作台既存原件同SHA重取未运行；PARTIAL/BLOCKED|
|B|未进入本组|六项普通source/payment/audit write/unlink MODEL及真实RPC均NOT_RUN|
|C|未进入本组|原件/附件跨公司门店family/混源/撤权旧页/有效token/图片响应体均NOT_RUN|
|D|未进入准入，新增上游/金额动作0|真实身份日期权限及全部渠道日结准入、独立6/2源、failed恢复、丢响应先查证防重均NOT_RUN|
|E|未进入本组|带已提交业务S10-only升级、升级后真实UI/原件同SHA回归均NOT_RUN|

P021既采成果保留：同源740及350+390、原生付款核销、药房4+2、价格快照、内部bill原件、
退款日结/数量/实物/调拨跨法人及前台支付的正式限定子证据。各独立来源不拼接为单一患者。
P020 A真实已结清入口/当前PDF不重做。模型调用不冒称Firefox或真实RPC；本包实际网络0。
旧v→6、无效JSON、Native UNKNOWN及P023/24正式结论保留，不重判、不重跑旧单字段诊断。

## 经济及最终证据限制

最后有效独立correct检查点，相对于克隆初始全部选定存储经济事实精确相同：
旧invoice/payment/partial/refund/stock/fee来源及旧原件记录未变；全差异含新scope、文书、
版本、审计和必要mutex，完整私有字段先保存后判，索引脱敏。
本包终点离线读取副本198份filestore与复制基线逐字节相同。
这些断言限定到指定已验检查点/文件观察，不扩写为完整最终数据库健康或业务恢复证明。

自动副本最终RO连接已关闭，但save(r2-final-tail-RO.json)在序列化读回全等门禁失败，
保留原文件且不当有效基线。原第一异常、已取得raw服务器行、服务器digest、文件均封存。
本包终点仅比较这一次已得capture0045的70950行与该落盘文件，发现ir_ui_view/1123.arch_prev
一处字段差异；服务器文本逐行摘要匹配。该比较不是另一次测量，也未重建/修补旧快照。
save当时内存对象不可得，无法据此定位发生环节、推断数据库损坏/完好或根因修复。
不重复连接或重采副本，不执行P023/24类新诊断批次。

## 退出表、证据、回滚及下一步

完整22行见[s10-closeout-v1-exit-table-terminal.md](s10-closeout-v1-exit-table-terminal.md)，
逐行正式需求、P021完整历史对象、复用理由、所需组、本包实际结果、待补和最终执行SHA
见evidence/s10-closeout-v1/exit-table-reviewed-terminal.json。较早自动seal表亦保留，
本终点表为具体逐组结论；不覆盖历史裁定。F4/T08仅新增文字confirm/correct子断言，
T12升级和A尾链仍缺；T05/T10/T14/T16等缺口未消失。全表技术退出仍BLOCKED。

主要索引：five-group-actual-results.json、terminal-verified-partial-facts.json、
actual-budget.json、r2-prepare-all-result.json、R2-window-result.json、
terminal-tail-acquired-layer-index.json、source-final-preserved-r2.json；
完整私有流/异常/日志/快照不公开，terminal-private-evidence-manifest.json保存路径/大小/SHA；
terminal-file-sha256.json保存本包脚本、报告及脱敏证据逐文件SHA（排除自身和后发表回执）。

本轮产品/core不变，无需产品回滚。不reset/clean/force-push、不丢弃已提交scope和文书。
隔离副本与源全部保留，禁止现场清编辑锁、手写状态、删除版本/审计或恢复旧业务窗口。
若未来授权撤回测试工程，使用正常revert，不能以代码revert声称数据库提交被回滚。

最低后续动作是GPT独立核阅本次新Native事故、尾审证据限制及部分提交，再决定后续可用
执行环境、有效基线与尚缺release/真实原件/B—E的边界；本次不自动诊断、重采或恢复。
即使之后功能补齐，也须GPT独立技术裁定，再由项目负责人启用S11；生产财务/税/支付政策
及最终统一用户验收另列，不由本包放行。正式交付REST逐字读回保存后立即STOP。
