# S13 UX 独立验收矩阵

本表为未实现者 `/root/acceptance` 的执行中草稿，尚未签本子计划总通过。验收者未实现产品或测试工具；共享 OS 不构成隔离。私有原始证据和独立回执由 `evidence-index.md` 索引，公共仓库不含 PDF、截图、认证材料或原始请求。

被测产品为 `b9a9bd70cd918f11606a81bf8d26398d8df62c64`（布局7），产品及测试工具执行候选 `c5052e519cb8fc97bc41a2867ab7155cf11d3547`。普通 HTTP/浏览器后续候选 `a3409907ae4c5b6dd7f2aaf0a17d36c1999f8705` 与 c505 产品/工具净字节相同，仅 CURRENT 文档变化。c505 实际运行39方法，30 MODEL、7原生 HTTP、2明确标示的加工授权/编码替身；0失败、0错误、进程0、无 Native 信号。不能把框架内部55条统计称为55项业务方法。

待实施的最小翻译增量、其适用加载及页面补验须另绑定真实新候选；当前结果不冒称在该增量上执行。最终42个路由/视口、116图及6张同视口财务对照图已由测试者采集，独立全图亲看尚 PENDING。最终独立新连接保护及同步读回也 PENDING。用户亲手验收、实机、正式政策与完整 S13 均未通过本表自动启用。

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
|N|`new-followup282-positive-independent.json`、`followup-closed277-negative-v1`；新来源未接通正例、终态真实409；旧责任全字段最终核验仍待独立保护连接|
|Q|`report-new-source-contributions-final`；普通 HTTP 实际新旧来源分区对账，不冒独立PG总验|
|V|最终全量浏览器及翻译增量补验，独立全图亲看 PENDING；旧0d569的114图只作为已审前轮结果和效果对照|
|G|完整即时保护投影/实际文件SHA、各次限定加载及独立差异分类；最近基线83文件，最终独立新连接 PENDING|

所有 PASS 均只指该行明示的软件断言与层级，不能据此直接推导完整 UX、用户效果或生产通过。

## UX-01—08

|UX|预期与实现位置|实际与层级|状态/限制|
|---|---|---|---|
|01|12指标中文业务摘要、原始字典入追溯；`ydental_reporting/models/ydental_reporting_presentation.py`、controllers/reporting.py、views/zh_CN|H12验证全部12指标标题/主结果/来源；S/R39核稳定key与公式，领域状态分别映射；实际PDF用途中文|适用 SOURCE/MODEL/HTTP/PDF通过；V及纯翻译增量补验 PENDING|
|02|授权法人/门店/币种及岗位对象选择；reporting、settlement._patient_options、documents、inventory、lab原生search view|H12授权选项/非法参数/真实来源；HP纯仓库无医疗来源泄露；E正常业务号选账单/前版；L真实菜单按识别码定位工单|已实现且有正常角色HTTP/浏览器有限正负例；最终岗位搜索/分页全图V PENDING|
|03|中文财务用途、USD0.01、实际/录入/生成时点；settlement print service、print QWeb/PO|F每份完整显示实际500、批准100实退0、实际退款100、当前AR240及真实不同UTC；原价600不回写目录620|已交付文件逐页通过；后续免单后AR230另时点；无正式税票/签署/出纸声明|
|04|短A4一页、80mm不裁切、标题随内容/重复表头；print report QWeb|F/P对应部分付款、批准待退、实退、多账分摊均各一A4；收退款80mm各一页。T原长表三页均重复表头；P长同意3A4/4窄纸为合理多页，尾页含实质正文和完整追溯|适用逐页通过。旧失败迭代保留；不要求长临床强压一页；窄纸金额有可读换行，不冒实机纸型批准|
|05|100×70演示标签与被动QR；lab print service/原生search view、print paperformat|L普通301一张；长字段308两张、完整264字说明与材料/色号保留，明确非常规长内容布局。QR软件解码等于冻结/当前载荷；原生识别码facet唯一定位214，无接收/入库/联系|软件有限通过；长标签两页已披露，不承诺所有长内容单张或物理扫码|
|06|临床/同意/检查/处方用途、正文/实际作者/范围；公共QWeb、各print service/PO|P草稿/摘录/完整selection14/15/16及作者/未纳入原因/实际医嘱执行保留，检查/处方中文且未签/待审标识完整；财务件不含临床免责声明|最终文件逐页通过；正式临床正文与签署政策未改、未批准|
|07|两固定桌面视口无根横向溢出、局部表滚动；reporting/print SCSS及各岗位模板|E/L的两个视口已独立亲看且root宽等于viewport；前轮114图发现的入口/中文/金额缺口已修；V有最终采集但尚未独立全看|PENDING：最终全量V及翻译增量受影响页补验，不用旧截图代最终|
|08|默认查看、按需办理/取消、终态复诊只读；settlement、inventory/access、followup模板/controller|F普通前台结算权实际收款/申请、另一审批者批准、结算执行；A取消无经济变化，免单/日结能力仍可办理；N新未接通仍待联系/责任11，closed277真实409|有限正负例通过；最终终态页面V、原责任最终G及翻译增量错误分支待补|

