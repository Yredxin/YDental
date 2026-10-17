[CODEX] S10-P0-22 已提交来源续补与阶段退出预检

唯一正式授权6230134070和P021正式裁定6230102263全文REST读取，P021已提交子证据继承、整体BLOCKED不改判，不重新治疗/发药/出账或重收已验证资金，不重做P020 A。当前#23/#34正文与P021保存正文逐字相同，全部有效评论3/260已完整API读取/保存；原253条逐字相等，新增为P021四冻结、交付、正式裁定及本授权。#35 OPEN/0，Issue/Project0修改。本批无已有CODEX预检/交付或本地运行记录；origin正确，原分支codex/s10-settlement-finance-r1-20261013，本地/远端起点f58d92046e14c77834a3ff12351a0010834e2da8，起始树干净，core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。

本批产品0修改，沿用be1d12a2d21771ca411ca8bdd510437980b68ef3内容。只新增8份P022脚本，实际测试提交219df2a8161f217abb2aa20cc446ffd2c68cd868；原P021347文件及引用私有提交marker/尾审/原件数据与固定索引SHA全部核对。已检查所有新增脚本compile/symtable全局引用、真实catalog字段与数据交接、原生slot返回实际没有version而由真实记录取发布版本；不再硬编码旧500或不存在的catalog单位字段。文书四动作完整正例、金额/患者/锁+2/错误actor反例及实际persist先存后拒绝纯文件检查均exit0，数据库/CREATE/Odoo/HTTP/Firefox仍0。准备中只做文件检查；旧脚本和旧报告未修改或执行。

执行冻结 `docs/evidence/s10-p0-22/initial-freeze.json` SHA256 **ff131b9731247e8a6d579de7b0e7a44cc4175cc901242ac12669dea28dbd3b47**，绑定当前实际HEAD、8脚本、所有YDental产品及实际引用core/旧证据/私有源输入共445份文件SHA。SQL字面合同及字段/动作合同另存本批证据。私有拟用配置SHA256 **1e652665d288192697d7982b06e56da64acb7d213ffdb1eea9b929e5ffc3a47a** 已离线生成，凭据不公开。正文REST GET逐字全等并保存后才允许以下操作；不另问用户启动。

唯一源为授权例外P021 `ydental_s10_test_20261017050000_21b0cafe` / OID2122140 / cluster7694897083368259627。只开复制前及最终各1条严格READ ONLY/REPEATABLE READ，显式ROLLBACK/CLOSE；比较保存的P021645实际物理表/schema/每个stored列、身份权限、原件/附件及filestore。源表或文件漂移立即STOP。源连接内检查其他活动/闲置连接，关闭源连接后、维护autocommit会话内再查一次源连接数，必须0；不终止其他连接。不给源启动任何Odoo/HTTP，不在源修改权限、文书或经济事实。

维护连接1、CREATE1，仅 `CREATE DATABASE` 从上述固定TEMPLATE复制。新名 **ydental_s10_test_20261017060000_22b0cafe**，尾码22b0cafe为P022标识，满足既存S10严格14位时间+8位hex guard，不使用破坏guard的字母p。端口18323，独立同名.local目录、data_dir/odoo.conf/一次性database.json；先不存在，后新OID不在旧catalog并绑定cluster/core/配置SHA。filestore copy2真实复制，无软/硬链接、无共享回写，逐文件内容SHA和inode独立校验。源filestore还须与已采P021私有索引全等。副本所有645表初始每列、物理来源/关系行及原件文件与源完全相同才可普通业务。其他旧库/W5/P013/14/18/19/P020 A/B均0连接，旧配置/证据/卷保全。

完整快照使用实际PG catalog列和类型，tableoid/regclass+ID或完整关系tuple，保留同号异表/重复key；所有645物理表和所有stored列均读，不再用只选部分表的视图掩盖锁副作用。stored金额/余额/币种精度、源/患者/公司/门店/价版、原生借贷/核销/库存批次/状态全部保留、Decimal精确比较；显式文书/account/stock展示字段另列，不作经济门禁。每个关键动作flush，先fsync私有before/after/full-diff和公开逐表/行/列完整脱敏索引，再运行断言。每个正常自有cursor检查点记录pending/COMMIT intent/returned，独立新RO/RR全量读回精确核对后才发布成功marker。资金结果未知不重交；提交后native rank只允许事前捕获的确切partner/field/delta/actor与技术时间，native cache逐条append另记，不能豁免金额或整个partner表。

