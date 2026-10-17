[CODEX] S10-P0-21 B收尾与内部账单原件最小补齐预检

唯一正式授权6229311739，P020裁定6229289071已完整读取：A限定采纳且本批0重做；P020整体/B历史BLOCKED及瞬时根因UNKNOWN不改。唯一父HEAD 7a4bdb93cb4a2d625f01df7eb0ac41d76c5e0e46；仓库Yredxin/YDental、原分支codex/s10-settlement-finance-r1-20261013、目录/home/redxin/code/odoo/odoo-sd/code/sd-addons、origin和本地/远端HEAD匹配，起始工作树干净。core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb。完整API读取#23正文/3评论、#34正文/253评论；旧248条与P020保存正文逐字相同，新增5条为P020预检/R1/交付/裁定及本授权。#35—37 OPEN/0，未启动。仅本批授权，无已有预检/交付或本地并行执行。实际引用P020脚本/退出表Git对象及SHA均核，未运行旧测试。

REST GET本正文逐字全等并保存前：产品修改、DB/CREATE/Odoo/HTTP/Firefox全部0。门禁后同批连续实施，不逐动作另请用户启用。

一、实际源码范围和原件合同
只改7份冻结产品文件：新models/ydental_settlement_bill_original.py、models/ydental_settlement_original_service.py、models/ir_attachment_original.py（含ir.binary防原生limited-field token入口）、controllers/bill_original.py，models/__init__.py、controllers/__init__.py和views/ydental_settlement_templates.xml。既有收退款/日结/库存/当前_pdf/_report_payload均不改，旧ACL不放宽。新模型普通ACL为默认deny，不给所有内部用户原件全文；只经当前真实settlement read + export write源鉴权的私有服务初始化/读回。产品完整候选在私有proposed目录，本次拟写文件及SHA见proposed-product-contract.json，不在预检前修改addon。

ydental.settlement.bill.original字段：invoice/patient历史来源/store/company/currency/actor/generated_at/request_key/version/previous_id/source_facts/source_sha256/template_xmlid/template_sha256/pdf_sha256/attachment_id。actor+key与invoice+version分别唯一；初始化仅私有object token允许，attachment只初始化一次，旧记录任何write/unlink均拒。生成先核posted out_invoice和本店公司、全部来源fee/event同店/confirmed/币种与合法patient family、invoice partner历史身份。固定源事实保存账单金额/余额、完整fee源ID/价格版本/快照数量/单价/价源/原生借贷及partial ID和金额，模板固定XMLID及有效arch checksum。原生服务器生成后再次核源与模板不变，失败不留混合版本。

POST /ydental/settlement/bill-original/create/<invoice_id>：auth=user/CSRF、revision+幂等key+可选明确previous。首次生成留存，重复同key返回原记录不渲染；新版必须关联latest，不覆盖旧件。附件固定服务器bytes、application/pdf、private/public=False/access_token=False、res_model指向唯一原件、公司固定，非上传通道。窄范围内部创建与既有服务授权模式一致，不做通用sudo兜底；执行器sudo0。
GET /ydental/settlement/bill-original/<original_id>：每请求核当前源read/export、公司/门店/所有费源/患者family及原件身份，只校验已保存附件字节SHA并原样返回，方法中无_pdf/render调用。缺件/校验错明确拒，不重生成替代。新附件write/unlink及重挂拒；原生/content/image/RPC及limited field/access_token旁路一律拒此特殊res_model，合法下载只走受控原件端点。固定core ir_binary._find_record的limited token分支先于_can_return_content，本补丁在super之前拦截。现有“下载当前内部账单 PDF”保持原用途；新增明确“生成并留存内部账单原件”POST与已留存版本下载链接；不拿旧A字节伪造历史签发，不称税票/签署/出纸或平台到账。

二、稳定事实/展示字段与提交门禁
完整stored经济事实矩阵：actual PG catalog列/类型；全部account_*、stock_*、inventory/treatment/结算source-payment-refund-close-correction-trade及关系表、S05 price/snapshot、币种/精度/UOM。stored计算金额/余额也保留；to_jsonb数值按Decimal精确保留，不用汇总金额或epsilon删除细差。tableoid/regclass真实物理来源+稳定ID/关系行完整tuple作为键，同号异表不覆盖。技术mutex/receipt、文书/原件、身份权限和审计另分类，旧原件/附件/version/audit行不得覆盖/删除。源、患者、公司店、价版、数量、金额、借贷、核销、退款状态及库存批次/状态全部保留。

每个关键业务操作前后env.flush_all，完整经济/文书/身份/审计/附件存储行私有保存；另只读明确ORM display_name及选定M2O表示投影，不作为经济门禁。acquire/confirm/correct/release、当前PDF、原件生成/重取分别捕获；先保存两侧全值、逐表/行/列全差异及脱敏完整索引，再断言。展示差异单独保存，必须查对应字段与固定源码解释后才作工程结论；不倒推P020缺失瞬时差异。金额/ID/公司/价版反例及实际persist先存后拒绝路径纯文件测试已通过。

