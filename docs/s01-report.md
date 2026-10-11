# [CODEX] 交付验收申请｜YD-N1 R1｜S01｜合成验证批次

S01 当前能力已实现并提交技术复核；**尚非 GPT 复核通过、用户验收通过或生产启用**。正式任免/安全参数未发布；真实临床、库存、费用、排班和坐诊不在本批实现范围。完成本申请后停止，不进入 S02。

任务与启用来源：用户在本次新会话明确要求开始 #25，先核对和发布开工检查再实施。[开工检查](https://github.com/Yredxin/YDental/issues/25#issuecomment-6107613041) 已成功发布、完整读回后才修改代码。需求仅来自 #23 当前正文、#25 当前正文及全部有效评论、#24 最终收口；初读时 #25 无评论，后续只有本次开工记录，无新增业务规则。当前正文/收口 hash 与复读时间见 [source-index.json](evidence/s01/source-index.json)。未读取撤销计划补需求，未使用旧会话聊天补规则。

基线 `6dbf0a0a8be966bee7b2250b2a77e5b4d70540d8`（S00固定交付）；实施与测试固定 commit **`abf7b243b12a3717ee63cab4247ae5d5a7d5c43f`**；分支 `codex/s01-access-r1-20261011`。产品 addon 在其父提交 `58e9b44d20d281a1f3edecf4372e5b7991f216e3` 已固定，abf7b24仅补强测试断言，产品 tree 相同。交付文档/证据提交在其后，模型、测试和运行工具 tree 不再改变；最终交付 SHA 在 #25 评论中固定。未创建/合并 PR，不关闭 Issue，不改 Project/workflow/原生 Status。Git 根、核心保护及 tree receipt 见 [code-receipt.json](evidence/s01/code-receipt.json)。

