# S07 定向修正技术报告（Codex自测）

唯一返工依据：[GPT-REVIEW6121445246](https://github.com/Yredxin/YDental/issues/31#issuecomment-6121445246)。本轮完整读取#23当前正文/全部2条有效评论、#31正文/全部4条有效评论；原启用仍为6119956887，修正范围仅本次两项代码边界与SIGSEGV调查。正文/有效评论和Project交付前再次读回不变，见[来源核对](evidence/s07-rework/source-final-check.json)。不使用撤销计划或旧聊天补规则。

|固定点|SHA/边界|
|---|---|
|返工baseline|f23ad62b20aa298b74adc993781863961946aec3|
|rework product|eb826219b008e8ebdf2073fc020a813f88764ecc|
|rework test|12730d0f69ddbbd4e21c5df76e0bc9e0c0480061|
|rework final|本报告与证据固定提交，完整SHA记录在#31本轮交付评论|
|分支|codex/s07-inventory-r1-20261012；原分支正常追加，不强推|
|核心|Yredxin/odoo@f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb；本地fork声明20.0；原venv和既存进程本地依赖|

原product/test/final及docs/evidence/s07、原SIGSEGV和失败记录完整保留。实际Git根 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`；origin Yredxin/YDental；开工HEAD等于返工baseline且工作区clean。只改库存service/event与对应中文、测试/验证脚本；S01—S06源码、核心、odoo-12、系统依赖与既有服务未改。product→test只测试断言/浏览器角色隔离，产品树相同；test→final仅AGENTS/文档/脱敏证据。[版本差异](evidence/s07-rework/version-boundaries.json)。

最终两新库为 `ydental_s07_test_20261012094527_249b480f`（18144）与 `ydental_s07_test_20261012094527_bbbbcece`（18145）。每个库均创建独立marker/OID/config hash/data_dir/log/dbfilter、校验127.0.0.1:5432/odoo和cluster，使用S07网络guard，SMTP外发关闭；不复用、接管、重置或删历史库。只停止匹配本轮config/PID的预览。[环境](evidence/s07-rework/environment.json)。

## 三项实际处理

|问题|处理/结果|证据|
|---|---|---|
|BLOCKER-1 类别匹配|已修正；取得可信来源并检查medical/pharmacy-write后，创建event之前强制treatment→material、chairside/prescription→medicine。prosthesis无授权临床耗用组合。六种不匹配完整拒绝，event/move/quant/audit不变；合法药品/耗材、权限/重复来源继续回归。|模型34/HTTP14全量；两库各6组独立连接类别负向|
|BLOCKER-2 历史pending补账|已修正；只对不可普通改写的原already-performed pending、原摘要/价/时间/类别确认、当前店warehouse-write、足够余额及原pending之后本店同lot/目标库位的done真实入库/正向盘点纠正进行恢复。只该分支绕过当前_usable；新执行/release仍禁过期停用。保留原event/actor/responsible/数量/原价/时间，固定纠正关联和补记时间，唯一原native move与审计；异常完整回滚。|过期/停用模型、HTTP、两连接唯一恢复/新请求负向；Firefox及native trace|
|SIGSEGV evidence-blocker|完成隔离调查与重复回放，未再现；根因仍UNDETERMINED，不能称已修复。正式部署保持BLOCKED。两次最终新库/新进程完整回放均PASS，另保留前两次夹具权限失败的部分回放。原固定be4a282的274个addon源码字节与Git核对，另新库/新进程install42、原probe12、原Firefox36/10/pageerror0及原SQL7类均PASS；诊断单列，不计入修正版本PASS。|[调查结论](evidence/s07-rework/crash-investigation-final.json)、原日志哈希/进程/退出码/源字节核对及Firefox结果|

原pending恢复不假启用产品/batch、不改lot效期、不新造临床事实/入库，不重价。新增 `ydental_correction_id`、`ydental_reconciled_at` 区分执行时与补记时；原native完成时间、S01当前操作者与来源都可追溯。缺余额/缺真实纠正/无法确认来源继续pending/负责人/人工核查入口。详见[工程契约](s07-rework-contracts.md)、[字段/动作/错误增量](s07-rework-data-dictionary.md)、[安全自审](s07-rework-security-review.md)。

## 全量回归与实际流程

以下只计算固定rework test在最终两库实际运行，均为Codex自测，不代表GPT复跑、技术PASS或用户验收。每个模型/HTTP方法的PASS与实际Starting日志、命令/退出码/日志hash见[逐方法](evidence/s07-rework/final-tests.json)、[29次runner行动与失败链](evidence/s07-rework/actions-summary.json)。安装50含48个S07方法（模型34+真实HTTP/RPC14），另2个原生资产初始化；不冒称完整原生JS测试。

|TC/流程|状态|实际断言与边界|
|---|---|---|
|S07-T01 / F1|PASS|真实入10→发3→7、同请求/同来源不双扣；模型/HTTP/双连接/Firefox；实退quarantine1、可发仍7，核验后8|
|S07-T02 / F2|PASS|最后1份两独立backend只有1成功，native done后异常回滚；原12组竞争全部重跑，新增10组，共两库各22/22，deadlock0|
|S07-T03 / F2|PASS|后台直接过期/停用/伪造批次拒绝，原锁交错；历史补账后新普通/临床仍拒绝；没有改效期或假启用|
|S07-T04|PASS|包装换算、小数/粒度、非有限数/错单位、原生单位factor/祖先路径保护，精度无静默截断|
|S07-T05 / F1|PASS|实物退回核查/release/discard/上限竞争；独立退款不回库，治疗/已消耗椅旁不可变未用库存|
|S07-T06 / F3|PASS（S07）|原缺料pending→真实入库/正向实盘纠正→原event唯一恢复；S05真实演示20→99后仍20/原版本；过期/停用历史恢复、缺证据/错lot纠正拒绝、异常与并发、readonly/CRUD/RPC负向；时间跨越使用明确合成服务时钟，不改批次效期|
|S07-T07|PASS|原两店/两法人、会话旧页/实时撤权、patient/附件/native/RPC/export拒绝；warehouse-only浏览器角色原权限恢复，医疗独立账号仅S06读比较|
|S07-T08|PASS（S07）|每库install50→upgrade48→提交真实库存事实→再次upgrade48；各46个committed事件，event/batch/move/move_line/quant五组签名一致，8类SQL不变量0；原盘点/调拨/跨公司拒绝回归|
|S07-T09|PASS|master/price/warehouse分权、三类归位、原预警/首次入库当地日/扫码fail-closed；新增六种来源类别负向，合法medicine处方/椅旁、material耗材及pharmacy-only派生回归|
|原/新增Firefox|PASS|两独立干净进程各63项/12图/pageerror0；24图逐张目视核验；含S06只读入口与5轮对比、实际收发退核查及两种历史恢复；默认Firefox sandbox|
|中文/guard|PASS|每库实际导出223/223，metadata0缺失；最终固定test guard5，通过业务/历史名称、错误端点/端口和外发负向|
|真实S08临床/分次发药与S10费库款、S09检查、S11来源|NOT_RUN|未授权/未安装；当前真实S07库存+受guard合成来源+S05演示价；合成费用引用不是实际凭证|
|生产稳定性/发布|BLOCKED / NOT_RUN|SIGSEGV根因未确认；部署阻断，不把重复回放无崩溃当根因已排除；正式参数、50会话/生产未执行|

[Firefox结果/图与失败](evidence/s07-rework/README.md)、[24图目视核验](evidence/s07-rework/visual-review.json)、[native前后/纠正/双时间/审计](evidence/s07-rework/native-trace-final.json)、[第二库trace](evidence/s07-rework/native-trace-second.json)。原生账实3与可发0、停用/过期标识仍在；全库来源类别及恢复审计额外检查为0错误。[SQL与五签名](evidence/s07-rework/README.md)。

实际重放命令使用 `PYTHONFAULTHANDLER=1 ../.venv/bin/python scripts/s07.py <install|upgrade|probe|preview|serve|audit|export> --db <新库名> --port <独立端口>`；每个动作记录精确DB/固定SHA/命令/exit及日志hash。Firefox为 `../.venv/bin/python scripts/s07_browser.py --db <新库名> --port <独立端口>`；中文为 `scripts/s07_translation.py`，guard为 `-m unittest scripts/test_s07_guard.py`。install必须新名，原库不重置；preview只追加全新合成夹具并归档旧私有凭据，不伪造原业务。

人工效果：登录选店→见10份→实际发3/同键重试仍7→实退1待核查仍7→核验8→停用后直接出库拒绝→原pending缺料拒恢复→有据实收入5后补原2→过期/停用原事件同样恢复而新领用仍拒。只读账号无写表单且手工POST拒绝，集团目录权限独立、扫码未安装来源不假成功。

## 故障、返工与未解决风险

先提交16aef9c测试复现原缺口，install45记录6个类别子失败+2个恢复错误；并非修正版本PASS。c193bae全量50遇1个新负向失败：同秒旧收货误选。eb82621修正ID顺序，再加2535699断言。2535699两库模型/HTTP/upgrade/probe通过，但Firefox各55项/8图处失败：测试角色加前台读权破坏原患者拒绝前提。12730d0以独立医疗角色读S06后，另两个全新库全量重跑；原失败库/截图/日志hash全部保留。[完整失败链](evidence/s07-rework/failure-chain.json)。

原SIGSEGV（PID1048392、signal11、runner245）日志仍本地受控保存并哈希，不发布含会话的原日志。原运行未有fault handler；没有可用原始原生堆栈，当前无gdb/coredumpctl、RLIMIT_CORE=0、无对应PID内核记录，未擅自安装或改设置。新进程均启用faulthandler；最终PID1074950/1074949完成真实流程后受控SIGTERM，runner0，无fatal/segfault。核查不等于根因修复：仍可能来自核心/原生扩展/环境，正式发布前需隔离观察与责任阶段运维/发布复核；若重现，保留对应栈/信号与最小触发后定向处理。生产部署不获本轮授权。

原固定test对照：`ydental_s07_test_20261012095612_e87d0dc6` / 18146 / PID1080740，安装和运行的274个addon文件在前后均与be4a282逐字节相同，实际导入路径也已断言；只适配验证脚本路径/证据SHA，不修改产品或模型/HTTP测试。开启faulthandler，原36项/10图完整回放PASS，受控停止runner0，无SIGSEGV；全部10图另逐张核验。与两次修正版本完整回放一起仍不能确认根因，不取消部署阻断。见[源码对照](evidence/s07-rework/baseline-diagnostic-source.json)、[原probe](evidence/s07-rework/README.md)、[原图核验](evidence/s07-rework/baseline-visual-review.json)。

## Project、交付和停止

实施前完整读21字段/15条目/6视图/7公开workflow；本轮0 mutation。交付前两次完整深比较相同：#31 S07/进行中/Todo/OPEN，#30待用户验收，#32—#37待启用，其他阶段和workflows不变。不自行改返工/待复核/已验收。

final正常推送原分支后，从GitHub逐文件完整blob读回并核对字节/hash和远端HEAD，再在#31发布 `[CODEX] S07定向修正交付与复核申请`，逐字读回后立即停止等待GPT。原生历史不可普通删除，成功动作不能删move/改quant抹账；纠正用有据追加事实。未做破坏性卸载、生产降级或部署。不关闭Issue、不合并/强推、不启动S08。
