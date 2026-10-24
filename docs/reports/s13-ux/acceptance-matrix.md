# S13 UX 独立验收矩阵

本表为未实现者 `/root/acceptance` 的最终软件独立验收矩阵：UX-01—08、UX-F1—F5及UX-T01—21适用软件断言通过；UX-T22的代码/私有包/复现路径已独立核，远端同步与Issue状态由主控依据实际工具读回补记（见表末，不冒验收者执行远端写）。验收者未实现产品或测试工具；共享 OS 不构成隔离。私有原始证据和独立回执由 `evidence-index.md` 索引，公共仓库不含 PDF、截图、认证材料或原始请求。

被测产品为 `b9a9bd70cd918f11606a81bf8d26398d8df62c64`（布局7），产品及测试工具执行候选 `c5052e519cb8fc97bc41a2867ab7155cf11d3547`。普通 HTTP/浏览器后续候选 `a3409907ae4c5b6dd7f2aaf0a17d36c1999f8705` 与 c505 产品/工具净字节相同，仅 CURRENT 文档变化。c505 实际运行39方法，30 MODEL、7原生 HTTP、2明确标示的加工授权/编码替身；0失败、0错误、进程0、无 Native 信号。不能把框架内部55条统计称为55项业务方法。

最终界面英文源/PO候选 `d601bef157c5539875504ed217170eb31780cbc4`；执行工具候选 `e85ae5a700d2ec308ed07806c97745be40e4c341` 另修当前S13 baseline provider选择，产品字节同d601。最终限定access/followup/settlement三模块加载实际退出0、ERROR0、无Native；39方法承接c505实际结果，不谎称在e85重跑。a340全量42路由/视口的120张PNG及6张同条件财务对照图全部独立亲看；e85受影响14路由/视口的19+2张补验图也全部亲看。独立新物理PG只读/RR连接完成145业务表、13元数据表、83实际文件核验，rollback后关闭。私有只读包成员字节/SHA已实际读回。远端同步/Issue实际读回已由主控补记；用户亲手验收、实机、正式政策与完整S13未被自动启用。

## 证据简称

|简称|真实载体与范围|
|---|---|
|S|实际产品源码、英文源/zh_CN、S12文书契约与12指标字典；SOURCE不是动态通过|
|R39|`final-tools-suite-suite` 原命令/退出/日志和完整 pre/post；独立 `final-tools-suite-independent.json`|
|H12|`http-final-export-present`，12指标真实页面/全分页/CSV/钻取；CSV11字段完整签名和有效条件一致|
|HP|`read-export-final-present`、`read-export-final-absent`、`warehouse-only-http-v3`；正常角色四组合及纯仓库边界，含正常授权恢复读回|
|F|`final-finance-pages-and-positive-independent.json`；新增740来源、6真实PDF逐页、4办理前后8图与不同物理连接提交读回|
|P|`final-long-all-pdf-pages-independent.json`、`final-rest-all-pdf-pages-independent.json`；最终候选11份新PDF21页全部亲看、文件及页图SHA核验|
|L|`long-label308-independent.json`、`internal-qr301-native-locate214-independent.json`；普通单张/长字段两张100×70、软件解码、正常原生菜单定位及4图|
|T|`long-table309-independent-visual.json`、独立原生文本回执；原309三页、52未知牙位各一次且三页均有表头|
|A|`auxiliary-cancel-positive-and-revocation-independent.json`；免单/日结两取消两提交4图、原生提交读回及临时结算权回收|
|E|`external-original20-independent.json`；外部原件正常选择/上传303/下载原字节、两视口与跨店拒绝|
|N|`new-followup282-positive-independent.json`、`followup-closed277-negative-v1`；新来源未接通正例、终态真实409；旧责任全字段已由G最终独立新连接保持核验|
|Q|`report-new-source-contributions-final`；普通 HTTP 实际新旧来源分区对账，不冒独立PG总验|
|V|`final-browser120-and-paired6-independent.json`、`final-ui-translation-delta-independent.json`；最终全量120+同条件6+翻译补验21张均逐张亲看；旧114图仅前轮对照|
|G|`final-fresh-protection-independent.json`；验收者另开唯一目标物理PG RO/RR连接，145/13/83、旧20原件/37文件/全部旧审计及业务源保持；`ui-s13-final-load-independent.json`分类最后加载|
|W|`final-view-only-package-independent.json`、`before14-static-comparison-independent.json`；私有0400 ZIP全部成员读回，最终19PDF32页+旧17PDF+183PNG；before14有工作树静态准备限制|