环境为锁定 Yredxin/odoo fork `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，声明 Odoo20.0，核心 `.venv/bin/python` 3.12.15。不声称核对了同 SHA 官方上游。运行只用新建 `ydental_s01_test_20261011103447_2298e42e`，端点 127.0.0.1:5432/odoo，独立 18089 HTTP 端口、配置/data_dir/日志、精确 dbfilter；先查 cluster/创建记录/OID，再运行。cron=0，workers=0，SMTP关闭；进程级外连与其他本地端口禁止，浏览器仅允许本预览源。运行证据不含配置正文、原始日志、账号凭据、cookie/SID 或 token。既有业务库、历史库、服务、Odoo 核心、odoo-12 和父目录未跟踪 AGENTS 保留。

## 需求完成情况

|#25 项/功能|状态|实现与实际范围|
|---|---|---|
|3.1 账号—员工—法人—门店；公共/私有隔离|完成当前能力|原生 res.users/hr.employee/res.company；每公司员工唯一；门店经营场所、公共 related 字段；按登录名或明确已有账号 ID 复用，不宣称根据未确定证件策略自动识别人|
|3.2 入职、加店、移店、集团离职|完成当前能力|私有服务原子处理；历史保留、最后公司员工归档、其他店账号启用；S03仅扩展契约|
|3.3—3.5 16 类三级业务权、独立管理身份|完成当前能力|membership/grant；普通人员上限与禁止自改；店长本店授予例外；集团按允许公司；系统/集团组不由模板授予|
|3.6 整体覆盖模板|完成|16项预览、明确确认、receipt再检查、缺项无、展开脱钩、任一越权整批拒绝；每项前后审计|
|3.7 医疗用途共享读与跨店写分离|部分：安全契约完成|合成医疗/财务源验证；不限制合法 care 历史读取，不开放 C 财务原单；真实病历在 S08复验|
|3.8 会话、旧页、撤权|完成当前能力|服务器 SID绑定、页版本、真实独立登录；切店不改全局组/用户公司；S03默认安排/S06真实执行仅上层钩子|
|3.9 内部创建、邀请、安全配置|部分：配置能力完成|禁止自助注册/门户提升；原生重置/邀请受理入口；密码/MFA/闲置可显式配置；正式参数及真实通道/闲置周期未验|
|3.10—3.11 公共审计、保护查询、导出|完成当前能力，实际业务待下游|actor/source/store/target/action/UTC/result/reason/metadata；普通账号无审计 CRUD；源 read + 本店 export write；原生 CSV、RPC、附件、HTML报告实际回归|

没有 OCA依赖。原生复用及开源替代调查已在开工检查登记：OCA/server-auth、OCA/multi-company 存在，未证明兼容本 fork，当前方案按 #23 原生+自研。新增 `ydental_access` 为实际能力；`ydental_access_test` 只放隔离合成验证对象，不用于生产，不建立未来业务空壳。

## 流程实际回放

|示例|合成前提/操作|实际结果与证据|
|---|---|---|
|F1|operator：A space写、B读、C无；直接模型、DataSet、页面；第二条越权批量/伪造context|A写成功；B只读；C空工作台；越权整批拒；T01、T13及浏览器|
|F2|两个真实登录 Cookie分别A/B；同会话旧页；撤A权限/移除A任职|两会话互不切店；旧页409；旧附件拒绝；B登录及读仍可用；T03—T05与浏览器|
|F3|A额外 warehouse read；前台模板缺warehouse/medical；再改模板、带非法B目标|warehouse/medical清none；B原权不变；后改模板不传播；非法批量无部分提交；T09|
|F4|无结算权的独立A店长授A；普通人员超级别/自改；审计与导出|店长本店例外成功、B拒绝；普通人员拒绝；view/modify/export独立真实actor事件，直接改删日志拒绝；T02/T10—T12|

## 测试结果

空库安装固定于58e9b44；最终升级及浏览器固定于abf7b24（产品 tree 相同，仅测试补强）。各次实际commit、日志 SHA256见 [runtime-redacted.json](evidence/s01/runtime-redacted.json)。命令均从 addon Git根执行：

```bash
../.venv/bin/python scripts/s01.py install --db ydental_s01_test_20261011103447_2298e42e --port 18089
../.venv/bin/python scripts/s01.py upgrade --db ydental_s01_test_20261011103447_2298e42e --port 18089
../.venv/bin/python -m unittest -v scripts.test_s01_guard
```

安装/升级启用 `/ydental_access_test` 标签。框架汇总分别 **21/19 项，0 failed、0 errors，退出码0**；本阶段有16个模型测试方法（13 TC + 3补充）和3个HTTP方法。不能把框架汇总数、方法数和13个TC当成同一口径。5项隔离保护测试通过，退出码0，见 [guards.json](evidence/s01/guards.json)。Firefox155 默认安全控制、15项 UI 检查通过，见 [browser-final.json](evidence/s01/browser-final.json)。

下表 PASS 仅指本阶段已具备能力及明确合成对象；共用上述安装/升级命令，角色见对应测试方法，不能读成真实临床/财务验收。

|TC|状态|角色/证据与限制|
|---|---|---|
|T01|PASS 合成|operator；test_t01_store_levels_and_batch、HTTP RPC、浏览器A写/B读/C无、伪造context及批量|
|T02|PASS|manager；test_t02_store_manager_exception；本店超自身业务等级授予可行，B/管理员身份拒|
|T03|PASS|operator；test_t03_scope_independence_and_old_revision、两个真实HTTP登录、双Firefox上下文及旧页409|
|T04|PASS 合成|operator；test_t04_revocation_and_attachment；原生附件/public/token及撤权下一请求；真实文书下载 NOT_RUN|
|T05|PASS 当前；排班NOT_RUN|group；test_t05_removal_and_departure；最后公司员工归档、跨店账号/历史保留；浏览器移除A后读B；S03排期待验|
|T06|PASS|group/HR合成夹具；test_t06_common_and_private_employee_fields；A/B同员工、C另一员工；公共岗位/能力同步、私有部门不互盖；浏览器关系复验|
|T07|PASS 合成；真实联系人联调NOT_RUN|operator；test_t07_minimal_information；搜索无医疗源、联系人fields_get及dashboard不暴露合成正文；实际患者字段待S04/S08|
|T08|PASS|group；全新库安装/升级及test_t08_idempotent_membership_and_account；UI重复建同login复用账号；模板重复另见T09|
|T09|PASS|group/manager；test_t09_template_replace_detach_and_atomic_batch；模型完整覆盖/解绑/跨店拒；UI16项预览后确认|
|T10|PASS|personnel；test_t10_personnel_ceiling_and_identity；超自身级别、自改、直接店长字段拒；公司范围/最后管理员额外回归|
|T11|PASS 合成；真实病历NOT_RUN|operator；test_t11_events_and_immutable_audit；view/modify/export事件、真实actor及metadata，普通改删拒；更正待S08|
|T12|PASS|operator；test_t12_export_requires_both_permissions、native_export补充、HTTP原生CSV；单条件拒、双条件成功且留痕|
|T13|PASS 合成；真实坐诊NOT_RUN|operator；test_t13_care_history_and_execution_hook；A care读取C医疗、C会话拒、跨C写/财务拒；执行钩子mock不是真实租约|

补充方法验证：未配置任免拒绝、显式合成政策配置及最后店长/系统管理员保护、短密码拒绝；集团操作限允许公司；原生导出 gate及模板旧预览拒绝。参数测试回滚，不自动发布到预览或生产。中文原生导出覆盖198词条、无缺译；截图另复核引用及显示，见 [translation-coverage.json](evidence/s01/translation-coverage.json)。

失败/补交过程长期保留于 [attempt-history.json](evidence/s01/attempt-history.json)：首次安装重复原生参数键导致255/NOT_RUN；原生导出组遗漏导致2 errors；HTTP测试未使用原生受保护 test-cursor opener导致3 errors；页revision=0渲染为空导致3 errors；PO写出丢native`:0`引用导致升级255/NOT_RUN。均修复后补交，不算当前通过。首个Firefox尝试通过13项后因旧式Owl props失败，失败截图及诊断保留；修复后15项通过。视觉复核又补全预览表头的翻译引用和导航对比度，最终固定提交重新验证。

## 字段、动作与配置

完整模型字段、账号/员工公共同步表、16类动作权限、实际动作/原子副作用/恢复、下游事件映射与参数表见 [s01-contracts.md](s01-contracts.md)。门店按有效 IANA时区初始化；业务时间存UTC。模板无反向链接；不物理删除员工任职、授权和审计历史。

|配置|当前方案|确认来源/正式状态|
|---|---|---|
|店长任免/最后管理员|group_with_replacement：独立集团按允许公司任免，撤最后店长/集团/系统管理员前有接替者|本会话提交的可选方案；用户尚未选择，未配置/发布|
|集团/技术角色|独立原生组，人员名单须明确配置；安装不自动授 base.user_admin|合成夹具明确角色；正式名单待用户|
|岗位模板|整体覆盖；medical/exam明确授权，不为摘要自动授予|合成前台模板仅测试；正式明细待用户|
|密码/MFA/闲置|建议12字符、内部MFA、15分钟；可配置原生参数|仅建议，未批准/发布；预览沿原生默认密码长度8；正式通道/次数策略另确认|

权限模板前后例：A的 frontdesk none→read、medical read→none、space write→none；其余缺项全部none；B的space read保持read。模型F3另测 warehouse read→none，模板后改不影响既有展开结果。预览显示16项及确认，见浏览器截图。

## 用户效果验证

仅隔离预览 `http://127.0.0.1:18089/ydental/access`；实际员工入口 Dental→门店与员工。角色为合成 group/manager/operator/personnel/portal，不提供生产登录。私有凭据仅本机0600文件，未入库/GitHub。本次Firefox自动回放以下流程，截图索引见 [browser-final.md](evidence/s01/browser-final.md)。这是Codex实测，仍需用户亲测确认。