每个native进程先在副本只读核身份、实际已加载9个关键函数的文件来源和code对象等于固定源码新编译结果，防错误addon来源；该检查不运行旧P021场景、不把异常源码当可修的资金结果。只有副本允许正常Registry/普通ORM服务，业务lambda仍合法普通角色；配置/核验uid1只作读投影/必要已有合成配置，不执行业务，不调用执行器sudo。

五组精确安排：

|组|来源、角色与动作|门禁和证据|
|---|---|---|
|A|副本真实marker patient1/execution1/doc1/invoice1/original1，沿每个外键/四费用而非猜ID。doc必须pending/v2无有效editor。原责任人user7建立合法新绑定，acquire1/confirm1/correct1/release1，分别合法提交并独立读回；confirm→v3，纯文字correct→v4，释放editor。|固定cl._operate→queue._locks→intake._all_locks继承链：patient/supply/intake/queue四个mutex，XML固定record1且仅revision各+1/动作，其他列不变；文书仅相应editor/session/CAS/content/saved/state/技术actor时间；confirm/correct各新增1条不可变版本/previous/template/author正确及对应S01审计。所有经济stored事实及旧原件/附件全等。原责任人不是配置管理员。|
|A Web|上述提交后经理user5在真实Firefox工作台点击既存v1链接1次；升级后再点击1次。reader8有效read+export时真实点击1次，撤export后下个GET拒绝1次。|总原件GET4/轮，生成0、GET渲染0。v1 SHA固定05928780e7d97a06cf29019634f64b010eb4994c2f1c5032d561008a50b059b4，v1/v2旧记录/附件/字节完全保全。不是当前动态PDF、不是另患者或新文件代替。|
|B|真实marker首付款350及对应源600、settlement.pay审计；普通经理user5分别对三对象write/unlink共6项。|每项MODEL调用，不冒称RPC；失败后完整字段和行集全等，0收款、0重复原件19项。|
|C MODEL/夹具|真实现存跨公司target store/company/manager从trade marker读取，回滚夹具内合法补export以确保测试到实际源公司隔离。错患者使用现存patient2，同公司混店使用现存store3，受控投影给固定服务守卫测试；不修改任何posted原单/旧原件。合法别名用正常患者create/request_merge/confirm在回滚夹具内形成真实family，再投影历史alias源作同SHA正例。|模型、受控异常源、正常alias merge各层明确标识；不称替身是已提交原生财务。每例内外完整差异先存，整个夹具回滚后所有物理表精确恢复；既有错误ID均真实存在，非不存在ID。失败返回任何未授权原件字节立即安全STOP。|
|C HTTP/RPC|一个Firefox内经理user5、reader8、真正匿名共3上下文（≤4）。经理/匿名分别测试content?download=true、image、image?download=true各无token/有效limited raw token，共12个真实响应。两类模型original/attachment的真实read RPC ×经理/匿名共4个；升级后追加有效token content和attachment read RPC各1。reader授权→真实取回→合法经理撤export→下个GET403，0普通账号提管理员。|每次真实body、MIME、字节数、SHA、headers、请求/响应/拒绝日志私有保存后判断，公开脱敏摘要。200图片必须实际PNG解码像素/尺寸与固定core placeholder经原生image_process变换结果完全相同且无PDF/原件/base64内容；不单放状态码。download/content及泄漏拒绝。token由固定core limited_field_access_token(scope=binary,raw)构造并用verify验证True，不修改access_token，不公开token；实际带有效签名网络测试在保护分支之前拒绝。P0216078缺体永久不追补。|
|D|唯一新P022-T05来源，正常上游新患者/目录6价/供给资格/执行1、费用6一笔、账单6一笔、收款6一笔、退款申请2一笔，复制来的所有经济行不变。合法doctor7执行、manager5出账/收6/请求2、不同user6审批。正常refund_uncertain failed→独立核无付款贷项→user6 verified_not_paid恢复approved，分别提交读回。|新金额/记录上限全批一次，不重建旧740或旧文书链。failed是实际业务API状态，不把网络失败标业务failed。所有关键事件/出账/收款/退款申请/批准/失败/恢复有完整前后字段差异；从真实返回值绑定event/fee/task/document IDs。|
|D 丢响应|仅新退款2的真实HTTP refund_execute POST1，稳定key/源由已提交marker保存。唯一一次route.fetch观察到服务端完整响应后丢给客户端的响应，客户端记录unknown，不宣称未付。先严格独立RO全量查证唯一done退款/native payment/posted move/贷项/operation receipt，再允许一次完全同key同payload POST。|完整差异先存再查断言；已确定提交后才同键幂等请求，不是盲退。第二次必须already_accepted且无第二经济事件，仅固定settlement mutex +1；未知资金立即STOP。新退款可从真实页面下载当前refund PDF1次（render≤2，只限新源）。|
|E|所有上述已提交业务/文书/原件上正常S10-only upgrade1，命令只-u ydental_settlement、不全模块升级，不重跑原经济链。|浏览器完成C/D后进入无请求等待，专属HTTP不接新业务；原生独立进程升级，前后各独立RO/RR全表及schema保存后判。全部业务/临床/库存/权限/原件/旧附件精确保全；元数据仅既存ir_model/fields/data/view/actions等的write_uid/date，目标view按固定源码派生arch_prev，目标module技术时间；每个真实physical record/field逐用途说明。cache仅id/date新行每表≤4，不豁免整表或同号子表。任何语义变化未解释即FAIL。原HTTP进程正常registry signaling重载后，真实v1链接同SHA及实际RPC/token拒绝回归；没有第二个Web服务或重新付款。|

