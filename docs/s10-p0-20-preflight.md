[CODEX] S10-P0-20 收尾退出表与执行预检

唯一正式授权6228862519；P0-19裁定6228828303已读并保留原BLOCKED，仅复用已限定采纳的元数据子证据，不重跑旧窗口。仓库Yredxin/YDental，目录/home/redxin/code/odoo/odoo-sd/code/sd-addons，原分支codex/s10-settlement-finance-r1-20261013。唯一父/执行产品HEAD a2fa26e37d350910668742869764c9ed102641ca；core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb；origin正确，本地/远端一致，起始工作树干净。

完整API读取#23正文/3评论、#34正文/248评论，旧244评论与上批保存正文全部逐字一致，后4条为P019预检/交付/裁定和本授权。#35/#36/#37均OPEN且正文说明未启动；本批仅唯一授权，没有既有预检/交付，本地未见同批运行进程。当前完整正文保留私有，脱敏逐评论SHA索引见github-start-index.json。已准备新文件均属许可路径，数据库/CREATE/Odoo/HTTP/Firefox/PDF实际预算仍0。先本评论REST GET逐字核对落盘，再同批执行A/B/C，不再申请开工。

一、有限退出表（旧22行历史状态原字节不改）
初始退出表docs/s10-p0-20-exit-table-initial.md与docs/evidence/s10-p0-20/exit-table-initial.json保存各行现行正文原文、完整GAP-03原行/历史出处及版本、原剩余缺口原文、最低补测、责任阶段和退出阻断。下表不是PASS。P016仅资格只读；P017仅当前产品静态；P018失败；P019仅物理元数据子证据，不能作真实UI/PDF证明。当前服务48个方法与R3固定f24b030的AST相同，仅_workbench变化，兼容性文件固定实际方法名；历史证据仅按实际来源/场景复用，不拼跨库完整链。