所有 PASS 均只指该行明示的软件断言与层级，不能据此直接推导完整 UX、用户效果或生产通过。

## UX-01—08

|UX|预期与实现位置|实际与层级|状态/限制|
|---|---|---|---|
|01|12指标中文业务摘要、原始字典入追溯；`ydental_reporting/models/ydental_reporting_presentation.py`、controllers/reporting.py、views/zh_CN|H12验证全部12指标标题/主结果/来源；S/R39核稳定key与公式，领域状态分别映射；实际PDF用途中文|适用SOURCE/MODEL/HTTP/PDF/BROWSER通过；最终翻译受影响页及400中文已补验|
|02|授权法人/门店/币种及岗位对象选择；reporting、settlement._patient_options、documents、inventory、lab原生search view|H12授权选项/非法参数/真实来源；HP纯仓库无医疗来源泄露；E正常业务号选账单/前版；L真实菜单按识别码定位工单|正常角色HTTP/浏览器正负例及最终岗位搜索/无结果/选择/钻取V通过；管理员非本批常用岗位ID表单未扩大重做|
|03|中文财务用途、USD0.01、实际/录入/生成时点；settlement print service、print QWeb/PO|F每份完整显示实际500、批准100实退0、实际退款100、当前AR240及真实不同UTC；原价600不回写目录620|已交付文件逐页通过；后续免单后AR230另时点；无正式税票/签署/出纸声明|
|04|短A4一页、80mm不裁切、标题随内容/重复表头；print report QWeb|F/P对应部分付款、批准待退、实退、多账分摊均各一A4；收退款80mm各一页。T原长表三页均重复表头；P长同意3A4/4窄纸为合理多页，尾页含实质正文和完整追溯|适用逐页通过。旧失败迭代保留；不要求长临床强压一页；窄纸金额有可读换行，不冒实机纸型批准|
|05|100×70演示标签与被动QR；lab print service/原生search view、print paperformat|L普通301一张；长字段308两张、完整264字说明与材料/色号保留，明确非常规长内容布局。QR软件解码等于冻结/当前载荷；原生识别码facet唯一定位214，无接收/入库/联系|软件有限通过；长标签两页已披露，不承诺所有长内容单张或物理扫码|
|06|临床/同意/检查/处方用途、正文/实际作者/范围；公共QWeb、各print service/PO|P草稿/摘录/完整selection14/15/16及作者/未纳入原因/实际医嘱执行保留，检查/处方中文且未签/待审标识完整；财务件不含临床免责声明|最终文件逐页通过；正式临床正文与签署政策未改、未批准|
|07|两固定桌面视口无根横向溢出、局部表滚动；reporting/print SCSS及各岗位模板|E/L的两个视口已独立亲看且root宽等于viewport；前轮入口/中文/金额缺口已修；V最终120+21图已全看，长列表/局部滚动和原生M2O省略使用正常详情可达|最终指定两视口及适用交互通过；未用overflow:hidden掩盖内容或旧截图替改后页|
|08|默认查看、按需办理/取消、终态复诊只读；settlement、inventory/access、followup模板/controller|F普通前台结算权实际收款/申请、另一审批者批准、结算执行；A取消无经济变化，免单/日结能力仍可办理；N新未接通仍待联系/责任11，closed277真实409|实际新源办理、取消、终态页面/409、最终责任保护和翻译后400中文通过；未重开旧终态补正例|

## UX-F1—F5