1. 集团角色选A，创建合成员工，再用同login创建一次：复用同账号；没有HR/系统角色提升。
2. 给A空间读写，切B关联同账号并授空间只读：同公司员工编号相同；只改目标店。
3. operator两个独立浏览器登录分别选A/B：第一会话保持A；另一个切C不影响第一。
4. 在A合成源写一次；保留旧标签，再同会话切B提交旧标签：返回409，旧页不误写。
5. C合成工作台没有可见业务记录；无医疗权不提供完整医疗源。集团历史读取另由T13模型证据证明。
6. A店长为operator选合成前台模板：显示全部16项前后值，确认后A空间/医疗清无；B空间只读不改。
7. 请求旧A附件被拒；集团只移除operator的A任职，再用另一个会话选B：仍可登录读取B，历史未删。
8. A店长打开原生后端：全局门店提示显示A、执行位置为空；审计页出现登录/切店/授权/模板/移店事实。门户访问员工入口403。

浏览器脚本为上述流程创建独立测试账号且修改合成预览状态，最终operator已移除A；人工复验可用集团角色重新关联A、按测试前提授权，不把合成值用于生产。脚本的完整可复现命令及本机依赖说明见 browser-final.md；不安装系统依赖、不关闭浏览器安全控制。

## 数据、审计、安全与回滚