新脚本全面做symtable全局引用/导入/成功路径静态检查，旧execution未赋值确实被检测，新链从opened_actual真实execution/document/patient绑定。转换额外发现same_company_transfer检查点root未绑定并改为真实f.root。所有marker写入转成pending私有材料，不能提交前发布b-chain/b-multi/trade.json。
正常独立事务检查点：初始chart/features→诊疗/检查/药房/出账/收款主链→原件首次留存→文书四动作→原件重取/明确新版→各组退款/日结/更正等。每段先原生借贷平衡、source/fee/event公司店患者币种和原生单据、退款额度/终态、done库存move、原件附件checksum核验，再保存完整precommit/pending、实时commit intent/returned/unknown。独立新连接RO/RR读回所有stored行精确核对，仅原生信号逐条id/date append≤1/类型另记，成功后才发布交接JSON/marker；commit未知先只读核实，绝不重交资金。后续失败保留此前已核提交，不用末尾打印异常回滚全部。

纯文件13项检查exit0；包括上述稳定存储正反例、真实物理来源、展示分层、未定义变量/导入、全部新场景编译、提交marker路径、getter无渲染回退和固定API核对。不是原生SQL/业务PASS。此前纯离线准备的路径/变量假设错误已纠正，运行预算仍0。

三、唯一新库、预算与14场景
唯一新B ydental_s10_test_20261017050000_21b0cafe，端口18322，独立.local同名目录/odoo.conf/data_dir/marker；CREATE前不存在，新OID不在旧catalog并绑定cluster7694897083368259627。maintenance1/CREATE1，template0正常安装l10n_cn,ydental_settlement_test及既有原生依赖；初始管理员在任何普通业务fixture前明确正常chart和3既存feature（多仓库/多库位/pricelist），新业务角色grant与feature分列，不把负向测试人员提管理员。

所有旧业务连接/复用/写入0：尤其W5 2100310，2100325/26/27/30、P020 A2100333/B2100336，所有旧失败库/文件/卷保留。不读W5快照、不重做A登录/PDF/XML同步、不重放旧500+240/refund14/close9/旧权限负向/refund13分页/旧文书。

14个冻结新源场景（control.py SCENARIOS）分三组连续执行：
1 收支/防重：新真实600+80+药4+2=740，先发布620后旧600出账，独立新收350+390结清/partial2并提交读回；新270/200多账日期/ID顺序/仅选新账；退款新100异人批准/实际执行、拒50、unknown80核实未付撤销，容量与幂等；负超折扣/零额无假收款、未收款waive、同key pay/bill去重。既有兼容且未受新原件改动影响的双连接竞争子证据按原范围引用，不虚称本批并发已跑。
2 更正/隔离：新日期/渠道/收费员日结锁、异人解锁/现金改微信/再结无伪资金往返；合法跨日双时间/锁后补录；六岗位/源权限、普通审计及单据write/unlink；新同法人库存move与跨法人sale/purchase/posted凭证/批次；普通前台新B真实Firefox勾选一账并支付alipay3。无外部支付平台证明或生产税币种批准推论。
3 同源原件/票据：已提交主链同一patient/execution/document，由真实责任人acquire/confirm/纯文字correct/release逐步stored经济不变；首次bill原件留存后上述合法文书变化，重取同一字节SHA；明确新版另存。新数量更正子例关联原fee/价源/贷项只减应收、不伪退款；原主链药event真实退1进quarantine，不自动减费/退款/增领量。bill/receipt/refund当前状态PDF实际生成并检查；真实工作台POST留存下一原件版本、点击既存原件链接、原生附件/content/image负向，撤权旧service下一次请求拒绝、缺read/export/错店/RPC/不可删改。子例分别列真实来源，不把不同患者/版本拼一个全链。

正常install1/configure1、S10-only upgrade1、scenario process14、native audit process2；每native进程池max8、workers0/cron0/list_dbFalse/exactdbfilter。允许原生postgres目录只读，累计backend/占用/DSN完整记录，不把累计与池容量等同，逐PID没有DSN则UNKNOWN。独立RO/RR最多32（每已提交检查点+Web前/最终+必要停止尾审），只连接本批新库，真实catalog不猜表名；statement15s/lock3s/每snapshot150s。旧库审计0。
HTTP专属服务1/Firefox进程1/独立context2：login GET/POST各2、合法switchPOST2、settlementGET≤8；真实前台payPOST1、原件生成POST1/真实旧原件clickGET1、native附件负向GET2；全部HTTP≤350，所有intent/start/response/failure/cancel实时脱敏flush/fsync，阻断先停新动作留在途再正常关浏览器和尾审。新staff≤120/store≤30/patient≤25/fee≤80/payment≤30/refund≤20/move≤150/original≤5/PDF render≤12/S01audit≤10000，逐来源/状态留证，非表豁免。当前计划原生14场景+两个真实Web角色，必要正反例而非组合穷举。