## UX-F1—F5

|流程|预期/实际|证据层级|当前结论|
|---|---|---|---|
|F1|正常选择日期/币种/授权店→实收实退当前应收→分摊/原来源→返回条件；Q现旧AR1073+新230=1303，日期限定账单群当前余额|S/R39/H12/Q；V待独立|HTTP软件通过，最终视觉 PENDING|
|F2|旧件保持；独立新740来源正常形成收500欠240→批准100实退0→实际退100；多账270+200收300分摊270+30欠170；新版真实时间|F/P/G，全部交付新PDF逐页|当前文件与真实办理正例通过；最后旧全事实G待独立|
|F3|旧93冻结draft与214当前sent不同；新单张label301与长308；正常受控识别只定位|L/实际文件/软件解码/正常原生BROWSER/不同连接前后保护|适用软件通过；无接收/入库/外部联系/物理扫码|
|F4|医生、结算/有权前台、纯仓库不记内部ID查阅；授权范围不扩大|H12/HP/E/L；V待全图|已有有限角色正负例通过；最终岗位全图 PENDING|
|F5|查看展开取消不改变经济；明确进入正常办理；关闭复诊无可提交联系表单且直POST拒绝|F/A/N/R39；V/G待最终|实际新源办理与取消/终态拒绝通过；最终视觉/旧责任保护 PENDING|

## UX-T01—22