预算：源RO严格2、独立RO总≤24（含源），维护1/CREATE1；配置池8/workers0/cron0/exactdbfilter/list_dbFalse，仅副本Odoo/HTTP，允许正常postgres目录读取。native进程初次A/B/C/T05-setup/T05-recover/prepare/revoke各1及upgrade1，共8；每场景420s、upgrade480s，HTTP ready60s、Web窗口1200s，浏览器只在受控等待阶段等检查点。控制器日志记录实际PID、每次backend创建/DSN/池峰值，累计不与池容量混淆，逐PID没标DSN则UNKNOWN。实时intent/派发/响应/失败/取消、commit均fsync。

每轮自有HTTP1/Firefox1/context3≤4，全部HTTP≤600（含redirect GET/资产/真实RPC/API负向/wkhtml请求）；原件GET≤4、生成0；T05真实退款execute首次1+查明后同键重复1；新退款PDF render计划1≤2。复制资金经济动作0；新增持久经济上限为fee1=6、out_invoice1=6、receipt1=6、refund request1=2、实际退款1=2，原生新增付款in/out各1、账务moves≤4；库存moves新增0。新患者持久1，另alias1仅rollback；目录/价/映射/供给slot各1、临床执行/文书各1仅T05；旧doc1四动作只有文字。新增S01审计≤400，grant只读者8本店read+export再撤export，跨公司41export变更仅rollback，旧源权限始终不动；无普通账号管理员提权。

执行顺序：纯文件已完成→本条REST逐字读回→`s10_p0_22_control.py create`（含源前读及副本初始全等）→A/B/C/T05-setup/T05-recover/prepare→`s10_p0_22_web.py`（真实UI/HTTP/RPC、合法撤权检查点、丢响应核实、原生S10-only升级及升级后入口）→final-tail→source-final（第二且最后源RO，表/schema/文件前后全等）→纯离线封存/逐页目视/22行新增层。全部Python使用既存../.venv/bin/python与PYTHONDONTWRITEBYTECODE，PYTHONPATH只既存.local/s04-deps；不安装环境依赖、不运行旧runner/Odoo shell、无executor SQL业务DML。

最多首轮+2轮同范围定向修复。每轮先固定新版本/文件SHA、增量预检并REST逐字读回，完整旧失败/冻结保留；仅在已提交及回滚均独立核清后继续未执行步骤，不重交已验证经济，不另换库。真实未解释经济变化、未授权文件返回、身份漂移/损坏风险或SIGSEGV立即停后续业务，保全并只读尾审；不能用修复额度强闯。一次CREATE/升级与T05经济额度全批不重复累加，工具比较器的已知错误只能重评保存的完整证据/合法剩余步骤，不能事后放旧合同或盲重试。

所有原始全值/病历/HTML/响应体/headers/凭据/token仅0700私有目录，Git仅新增本批允许路径中的脚本/报告/脱敏索引及核合成后可公开样本。所有旧库/证据/源码保留，S01—S09/core/AGENTS0修改，Issue/Project状态0修改，无sudo/OS/PG/Docker/防火墙/IPv6专项、不碰odoo-12。只关闭本批PID/config，不清理/删库或force-push。回滚以正常新提交撤候选代码为原则，本批产品不改；已提交合成交易/文书/原件永不以回滚清除历史。

完成或BLOCKED均线性固定提交推送，P021原22行历史逐行完整保留，仅新增本批五组和实际层级/角色/差异/升级/来源血缘/预算/退出码/未运行。给5—10步实际效果入口及是否满足S10阶段技术退出，旧已采子证据只按原来源/版本复用，不新造无关门槛。#34正式交付或具体BLOCKED回执REST GET全文逐字相等留存后立即STOP，等待GPT独立裁定，不自启P023/S11、不改Issue/Project、合并或部署。