|流程|预期/实际|证据层级|当前结论|
|---|---|---|---|
|F1|正常选择日期/币种/授权店→实收实退当前应收→分摊/原来源→返回条件；Q现旧AR1073+新230=1303，日期限定账单群当前余额|S/R39/H12/Q/V/G|HTTP与最终视觉通过；金额旧新分区由独立PG确认|
|F2|旧件保持；独立新740来源正常形成收500欠240→批准100实退0→实际退100；多账270+200收300分摊270+30欠170；新版真实时间|F/P/G，全部交付新PDF逐页|当前文件/真实办理正例及最后旧全事实G通过|
|F3|旧93冻结draft与214当前sent不同；新单张label301与长308；正常受控识别只定位|L/实际文件/软件解码/正常原生BROWSER/不同连接前后保护|适用软件通过；无接收/入库/外部联系/物理扫码|
|F4|医生、结算/有权前台、纯仓库不记内部ID查阅；授权范围不扩大|H12/HP/E/L/V/G|适用角色正负例及最终岗位全图通过|
|F5|查看展开取消不改变经济；明确进入正常办理；关闭复诊无可提交联系表单且直POST拒绝|F/A/N/R39/V/G|实际新源办理、取消/终态拒绝、最终视觉与旧责任保护通过|

## UX-T01—22

