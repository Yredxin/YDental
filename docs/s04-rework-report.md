# [CODEX] S04修正交付与复核申请｜YD-N1 R1

按[#28 GPT-REVIEW6114781429](https://github.com/Yredxin/YDental/issues/28#issuecomment-6114781429)仅修两个BLOCKER，申请GPT技术复核；不是GPT或用户验收通过。继续原S04会话和`codex/s04-patient-r1-20261011`分支，起点`3b74b33987252d59033ae4b9d6757ad609818216`，工作区原先干净。返工前重读#23当前正文/有效评论及#28当前正文/全部有效评论，交付前再次读取#28全部4条评论，review未变。没有从撤销计划、旧四份文档或上一聊天补需求。

## 版本与范围

|项|固定事实|
|---|---|
|原交付|product `eb607750a4b35885f37acfb07d504f758b877b73` / test `a35af92ef89465dbbf71cb6f88297e4c097b43c7` / final `3b74b33987252d59033ae4b9d6757ad609818216`，原证据原样保留|
|本轮product|`887d0a9772a9ee165992ccd77af87fbb2c287d93`，包含首轮返工及RPC绑定补正|
|本轮test|`f3dc3dcb188511b19f9f2d898f45fbfdd6280663`；product→test只改测试/Firefox/probe，无产品变更|
|本轮final|仅AGENTS、返工报告/契约/安全复核和脱敏证据；完整SHA固定于#28修正交付评论，test→final不改产品或测试|
|产品tree|`95051feeb90f3bcfd9067dc72329b158eadabca9`，在最终test不变|
|核心/Python|锁定Yredxin/odoo `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明20.0；核心`.venv/bin/python`；不声称核对同SHA官方上游|
|最终新库|`ydental_s04_test_20261011233749_c7095425`；[OID/创建/配置摘要](evidence/s04-rework/final-isolation.json)|
|隔离|127.0.0.1:5432/odoo，cluster7694897083368259627；独立配置/data_dir/log，HTTP18106、精确dbfilter、list_db=False、cron=0，进程外发限制；仅合成数据|
|依赖/资源|不安装系统依赖，不改核心/odoo-12/既有服务/业务库；沿用进程本地phonenumbers9.0.16、Firefox155及字体/动态库，默认sandbox无关闭开关|

## Project先行操作

2026-10-11 23:22 UTC先完整读取Project #4 API公开的21字段、37条目、6视图（含全部显示/分组/排序字段）和7条workflow元数据，确认#28唯一条目和自定义执行状态唯一选项。仅一次mutation将#28自定义“执行状态”由待启用改为返工，随后完整读回及二次核对，整个Project快照仅这一值变化。

[before](evidence/s04-rework/project/before.json)、[prewrite](evidence/s04-rework/project/prewrite.json)、[mutation](evidence/s04-rework/project/mutation.json)、[after](evidence/s04-rework/project/after.json)、[second](evidence/s04-rework/project/second.json)。原生Status仍Todo，其他条目/字段、Issue OPEN、7条workflow enabled/元数据未改。GraphQL不公开workflow内部trigger/action，证据准确记录这一API边界；没有调用workflow或原生Status mutation。完成交付后执行状态仍返工，不自行改待复核。

## 两项修正及流程回放

|阻断|修正|实际验证|
|---|---|---|
|patient-owned partner读取旁路|模型read domain与原生域AND、live check_access/fetch、export双资格、image/HMAC请求者重查；native RPC由真实SID重建Binding，普通partner保留原ACL|none有效A会话，即使export=write，主联系人/监护人direct read/export拒绝；按name/phone/email的search/search_read/name/count/group无记录；前台合法行政读→显式撤权→下一请求拒绝；无YDental组/会话的普通内部账号仍能读普通partner|
|当前关系缺失仍可care/clinical|固定私有_current_relation先canonical，仅认current store/superseded=False；签发care及后续域、本店clinical新建/维护和原生clinical read/query均要求关系|B-only在A无关系：care GET/模型、原生RPC、本店新建拒绝且关系未增加；A前台显式relation后first_arrival为空；医生读B历史留痕、写A背景；失效关系、合并后source旧scope均拒绝，只认target current relation|

原native partner Notes/chatter/owner写/unlink保护和附件分型/public/HMAC控制不变；不靠菜单或field groups。原患者号、旧号、统一身份、合并锁/事务/幂等/版本、活动冲突钩子和历史快照不重写：原patient/number/relation/merge/record模型文件完全相同；service原方法只有_clinical新增关系前置，其余原方法AST不变。

前台原流程（跨店查档→新关系→共电话提示→门店申请→集团确认→旧号查询）、真实到店、本店政策、行政/临床分层均全量回归。字段未新增，沿用[原字段字典](s04-data-dictionary.md)，最终probe仍9模型100字段。新增规则见[返工契约](s04-rework-contracts.md)和[安全复核](s04-rework-security-review.md)。

## 最终完整验证

均在固定test `f3dc3dc`、上述最终新库执行；以下是一次完整最终结果，不累加历史成功数。命令从仓库使用`../.venv/bin/python`，`scripts/s04.py ACTION --db ydental_s04_test_20261011233749_c7095425 --port 18106`。

|检查|最终结果|证据|
|---|---|---|
|install|exit0，0 failed/0 error/38 tests：S04模型24+真实HTTP/RPC12+底座2|[runtime-history](evidence/s04-rework/runtime-history.json)|
|probe|exit0，7/7真实多连接竞争PASS，独立RR快照/有界重试；22原身份/22号码映射，唯一/canonical且无患者账号|[final-probe](evidence/s04-rework/final-probe.json)|
|upgrade|exit0，0/0/36，全部S04模型24+HTTP/RPC12|[runtime-history](evidence/s04-rework/runtime-history.json)|
|native i18n export|exit0，225/225，无缺失/fuzzy|[translation](evidence/s04-rework/translation.json)|
|Firefox155|37/37 PASS：原22项+新增15项，pageerror=0，10张合成截图|[final-browser](evidence/s04-rework/final-browser.json)|
|guard|5/5 PASS：错库、错端点、错误端口、外发DNS、其他本机服务拒绝|[final-checks](evidence/s04-rework/final-checks.json)|
|静态/工程|38 Python AST、git diff check、核心tracked diff空、旧证据未改、隐私/截图SHA/相对链接检查PASS；自建预览精确停止|[final-checks](evidence/s04-rework/final-checks.json)|

7组probe原实现保留：8路唯一发号、同建档key、同合并key、同申请异key/version、business先于merge、merge先于business、双向merge不成环。合并引用前后数和blocked冲突清单完整留在final-probe.merge_samples；未执行的真实活动业务不冒称验证。

新增模型测试4个、真实HTTP/RPC测试4个分别在test_patient_rework.py/test_patient_rework_http.py。覆盖主/监护人、export-only、普通账号、缓存预热/撤权、普通和limited-HMAC image、B-only前后关系、旧scope/失效关系/canonical merge；原forged context、other session、撤权、跨店write、finance拒绝继续成立。

Firefox通过原生res.partner客户/联系人表单（base.action_partner_form）请求web_read，并检查真实AccessError及退回可见列表无患者/监护人，普通联系人表单成功；06b可见中文权限错误。截图06a是拒绝后列表挂载时刻，拒绝依据是实际web_read错误，不以空白截图单独证明。07明确A关系已建立但尚未到店，08同时展示只读B历史与可维护A背景。

|TC|本轮适用结果/角色|未来真实复验|
|---|---|---|
|S04-T01|PASS；跨店统一档/关系幂等/预建无到店/真实首次UTC与本地日期；前台、医生；新增B-only关系前置|S05预约→到店NOT_RUN|
|S04-T02|PASS；共电话/同名生日/联系人提示、不猜地区、不自动合并；前台|—|
|S04-T03|PASS；门店确认拒绝、集团确认、旧号及快照；合并后只认canonical current relation|—|
|S04-T04|PASS（基础+合成）；重试/版本/异payload/失败回滚及7组真实竞争；集团|S05/S06真实活动互斥NOT_RUN|
|S04-T05|PASS；原前台临床旁路负向；新增none患者/监护人native Contacts全查询/导出/image拒绝及普通partner正常|未来正式临床/PDF源NOT_RUN|
|S04-T06|PASS；A医生有current relation才按用途读B/C留痕；伪context/另会话/撤权/关系失效/跨店write/finance拒绝|S08/S09真实源、S10原生凭证NOT_RUN|
|S04-T07|PASS（合成历史）；更名/合并不改origin/actor/snapshot、关系重叠最早到店保留|真实病历/账单/PDF NOT_RUN|
|S04-T08|PASS；新库安装/升级、并发唯一号/建档重试、raw CRUD拒绝，无患者账号/自动通知/签署|生产迁移部署NOT_RUN|
|S04-T09|PASS（政策+合成事实）；本店待完善/待核验、不继承旧店签署，行政建档可继续|S12正式签署/PDF NOT_RUN|
|S04-T10|PASS（合成保护）；双活动/执行阻断、列冲突、处理后恢复，原RR竞争保护|S06队列/S08执行真实回归NOT_RUN|

## 数据、配置、失败与停止

原始3b74b33和全部历史失败链保留。本轮首install的RPC绑定/测试API问题，以及Firefox等待错误提示的超时，均在[失败链](evidence/s04-rework/failures.md)、各次summary、runtime日志SHA中保留；原始日志/凭据保持私有，不发布配置内容、session/cookie、患者实料、签名或备份。三个库均由本轮runner新建并记录OID；未接管旧S04、S00—S03或业务库。

合并/行政动作仍沿用原savepoint+审计+回执，无产品手工commit，无新增资金/库存/费用动作；本轮无新配置或字段级权限体系。号码格式、监护/证件政策、正式正文/签发等仍按#23责任阶段审核，不提前设业务门槛。回滚范围是当前独立分支和本轮隔离资源，没有生产部署；不自动删库或失败材料。

S03技术PASS仍待统一用户验收；S04申请GPT复核，#28保持OPEN，Project自定义执行状态保持返工，原生Status/workflows/Issue/PR状态不改。S05/S06/S08/S09/S10/S12真实业务联调、患者门户和自动通知均NOT_RUN/未实施。

**#28修正交付评论写回并完整读回后停止等待GPT，不进入S05，不关闭任务或发布生产。**