|行|现行需求原文|最低补测/仍缺断言|责任/退出阻断|
|---|---|---|---|
|F1|S10-F1（独立合成数据）：治疗600+检查80+发药6×10=740，出账740→实收500欠240→补240结清。重复请求不再收款/出账。|复用W3/W5原生740/核销子证据；B新源350+390及幂等，不重收旧500+240。|S10 / 是（补测前）；不自行免测|
|F2|S10-F2：已收740→申请退100→他人批准，在途100/实退0→确认真实退100，累计已退100/净收640。拒绝另一申请须原因且不产生退款。|B新申请100/异人批准/实际执行、驳回50、unknown80核实未付撤销；原额度并发证据按未改财务代码范围复用。|S10 / 是（补测前）；不自行免测|
|F3|S10-F3：实际微信录成现金且已日结→财务审批解锁留原因→更正登记→再日结，没有真实资金往返；实物退药另进待核查。|B新日期/渠道日结解锁更正再结；尾审原凭证及零伪退款。|S10 / 是（补测前）；不自行免测|
|F4|S10-F4：真实诊疗/检查/发药、批次扣减→结算→补旧文书/重印票据，费库款不再变化，调价也不改原已确认费用。|B新同患者治疗/检查/药房真实链、结清后原责任人confirm及文字correct、PDF不变经济；实物退回另核同原药事件。历史原版仍缺。|S10 / 是（补测前）；不自行免测|
|F5|S10-F5（另一个独立场景）：旧账270、新账200，均选中，实收300→先核旧270，再核新30→旧账0、新账欠170，保留两张账单和一笔300收款。仅选新账时不得擅自核旧账。|复用原270+200原生核销子证据；B新同源多账选中/未选+实际普通前台Web支付。|S10 / 是（补测前）；不自行免测|
|F6|S10-F6：前台小李有A结算权可从前台收款，无结算权者只能看到获准摘要。B看到A欠270仅只读；不能在B收A款，A权限且上下文合法时到A处理。|B普通前台工作台及新付款；六岗位真实服务拒绝、跨店/公司/附件原测试范围复用或列缺。|S10 / 是（补测前）；不自行免测|
|T01|740重复/并发出账；来源有效出账一次|复用原源唯一/幂等与独立双事务证据；B新源bill重试不增来源。|S10 / 是（补测前）；不自行免测|
|T02|740收500补240及重试；应收240→0，原生核销和实收一致|旧500/240只复用；B新350/390真实原生partials及同key重放。|S10 / 是（补测前）；不自行免测|
|T03|负/超额折扣、明确免单；非法拒绝，原因齐，零账无假收款|B新负/超额折扣拒绝、零额posted但无资金。|S10 / 是（补测前）；不自行免测|
|T04|退款自批与并发批准；自批拒绝，在途+已退不超允许额|B新请求自批拒绝；原独立审批/额度竞争子证据复用，未验HTTP丢响应仍列缺。|S10 / 是（补测前）；不自行免测|
|T05|退款失败/未知/实际完成/重试；不伪已退、不重复资金记录|B新unknown核实、取消释放、实际执行；未知平台真实性不当合成门槛，HTTP未知后重放证据仍保留缺口。|S10 / 是（补测前）；不自行免测|
|T06|未收款减免；只调应收，不记实退|B新未收款waive，仅贷项与应收，无现金退款。|S10 / 是（补测前）；不自行免测|
|T07|日结后改支付方式；财务解锁/原因/再确认，无伪退款|B新cash→wechat真实原生更正凭证、解锁重结，无资金往返。|S10 / 是（补测前）；不自行免测|
|T08|已出账数量更正、文字更正和实物退回；反向来源正确，文字不动费库，未退不回库|B新数量correct关联原费+贷项、纯文字经济签名全等、同原药event真实退回quarantine且不增领量不减费款。|S10 / 是（补测前）；不自行免测|
|T09|同法人调拨与跨法人交易；实际收发/凭证对应、公司店铺隔离|B全新原生同公司move及跨法人sale/purchase/invoice/bill/lot链；不重跑旧R3链。|S10 / 是（补测前）；不自行免测|
|T10|他店代收/无权医疗全文或票据；越权拒绝，摘要与全文分离|B六岗位服务board/pdf/pay拒绝；他店摘要/附件原生矩阵未覆盖项保留。|S10 / 是（补测前）；不自行免测|
|T11|中文票据及部分收退款；实收/欠款/在途/已退准确，法人门店正确|A真实页面一次paid740/0中文PDF，B新当前bill/receipt/refund及原状态PDF子证据；不称历史原版/多页全通过。|S10 / 是（补测前）；不自行免测|
|T12|安装升级及F4真实全链；事件、价格、批次、费账款一一对应|B正常install/S10-only upgrade，真实S08/S09/库存/费/账/款/文书同源链；A完成真实UI；仍缺原版不由当前PDF代替。|S10 / 是（补测前）；不自行免测|
|T13|F5旧270新200收300及仅选新账；核销270+30、欠170，未合并账单；未选不核|B新多账日期/稳定ID/仅新账核销，原账不合并；普通前台Web实际付款。|S10 / 是（补测前）；不自行免测|
|T14|F6前台有/无billing权及跨店摘要；同一结算服务鉴权，无按岗位默认放开，无跨店代收|B前台有权Web和六岗位无权服务；跨店摘要原限定证据。|S10 / 是（补测前）；不自行免测|
|T15|已确认600调价620后结算/重印；退款驳回；仍取600快照；驳回原因和审计齐、不生贷项/退款|B已确认600后发布620仍按600出账，confirm/correct/PDF签名全等，驳回无贷项/退款及审计；历史原版存取产品缺口仍BLOCKED待GPT裁定。|S10 / 是（补测前）；不自行免测|
|T16|日结锁后补录、解锁更正、删除/篡改审计；锁覆盖新增/更正，合法补录双时间可查，单据日志不可普通删改|B新跨日补录双时间、锁/解锁/再结、单据/审计普通write/unlink拒绝；旧事实不删改。|S10 / 是（补测前）；不自行免测|

S12完整正式快照、S13美化/50会话/持续备份/统一用户验收与生产审批分别保留；它们不扩成当前测试前置。明确TC里的原版重印没有同源原件，也没有当前S10原版取回接口，不能免测或用重新渲染冒充，最终交GPT裁定。

工具缺陷：原生累计连接≠池容量、正常postgres目录读取、finally-only请求账本。新增执行器修正，旧失败永久保留。