|TC|预期、实现位置|已核实际/证据|层级与限制/当前结论|
|---|---|---|---|
|01|12指标中文无字典作主视图；reporting presentation/templates/PO|H12全部标题/来源正确，S/R39保持key/公式|SOURCE/MODEL/HTTP及最终BROWSER视觉通过|
|02|USD0.01及实际/录入/生成各取真实源；financial print/presentation|F六份逐页均明确时点；收500、批准100、实际100不混淆；非收入非税用途|PDF/BROWSER/提交读回有限通过；末次翻译只补其受影响页|
|03|授权法人/门店/币种，组合由后端校验；reporting controller/service|H12正常selectors、无权门店403，非金额币种409；R39原生HTTP非法过滤/撤权等|SOURCE/MODEL/HTTP通过；公司/门店边界按现有合成目标而非虚构多法人正例|
|04|岗位患者/物料搜索、同名/无结果/分页/最小读取；settlement/documents/inventory|R39明确分页/非法页/范围；HP纯仓库；E业务账单搜索；L真实菜单code搜索|MODEL/HTTP及最终三岗位BROWSER搜索/无结果/详情状态通过|
|05|期间发生额与当前账单群/待办分开，非金额不残留币种；reporting字典/presentation|H12有效filters/timezone/UTC边界，R39原生DST/非法过滤，Q查询时点与新旧分区|SOURCE/MODEL/HTTP通过；不称历史as-of余额或跨币换算|
|06|全分页/CSV/钻取返回同一条件、来源上限拒绝；reporting|H12全部12 CSV200且全11字段/顺序/全分页签名一致，filters除实际query_at同；正常来源钻取与返回URL；R39上限断言|MODEL/HTTP通过；真实数据可合法变动，不强求不同请求旧截图恒同|
|07|读/导出四组合、单份与批量；原件/report权限|HP最终a340 present+absent普通HTTP：有源单份200；批量须源+export；无源即便export仍403；R39同契约|最终HTTP通过；旧e85整体FAIL仅保留其中真实子结果，不冒最终四组合|
|08|跨店/公司/撤权/旧页/下载/导出重核；controllers/services|HP纯仓库17无医疗/财务来源；A前台结算撤权旧session及fresh403；E同14正常选店2对真实店1账单/新原件403；R39附件/缩略图/CSRF等|MODEL/原生HTTP/普通HTTP通过；最终G已复核临时权限语义回收，不把原生缩略占位当文件泄露|
|09|对应59/60/61/62结构新A4各1页，80mm无裁切无孤页；financial QWeb|F部分500/批准100未退/实退100各1A4；P多账分摊各1A4；F窄纸收/退各1页，逐页亲看|真实PDF视觉通过；新时点/新来源与旧件不假称同快照|
|10|中文长文/长表完整、标题随内容、重复表头；公共QWeb|P两长同意全部7页正文/作者/状态/追溯保留；T52未知FDI各一次/三页表头均在|真实PDF视觉通过。原309检查器因兼容部首未NFKC而exit1，原图/native文本纠正；未加载layout8已前向revert，不反写原FAIL|
|11|单张普通100×70/QR软件一致/无副作用；lab/print|L普通301单页、长308两页披露；真实native菜单按code定位214、四图/两视口亲看；214/280/253/contact/库存/mail/SMTP/旧scan前后投影同|PDF/软件QR/原生BROWSER/源投影通过；不冒实机或扫码接收入库|
|12|草稿/部分摘录/完整集合、未纳入原因、实际作者和待签用途；公共文书层|P全部对应临床/summary/consent/exam/Rx逐页亲看；F财务没有临床不适用免责声明|真实PDF视觉通过；正式医学签署/政策仍未启用|
|13|1366×768及1440×900/100%根无溢出、关键列/操作可达|V42路由/视口120图+同条件6图+e85翻译受影响14路由/视口21图均独立亲看，严格root/body尺寸记录无溢出，100%缩放|最终BROWSER视觉通过；实际尺寸断言与亲看共同成立，未隐藏内容凑通过|
|14|查看/展开/进入/取消不改费库款及责任；岗位模板|A免单与日结两次取消显式业务投影逐字段同，仅query_at变化；E选择/展开/取消原件及账单同；L定位保护投影同|HTTP/BROWSER/不同物理提交读回通过；正常会话/查看审计不要求全库物理零变|
|15|修改过办理普通有权新源正例，审批执行分离|F普通前台结算权收500/申请100、另一人批准、结算执行100；A新源免10与cashier8日结500/0/0；N新282手工未接通仍待联系|实际BROWSER/不同连接提交读回通过；仅新源，旧经济未重放；全局旧事实最终G已独立保持核验|
|16|closed只读历史/原因，直POST仍409，非终态不误隐藏|N closed277真实普通HTTP409且该源/contacts同；新282非终态可办理；S closed行无任何form且reopen独立设置区带真实目标说明|SOURCE/HTTP/正常新源BROWSER通过；最终closed/独立重开设置/错误400中文V均已补验|
|17|旧原件实际bytes/SHA保持，新版另存/来源时间正确，缺件不再生|G各次完整pre/post逐文件保护；P/F/L/T新版均另存并核SHA；E外部20原字节与旧5保持；R39存储/缺件/版本机制|MODEL/HTTP/PDF/即时保护通过；最后独立新物理连接83files逐文件SHA保持；初始旧20原件/37附件全部未变，新增45内部原件+1外部件另存|
|18|旧金额/分摊/600价/退款/lot253及未完成责任保持，新贡献另核|G现前态保留旧来源；Q同有效范围旧AR1073+新230=1303；新740/贷项110/实收500/实退100/待退0，耗用新增0；followup新增2，unique按union|普通HTTP与最后独立新连接已核资金/库存/责任及总分区，不硬编码1073为未来全库总额|
|19|失败/重复/恢复按改动影响，未知先查已提交|R39实际渲染失败恢复/重复/子模板变化拒stale+新版本/旧bytes保持；L同key返回同原件SHA；新1313原lease自然过期后正常续接、455pending责任保留；首fixture409未产生event/fee|MODEL/HTTP/真实新源恢复通过；旧Native139因果仍UNKNOWN，后修依赖/真实0不反签其根因|
|20|最终适用加载即时前后态、退出/差异分类；限定模块|最终b9print-u实际0，新增tracechild冻结/PO引用；c505仅test+CURRENT实际39，完整pre/post全业务/63files同仅module时间；a340仅CURRENT，正常新基线83files非升级授权|各次独立加载分类通过；最后e85仅三受影响模块加载0/ERROR0/noNative，145/83前后除ACL/group时间和既有XML mutex fence外业务保持；最终定点补验完成|
|21|未实现者独立固定候选/所有交付新PDF每页/两视口真实结果|本验收者已亲看最终普通/长标签、全部临床/汇总/同意/检查/Rx、六财务、长表；独立回执不由实现/工具作者冒签；最终全量V、翻译受影响V与新物理RO/RR保护G均已完成|本子计划适用软件独立通过；实现者/测试作者与验收者真实分工，不冒OS隔离或用户亲手验收|
|22|全部范围/普通角色复现/私有包/同步读回/#37OPEN|UX/P2均未跳过；W只读包0400、222成员/36PDF/183PNG全SHA读回；正常三岗位各7—8步路径已核。主控实际推送/ref/Issue读回见末段|软件/包/路径已独立通过；同步由主控实际读回为SYNCED。只在#37最终记录并保持OPEN，#36保持关闭；不合main/部署/负载/恢复/设备/下一计划|