具体命令均../.venv/bin/python、PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=.local/s04-deps：先s10_p0_21_apply_product.py仅写7候选文件→正常产品commit→新测试脚本独立commit。实际产品/测试commit及脚本/产品SHA形成runtime-freeze并REST读回固定，再s10_p0_21_control.py create/install/configure；顺序f1_740/document_original/f5_270_200/f2_f3_refund_close/discount_waive/quantity_correction/drug_return/t09_trade/same_company_transfer/audit_integrity/security_matrix/idempotency/late_close/original_security；s10_p0_21_web.py；audit-before-upgrade/upgrade/audit-after-upgrade；final-audit。install/upgrade480s、场景360s、HTTPready60s、browser240s。升级只ydental_settlement，带已提交业务前后全差异先保存再核经济/临床/权限/旧附件完全不变，新schema按真正模型来源，不强套旧643表。

四、22行退出及停止/封存
原P020最终退出表/历史22行原字节保留，新增本批层，逐行保留现行需求原文、历史证据/版本/库来源和剩余断言。初始本批均NOT_RUN，A仅历史限定采纳；结果按真实提交/独立读回/普通Web/原件SHA填入，不拿比较器、install或回滚中间输出替代全链。
|行|本批最低补齐分组|目前|
|---|---|---|
|F1|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|F2|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|F3|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|F4|组3：同源文书/价库款/原件与升级；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|F5|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|F6|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T01|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T02|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T03|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T04|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T05|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T06|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T07|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T08|组3：同源文书/价库款/原件与升级；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T09|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T10|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T11|组3：同源文书/价库款/原件与升级；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T12|组3：同源文书/价库款/原件与升级；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T13|组1：真实收支/选中核销/状态及防重；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T14|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T15|组3：同源文书/价库款/原件与升级；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|
|T16|组2：更正、隔离、审计与交易；兼容旧子证据只按原范围复用|P021 NOT_RUN，待真实提交证据|

首轮+最多2轮同范围定向修复：每轮先新增量预检固定commit/脚本SHA并逐字读回，保留旧合同/失败，回归仅新唯一来源。真实未知资金、不能解释的stored经济变化、身份/权限越界、Native SIGSEGV或范围外依赖立即STOP，不以额度强闯；完整字段证据保存，关闭新业务入口，只余只读尾审。commit未知不重交资金，已提交事实不删改；只停本批PID/config，不DROP/reset/clean/force-push，不sudo/OS PG Docker防火墙IPv6专项，不碰odoo-12/真实患者资金。原始全值快照/HTML/credential在权限700私有目录，脱敏SHA/逐列变化索引与确认合成PDF/截图才入Git。

最终固定产品/测试/证据SHA、逐文件SHA、失败修复轨迹、每组普通账号Web/原生事务、原件重取同SHA与权限负向、新库独立尾审、升级和5—10步效果及完整退出表；必须给出可申请S10阶段技术复核或具体阻断/最低动作。S12通用模板/税务原件/报表、S13美化/50会话/持续备份/最终统一用户验收、生产政策各自保留，不拿它们混作全部合成技术门槛。本批最小内部bill原件责任已明确实现，不再循环推迟。正式交付/BLOCKED在#34发布、REST逐字读回保存后立即STOP，等待GPT，不启P0-22/S11、不改Issue/Project状态/合并/部署。

初始冻结docs/evidence/s10-p0-21/initial-freeze.json SHA256 e58b97fc104ef02cc9739673eaf9420428302d6740960f257fe76150af1ce331
7份候选产品SHA：
- ydental_settlement/models/ydental_settlement_bill_original.py 7361b3a4717d94598ae55aa958176bcb27aedae29f7f8e2557dc46b4c89e7364
- ydental_settlement/models/ydental_settlement_original_service.py e579903e43a3464107fa35476a97a4520d1b9880724157181833a8a1a303c401
- ydental_settlement/models/ir_attachment_original.py ada928467b05099a5eb570e1e8f972eabe25f588dfbacee81b7c75985ce73864
- ydental_settlement/controllers/bill_original.py 0ab10e3048deb29d1cd7036fcc89b796f6d3f181f8330569d4e9e75c74bb1a17
- ydental_settlement/views/ydental_settlement_templates.xml b163a1bd3fad170d0f309b624fad216109e90642ca51f66ce5c372bdc0ee27fc
- ydental_settlement/models/__init__.py 0bbf3e7d893e1fbce3689ae54139e62465db485cd1bd854dc76d02e05a76919a
- ydental_settlement/controllers/__init__.py 0f8e8904c54459108cdd0f49a42a4bae19de57a08ade39ad33fad5b22825ef41
完整新脚本/引用core和证据SHA均在初始冻结file_sha256，运行前再绑定真实产品/测试commit。