二、真实依赖、允许文件与三组新B场景
当前不计划修改产品。实际新增scripts/s10_p0_20_*.py（A合同/控制/metadata/browser/preflight，B原生加载/12场景/普通账号Web/自有服务、无executor sudo的合成fixture和退出表生成器）、docs/s10-p0-20-*.md与docs/evidence/s10-p0-20/*。若在最多两轮定向修复内确认S10产品缺陷，只能在ydental_settlement/**最小修正，先发布增量冻结实际commit/受影响文件/脚本SHA/场景，保留旧失败；不改ACL、不放开权限、不改S01—S09/core/旧脚本报告证据/AGENTS。现有ydental_settlement_test仅为B安装已有demo供给适配器，其原guard/源码不改，名称与marker符合原guard；业务仍走真实容量/医疗/药房/库存/结算服务。

A=ydental_s10_p020_20261017040000_20a0cafe，端口18320，独立.local同名目录/config/data_dir，CREATE前不存在；W5 OID2100310/cluster7694897083368259627只在前/最终各1严格RO/RR来源连接，643表/schema/物理继承族及config/marker/152文件封存核对，rollback/close，前连接关闭后才CREATE。独立显式维护连接1/CREATE1、copy2实际filestore，不硬链接共享；新OID不在旧catalog，marker绑定。A副本独立RO/RR审计3（前、metadata后、最终）；原生convert_file固定views/ydental_settlement_templates.xml一次、metadata commit1，先保存完整私有before/after/full diff及完整脱敏变化索引再门禁/commit，独立后核。沿用已审action571物理ir_act_url→ir_actions共享投影和五XMLID/对象逐列条件，无整表免检。

A原生HTTP1/Firefox1，user5既有密码/公司/员工/权限不改；login GET1/POST1、工作台GET2（登录redirect默认1+患者1真实筛选1）、真实页面“下载当前内部账单 PDF”点击1/GET1/render1/download1。验证posted/out_invoice/paid/740/residual0及患者/门店/公司/真实费源、旧未结清勾选不包含invoice1。PDF最多10MB/20页，中文实际text+逐页raster目视；响应SHA=文件SHA=report_download审计SHA。不声称实机出纸、真实多页或历史原版。
A非经济：login/login.scope/store.switch各1、invoice_view2、report_download1；原生session/device/userlog各1，身份指定五记录仅技术uid5/time（hr_version另last_modified），default信号最多1；旧行全部不变。资产最多12新附件，严格/web/assets/原生frontend minimal/lazy js/css/iconwoff2用途、MIME、5MB上限、字段与文件checksum，不包含患者/报告附件；静态GET100/translations1/wkhtml资源0。A经济、临床、权限业务写0，旧500+240/refund14/close9及负向/refund13分页/doc确认不重放。

B=ydental_s10_test_20261017040000_20b0cafe，端口18321，独立.local同名目录/config/data_dir；第二次独立显式维护连接1/CREATE1，template0全新正常安装l10n_cn,ydental_settlement_test（真实依赖含account/sale_stock/purchase_stock/ydental_exam/ydental_print及上游），--without-demo=all，en_US/zh_CN。原生正常chart模板演示映射、合成员工/门店/患者/价目/真实库存来源允许；fixture uid1只准备新主数据，实际业务均with_user合法普通账号绑定真实门店session/connection，无executor sudo、SQL伪posted/done或绕服务鉴权。B来源与W5家族独立，不能按相同数字ID拼链。
B三组具体脚本场景：
1）f1_740全新S08/S09/药房4+2及740真实出账，新收350+390（不是旧W5500+240），核原生partials；f5_270_200新多账选择/日期/稳定ID与仅选新账；f2_f3_refund_close新退款100他人审批/实际执行、拒50、unknown80核实未付撤销；discount_waive负超折扣/80免应收/零账无假款；idempotency原新源重复bill、同key pay5与冲突key不重复。历史双连接竞争仅按不变方法/已测范围复用，缺失HTTP响应丢失实证继续列缺，不用文字宣布全覆盖。
2）f2_f3中的新日结锁→异人解锁→cash改wechat→再结原生更正，无伪资金往返；late_close跨日双时间/锁/合法解锁补录/再结；security_matrix六岗位board/pdf/pay鉴权，普通前台新B Firefox真实一笔alipay3；audit_integrity普通单据日志write/unlink拒绝；t09_trade+same_company_transfer全新真实原生调拨及跨法人sale/purchase/posted账单/批次链。新演示配置不等于生产财务批准。
3）同一B新patient的治疗600/检查80/药40+20真实事件→快照→费→账→款链，执行后发布620，原账仍600；结清后原责任人acquire/confirm/纯文字correct/release，各次签名证明费库款不变；真实当前PDF另核不变。quantity_correction独立新治疗数量-1生成原价反向费/贷项、应收减免而无现金退款；drug_return引用本B同原药event，真实退1至quarantine，不自动减费/退钱/再领量。原版历史PDF无同源原件/取回接口，仍明确BLOCKED提交GPT，不擅自免测推S12或用新渲染冒充原版。

三、连接/请求/事务预算与具体命令
池db_maxconn8/workers0/cron0，原生累计backend创建全记录，不设累计<=池容量；固定core正常postgres/db_system目录只读允许，DSN如实记录，逐PID无法归属标UNKNOWN。明确新db_name/dbfilter/list_db=False，禁止任何受保护旧业务库连接。源前/最终各1；A维护1+审计3；B维护1；native按各进程pool<=8分列，不把维护连接冒称全部catalog。保护OID2100325/2100326/2100327/2100330及全部旧失败环境不连接/复用/删除。

纯文件：PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.local/s04-deps ../.venv/bin/python scripts/s10_p0_20_preflight.py，exit0，33项实际共享比较器/事务fixture检查（同号异物理表、parent/child、ONLY自有、失败全差异/commit门禁等）及3项工程检查=36；不是SQL或Web实测。初次准备后改B普通Web凭据映射/自有服务，全部脚本AST再次compile成功，最终SHA冻结，无运行动作。SQL-contract.json保存原643条逐列SELECT、身份/catalog/继承3条/维护CREATE合同；source每连接显式SQL<=651、A审计<=650、statement15s/lock3s/快照150s。B全量动态schema逐表SELECT只取新B，native明细服务SQL另列。

执行（均使用../.venv/bin/python及.freeze中的完整argv）：
- scripts/s10_p0_20_control.py：A源前→CREATE→metadata120s→HTTP就绪60s→Firefox150s→自有进程停止→A尾审；成功后暂缓唯一源后到B结束，若致命停止则立刻源后。
- scripts/s10_p0_20_b_control.py create；install（480s）；依序f1_740/f5_270_200/f2_f3_refund_close/discount_waive/quantity_correction/drug_return/t09_trade/same_company_transfer/audit_integrity/security_matrix/idempotency/late_close（各180s）。B scenario进程最多12，正常install1、S10-only upgrade1、审计进程2，每进程pool8，原生累计完整留证；单次脚本内部业务请求有稳定key，不无限循环提交。
- scripts/s10_p0_20_b_web.py：B专属服务1/Firefox上下文1（就绪60s/browser180s），普通前台login GET1/POST1、workbenchGET2、真实付款POST1、静态GET100；上界合计允许3角色会话/login3/workbench6/业务POST3/static300，当前只计划1角色。B _pdf实际调用最多8（当前计划4），新staff<=100/store<=30/patient<=20/fee<=50/payment<=20/refund<=10/stockmove<=100/S01审计<=5000，均须按来源/用户/实际方法核对，非整表豁免。
- B snapshot-before-upgrade→upgrade仅ydental_settlement（480s）→snapshot-after-upgrade（180s）：升级前后全量快照/全差异在断言前保存，原经济/临床/权限/旧主数据逐行全等；安装/升级必要metadata按真实对象用途留证，不做全表豁免。
- scripts/s10_p0_20_control.py source-final：B完成/停止后最后唯一W5 RO/RR，643/继承族/152源文件不变。

请求intent/request/dispatch/response/failure/cancel/stop/close同步jsonl+flush/fsync，脱敏不写密码/cookie/CSRF/SID。停止先关新业务入口、留在途状态、尽量正常关浏览器，再独立尾审。失败与UNKNOWN不靠finally内存补造请求；未知付款/退款/PDF先核验，绝不盲重试/再点。

四、有限修复、停止与回滚
首轮+最多两轮相同范围工具或明确S10产品缺陷定向修复，先固定实际commit/脚本/场景和预检增量，旧证据保留，回归业务用新来源标识不覆盖已提交失败。身份/权限边界、不明经济结果、不可逆损失、Native SIGSEGV或范围外依赖立即STOP，只剩余只读尾审封存；不把授权当无界重跑。任何未知经济提交不得重复，A PDF已取得或未知不再次点击。自有进程按PID/config停止，旧库/日志/文件全部保留；不DROP/reset/clean/强推或逆向SQL删账。产品回滚须后续正常revert已识别产品提交；当前无产品改动，无需撤回账务事实。

冻结execution-freeze.json SHA256：91c02df09041a053cd8c4e3d27f29da045a523f2d880113d50f78a7cefeb84ca
逐脚本SHA256：
- scripts/s10_p0_20_b_audit_integrity.py: b7704bc24e63726095b146330595ef0dfd3fbdaf3d2bd715c945e92f14f91074
- scripts/s10_p0_20_b_browser.py: 13c0792ec3903bf2b7c70f08a14bc814b12d58350f24cb54b40921528047f6df
- scripts/s10_p0_20_b_control.py: f40970d5c210d684ba9749344c804e79d6a907efb8255512473a90c2b48c8211
- scripts/s10_p0_20_b_discount_waive.py: 76a9910ddc142ec8f5081b02abeca4e6567e60e68d0d67dbe0822f8c3e672e63
- scripts/s10_p0_20_b_drug_return.py: 7b289e49c47b9403c35d634962cfc0579f990c08f4f02463435c80b7374fe80d
- scripts/s10_p0_20_b_f1_740.py: cc46764544c9db5051ff1a840e26ff3cac6a9bfd4d8b5910ba3fee2ea21f8b0d
- scripts/s10_p0_20_b_f2_f3_refund_close.py: 5cb06f0747f06f2f57a0071d25348ae8f602cb01da5267ae8e8a826ec73c7ad9
- scripts/s10_p0_20_b_f5_270_200.py: c6f82ebd5816046ea85cea3f15f7e119c48bcebc0d0ba411dd9d6a066fc4a862
- scripts/s10_p0_20_b_idempotency.py: eeca03b28db88c55a385af4cef0fc0803aa985371174d5bee609b76bc5186d9d
- scripts/s10_p0_20_b_late_close.py: a881881e106807fc9775550e14e8d4edd20119b9296b7d5d13d971a3c16450d2
- scripts/s10_p0_20_b_native.py: c14a0a5ab3f1ee1635953053e9fda2cbcbc122c9269550d5a9ae438e42b9f298
- scripts/s10_p0_20_b_quantity_correction.py: 2329a4e8ad9a870026ab3dd4fc039c70095a3ce8293e0cc01a731ea5b4d50b23
- scripts/s10_p0_20_b_same_company_transfer.py: ad0561af789be92ab747e1820a43bc848d5343589fa038490d9697f2e43ea029
- scripts/s10_p0_20_b_security_matrix.py: a7ab6b4981d41aaa77623ed433a2f0f207844d42e7e2d63d1ac9afdcc5a87dad
- scripts/s10_p0_20_b_t09_trade.py: 32e84ff84e629d67ab60d2932f05a5cd8c2c86ecafa9172dec239b3e7f18deea
- scripts/s10_p0_20_b_web.py: 1a48b44abdd5b79b65270d7f8a124a0262bd6f67b72e8d3bf134f8ffa1acc641
- scripts/s10_p0_20_browser.py: a554f23a0f6a9279ad99f63cb0fbc16eaaebd2bce89526175be6184cad10fc02
- scripts/s10_p0_20_contract.py: a7ae80f34a46a1e8376c851a346ffb4cc0193ff9014bf40fdcb6a23b4db1f92e
- scripts/s10_p0_20_control.py: fbe2b884ad398a94862072ddd6848a37ab566637780f55947cac9013da80c15c
- scripts/s10_p0_20_exit_table.py: 2cf47a33ce8406b8d27e0734ec5fff3d7f2f9974686a3ff91fe7842081fa9482
- scripts/s10_p0_20_fixture.py: e4d2a1c522c5dac803577c7b85492aa9afb0716e8ce1000c9b4f2485b9f63344
- scripts/s10_p0_20_metadata.py: f6d25f3af417e24471ca75eb7c30073d8ea55d187c734ae365f44f7ddf3536f9
- scripts/s10_p0_20_preflight.py: 04fd871744408ffb935ede9c1398647213b1d51b9594d47d8967095d3b19735a

最终新增退出表与报告必须逐行列真实结果、版本/来源/剩余最小动作，固定产品commit（无变化则本基线）及证据commit、逐文件SHA、原生退出码/普通账号Web/账务库存血缘、失败修复轨迹及5—10步用户效果。当前原版重印、完整附件/原生RPC/HTTP未知响应等未获证据项继续按实际NOT_RUN/BLOCKED，不用分组掩盖。只可申请S10阶段独立技术复核或交具体功能/缺证BLOCKED，不自称整个S10通过。S12/S13和生产政策另列。正式回执REST GET逐字相等并保存后立即STOP，等待GPT；Issue/Project状态、S11/合并/部署0。