## 最终独立软件结论与同步事实

UX-01—UX-08（含P2）、UX-F1—F5及UX-T01—21适用软件断言通过。最终19份PDF32页已逐页亲看：A4部分收款/批准待退/实际退款/多账分摊各1页；80mm实际覆盖部分收款与实际退款各1页，不宣称未生成的纸型×状态组合已验。普通100×70标签1张；264字长标签为已披露2张；长同意3/4页合理分页；长表52行3页且每页表头。原文件、生成时点、作者和旧状态保持。

验收者最后新物理连接 `upgrade-independent-final-protection-baseline.json` SHA `aa763a8b7c40019e24c77f57d89b32e53a4fd62fc55b9a3c2672a764a87f114f`：目标OID2171423/原cluster、READ ONLY/REPEATABLE READ、rollback后连接关闭；没有业务写。旧1073+新230=1303；新账740、收500、批准后实退100、贷项110、待退0；旧lot253实际10/2/8，旧214sent/280waiting及旧未完成责任全字段保持。新455pending/v1作者责任9、新508pending/v2与task880pending、新215draft/281waiting/282待联系和唯一未接通联系65如实保留；3个新编辑租约均已正常释放，临时6能力记录none且原权限值保持。所有旧审计原行保持，新增查看/授权/正常业务审计单列。

最终浏览器工具并非全部一次成功：翻译delta-v1因waiting280表单预期错误exit2；v2已完成12路由/视口后因当前无权限模板fixture而exit2；v3remaining实际exit0补2管理视口和正常400中文。19+2张全部独立亲看，未反签失败进程为0。无模板的权限preview没有运行；新增ARIA exactref按SOURCE及已加载view/PO证据记录，不虚构浏览器preview。管理账号本批未改的员工/政策办理并未全面重做。

UX-T22同步补记（主控/root）：首报告fa89ef1f5e4ee6365846aad67cab3de85f252bba正常push/ref和计划/CURRENT/三报告全文/blobSHA实际读回同；main仅两份文档0b3cf95e1762786f8ccbea48291ef2fa0b630b12正常push/ref/全文读回同；[#37唯一最终评论6382778460](https://github.com/Yredxin/YDental/issues/37#issuecomment-6382778460)逐字同且OPEN/2评论，#36仍CLOSED/2评论无改动。首回执222a06b9e64a23610901e337df687934ee09055329011fe07948a2a61e92a172；末次仅同步元事实文档完整HEAD及再读回见同一评论，产品/执行候选不变。技术与同步结论分别为TECHNICALLY_COMPLETE/SYNCED，未用预签代实际工具。私有包与5—10步角色路径已通过，软件结论不依赖用户亲手或实机审查，也不冒称其通过。#37保持OPEN、#36保持关闭，不合main、不部署、不启动下一计划。

本表不把历史工具错误、兼容字符检查器误判、只读元数据过期拒绝当成永久停工，也不把已修复的新候选反签到历史FAIL。客户端Native139因果UNKNOWN保留；已停止受影响动作、依赖修正及实际正常退出分开记录。所有经济正例来自独立新合成来源，未为截图重付、重退、重治、重出入库。