|TC|预期、实现位置|已核实际/证据|层级与限制/当前结论|
|---|---|---|---|
|01|12指标中文无字典作主视图；reporting presentation/templates/PO|H12全部标题/来源正确，S/R39保持key/公式|SOURCE/MODEL/HTTP通过；V最终视觉待补|
|02|USD0.01及实际/录入/生成各取真实源；financial print/presentation|F六份逐页均明确时点；收500、批准100、实际100不混淆；非收入非税用途|PDF/BROWSER/提交读回有限通过；末次翻译只补其受影响页|
|03|授权法人/门店/币种，组合由后端校验；reporting controller/service|H12正常selectors、无权门店403，非金额币种409；R39原生HTTP非法过滤/撤权等|SOURCE/MODEL/HTTP通过；公司/门店边界按现有合成目标而非虚构多法人正例|
|04|岗位患者/物料搜索、同名/无结果/分页/最小读取；settlement/documents/inventory|R39明确分页/非法页/范围；HP纯仓库；E业务账单搜索；L真实菜单code搜索|MODEL/HTTP/有限BROWSER通过；最终三岗位搜索状态V待独立|
|05|期间发生额与当前账单群/待办分开，非金额不残留币种；reporting字典/presentation|H12有效filters/timezone/UTC边界，R39原生DST/非法过滤，Q查询时点与新旧分区|SOURCE/MODEL/HTTP通过；不称历史as-of余额或跨币换算|
|06|全分页/CSV/钻取返回同一条件、来源上限拒绝；reporting|H12全部12 CSV200且全11字段/顺序/全分页签名一致，filters除实际query_at同；正常来源钻取与返回URL；R39上限断言|MODEL/HTTP通过；真实数据可合法变动，不强求不同请求旧截图恒同|
|07|读/导出四组合、单份与批量；原件/report权限|HP最终a340 present+absent普通HTTP：有源单份200；批量须源+export；无源即便export仍403；R39同契约|最终HTTP通过；旧e85整体FAIL仅保留其中真实子结果，不冒最终四组合|
|08|跨店/公司/撤权/旧页/下载/导出重核；controllers/services|HP纯仓库17无医疗/财务来源；A前台结算撤权旧session及fresh403；E同14正常选店2对真实店1账单/新原件403；R39附件/缩略图/CSRF等|MODEL/原生HTTP/普通HTTP通过；最终G复核临时权限语义回收，不把原生缩略占位当文件泄露|
|09|对应59/60/61/62结构新A4各1页，80mm无裁切无孤页；financial QWeb|F部分500/批准100未退/实退100各1A4；P多账分摊各1A4；F窄纸收/退各1页，逐页亲看|真实PDF视觉通过；新时点/新来源与旧件不假称同快照|
|10|中文长文/长表完整、标题随内容、重复表头；公共QWeb|P两长同意全部7页正文/作者/状态/追溯保留；T52未知FDI各一次/三页表头均在|真实PDF视觉通过。原309检查器因兼容部首未NFKC而exit1，原图/native文本纠正；未加载layout8已前向revert，不反写原FAIL|
|11|单张普通100×70/QR软件一致/无副作用；lab/print|L普通301单页、长308两页披露；真实native菜单按code定位214、四图/两视口亲看；214/280/253/contact/库存/mail/SMTP/旧scan前后投影同|PDF/软件QR/原生BROWSER/源投影通过；不冒实机或扫码接收入库|
|12|草稿/部分摘录/完整集合、未纳入原因、实际作者和待签用途；公共文书层|P全部对应临床/summary/consent/exam/Rx逐页亲看；F财务没有临床不适用免责声明|真实PDF视觉通过；正式医学签署/政策仍未启用|
|13|1366×768及1440×900/100%根无溢出、关键列/操作可达|E/L定点两视口已审；V42路由/视口116图已采，独立全图及翻译增量补验尚待|PENDING；不以scrollWidth单个断言或隐藏溢出替代亲看|
|14|查看/展开/进入/取消不改费库款及责任；岗位模板|A免单与日结两次取消显式业务投影逐字段同，仅query_at变化；E选择/展开/取消原件及账单同；L定位保护投影同|HTTP/BROWSER/不同物理提交读回通过；正常会话/查看审计不要求全库物理零变|
|15|修改过办理普通有权新源正例，审批执行分离|F普通前台结算权收500/申请100、另一人批准、结算执行100；A新源免10与cashier8日结500/0/0；N新282手工未接通仍待联系|实际BROWSER/不同连接提交读回通过；仅新源，旧经济未重放；全局旧事实最终G待独立|
|16|closed只读历史/原因，直POST仍409，非终态不误隐藏|N closed277真实普通HTTP409且该源/contacts同；新282非终态可办理；S closed行无任何form且reopen独立设置区带真实目标说明|SOURCE/HTTP/正常新源BROWSER通过；最终closed与错误提示V及翻译增量补验待独立|
|17|旧原件实际bytes/SHA保持，新版另存/来源时间正确，缺件不再生|G各次完整pre/post逐文件保护；P/F/L/T新版均另存并核SHA；E外部20原字节与旧5保持；R39存储/缺件/版本机制|MODEL/HTTP/PDF/即时保护通过；最近83files基线与最后独立新连接全文件核仍PENDING|
|18|旧金额/分摊/600价/退款/lot253及未完成责任保持，新贡献另核|G现前态保留旧来源；Q同有效范围旧AR1073+新230=1303；新740/贷项110/实收500/实退100/待退0，耗用新增0；followup新增2，unique按union|普通HTTP与即时投影已核；最终独立新连接资金/库存/责任及总分区 PENDING，不硬编码1073为未来全库总额|
|19|失败/重复/恢复按改动影响，未知先查已提交|R39实际渲染失败恢复/重复/子模板变化拒stale+新版本/旧bytes保持；L同key返回同原件SHA；新1313原lease自然过期后正常续接、455pending责任保留；首fixture409未产生event/fee|MODEL/HTTP/真实新源恢复通过；旧Native139因果仍UNKNOWN，后修依赖/真实0不反签其根因|
|20|最终适用加载即时前后态、退出/差异分类；限定模块|最终b9print-u实际0，新增tracechild冻结/PO引用；c505仅test+CURRENT实际39，完整pre/post全业务/63files同仅module时间；a340仅CURRENT，正常新基线83files非升级授权|各次独立加载分类通过；待最小翻译增量仅受影响3模块加载/新候选pre/post及定点补验 PENDING|
|21|未实现者独立固定候选/所有交付新PDF每页/两视口真实结果|本验收者已亲看最终普通/长标签、全部临床/汇总/同意/检查/Rx、六财务、长表；独立回执不由实现/工具作者冒签；最终全量V与freshG尚待|PENDING总验；不以200/XML/提取文字或测试作者自签代视觉与持久保护|
|22|全部范围/普通角色复现/私有包/同步读回/#37OPEN|UX/P2均未跳过；真实层级/失败/候选分开。本表与summary/evidence-index/私有包待最终合流，推送/ref/Issue实际读回未发生|PENDING；只在#37最终记录并保持OPEN，#36保持关闭；不合main/部署/负载/恢复/设备/下一计划|

## 尚不能签总通过的剩余项

1. 最终全量浏览器图逐一独立亲看，及最小翻译增量的真实候选、加载前后保护、受影响页面/错误分支/取消补验。
2. 主控调度的唯一同库独立新连接：所有旧原件文件SHA、旧资金库存和未完成责任、全部新贡献/新增待办与临时权限恢复、外部通道状态。
3. 最终私有只读包及普通角色5—10步路径、公共索引脱敏，正常同步并实际读回；同步失败明示SYNC_PENDING。

本表不把历史工具错误、兼容字符检查器误判、只读元数据过期拒绝当成永久停工，也不把已修复的新候选反签到历史FAIL。客户端Native139因果UNKNOWN保留；已停止受影响动作、依赖修正及实际正常退出分开记录。所有经济正例来自独立新合成来源，未为截图重付、重退、重治、重出入库。