本批新增门店/任职/授权/模板/能力/session/audit表及两个公共人员字段；原生员工公司私有字段保持原语义，没有费用、库存、资金或患者迁移。schema变更只发生在新S01库。成功业务与审计同事务；HTTP业务失败savepoint回滚后另记录denied，直接模型拒绝只记不含正文的安全日志。审计事件不可普通改删，查询不能绕过源读取。源正文只用于明确合成测试，不进入审计前后值。

按odoo-guidelines/odoo-web-guidelines/odoo-security对本次addon做Codex自审，位置及命中处置见 [review-sweep.json](evidence/s01/review-sweep.json)：sudo限私有固定模型服务和审计/投影；3条SQL仅参数化锁；业务方法私有；CRUD/批量每次校验；POST+CSRF、输入白名单；QWeb/Owl转义；related_sudo=False、session hash NO_ACCESS；无不可信eval/文件路径/动态属性。集团允许公司、普通人员上限、独立店长例外、原生export gate和最后管理员均有负向验证。本自审不替代独立技术复核。

原生附件/HTML报告读取会触发审计写，当前无只读副本环境下原生框架已实际重试到主库写cursor。只读副本路由兼容、真实PDF/实体出纸、真实临床/库存/财务事件、S03排期、S06全局租约、50会话/持续备份、真实邀请受理/送达、真实MFA与长期闲置周期均 **NOT_RUN**。邀请入口只在原生调用成功后返回受理，未发送实际邮件，不把入口存在视为已验证送达。不关闭框架安全控制或写库保护来补证。

一次本机目录枚举包含隔离测试会话文件名；未发布其值，未写入公共证据，并在新预览启动前把本批停止运行的测试session目录移出有效会话路径，保留私有材料、使测试会话失效，见 test-session-retirement.json。后续只读取明确证据文件。

回滚：尚未部署业务环境；既有环境无本批变更可回滚。隔离预览只有本批独立PID；需要结束预览时先核对PID命令行仍为本库独立配置，再仅停止该进程。保留所有失败库/日志/证据，不自动drop或重用；不能以卸载业务模块代替正式恢复方案。若以后获准部署，先做对应库+filestore恢复准备、由所属发布批次验证，本次没有生产回滚/恢复声明。

## 复核申请

申请审查固定实施commit及其文档/证据交付：#25当前S01能力、13TC合成范围、原生HTTP/导出/附件/HTML、Firefox用户效果、正式参数待定与下游NOT_RUN边界。请技术复核与用户验收分别记录所审commit和范围；不能把本申请当成已验收，不自动启用S02。
