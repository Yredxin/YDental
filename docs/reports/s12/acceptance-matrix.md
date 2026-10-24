# S12 F/T逐项验收矩阵

当前冻结草稿：实际业务实证及限定独立结论已具备，T10最终数据升级/全表保全和总签PENDING。本表不预签技术完成。全部行产品/工具候选为`5cb1e46fbe1e4243c7a292f64ecfd375afb3dce2`，core固定f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb；最终仅文档执行HEAD在[证据索引](evidence-index.md)另列。

普通actor：8前台、9医生、10检查、12原生采购、13仓库、14结算、15退款批准、16有医疗源读取无导出、17无源；5为正常集团管理。2仅进行正常原生语言/产品主档配置，不冒普通角色验收。所有目标均唯一OID2171423；写入仅本阶段新合成来源。

每行“软件通过”仅指列出的实际软件断言，真实正式正文/临床签署/经营政策/税票/设备出纸均按外部条件NOT_RUN/待审核，不被行内结论覆盖。独立人员为未实现产品/测试的`/root/acceptance`；完整原始路径、SHA、命令/退出码和失败记录见证据索引。

|编号|来源/版本与前提|实际操作及预期/实际|层级及独立证据|软件结论 / 未验|
|---|---|---|---|---|
|F1|新524；D2=328v2已确认，D1=354 pendingv2；同scope source selections13—16|完整生成409并指明未确认来源；draft95与受策略excerpt96不冒完整。正常确认D1v3后complete99，原件链1→2→3，旧文件bytes不变，费库款未重复|正常HTTP/新RO-RR/6真实PDF逐页；consent-summary-independent `113b0899d0f7707428626ca596345ab93dd5727014a623697ec3baf72f808f5e`|软件通过；正式临床汇总/签发政策未批准|
|F2|521/522/523新source；bill72/76/77/79，pay7/8，refund3|740收500欠240；批准100时实退0/待退100；执行后另凭据61。270+200收300精确270+30/欠170。原59/60不改|正常HTTP/nativeposted/独立RO借贷分摊/6PDF逐页；financial-independent `65c74ae13234c06d674ebf35462352693ed4438cba334c57e0788e63215b78d5`|软件通过；无真实资金/正式财务政策批准|
|F3|合成模板29/30/31/32；consent97/98；evidence10/11|生成仍未签；上传pending，明确软件verify/reject留人时结论；同件恢复不重置，跨原件409，不复用签名；另店/旧版按明确策略。打印只请求，paper unknown|正常HTTP/独立提交/文件；113b0899…；MODEL受控device failure与31回归原log|软件通过；真实签署/物理设备故障与出纸NOT_RUN|
|F4|524 arrival517；area7/8，exec349/350，events291/292各qty1；新金融/lot253/lab214/followup280|一个canonical患者/一个arrival；两项目按catalog/UOM；跨日收退、原单冲销分列；分页/CSV/钻取与原生核对|正常HTTP/独立RO/F4 baseline+1/+1/+2；integration-label-f4-independent `c378be85120584ee5a06f2cd0a676359c16f1576d4f8e1d47ae698ba354a81fd`及金融/耗用/加工回执|软件通过；正式经营口径发布待审，非50会话|
|T01|原件94长FDI表，95/96/99合集，97/98长正文；所有21份独立PDF|21份/49页实际render亲看；52unknown FDI跨页重复表头；中文/状态作者/空值/页脚；80mm实测227pt约80.08mm。旧1原排版保留，后续模板新件修正|真实PDF/逐页图/高分辨率必要复看；113b0899…及各视觉独立receipt，原始index路径见证据索引|软件通过；实机纸型、切纸与出纸NOT_RUN；轻微分页限制如实保留|
|T02|本阶段254→656/merge26；273v3/旧1、30、57；新100v4 prev57；确认600/原63，目录620|正常更名/确认合并/模板升级/改目录后旧件下载SHA不变；新版本另存；273历史作者及文本版本保持；604合法canonical迁移但仍pending|正常HTTP+新物理RO/前后文件；merge-original-independent `c389e39c584a912ab2e69c1911c0a5a3d05ce253e66953d26d360812c5f4b7d9`，首链/金融/合集回执|软件通过；未动旧S11身份/账本|
|T03|328v2确认+354pendingv2→v3；完整拟纳集合不缩减|complete真实409而不是过滤D1；draft/excerpt披露范围；正常补确认后新complete；arrival/费用/库存不增加|正常HTTP/已提交source/file；113b0899…；31内完整集合/政策回归|软件通过；不等于正式临床签署|
|T04|97/98材料，10/11上传件，normal9验证/拒绝|打印不变已签；上传不自动核验；verified仅synthetic软件分支；原文件/人时/结论实际可核，未编造签名或印章|正常HTTP/真实附件/RO与4+5页PDF；113b0899…|软件通过；真实告知、签署、审核正文NOT_RUN|
|T05|bill72=740/pay7=500/refund3=100；原58—61|批准与执行分开，未执行时真实native_payment为空；执行后posted真实合成退款；旧收款原件不变，生成不重做资金|正常HTTP/独立原生分摊/文件；65c74ae1…；31内render失败保留已写付款MODEL断言|软件通过；无真实现金/支付通道|
|T06|医疗/检查/财务各四读/导出组合；正常9/14/16/17；source附件|真HTTP单份/ZIP/报表与RPC/直链正负；原生缩略图200仅标准占位PNG，download仍拒；撤权/切店旧页重核；普通浏览器导航/下载/过滤/新source drill/无权403|7真实HttpCase+normalbrowser；31独立 `18158ffe369b5b3077f1bd501e375a7239c85a8e487d41dd03f9e79d6c822b85`；browser-independent `d86c54a1073b1beeaeac2ab1cb680bad314ddd03d95e949ee620df0fbf250d04`|软件通过；不把占位200/fixture预拦截冒产品泄露或拒绝|
|T07|normal9/273v3/prev30→57；显式default-off native delay|实际0.7527秒ReadTimeout后未知，不自动retry；新RO先确认commit与可读file，再同keyduplicate恢复、同SHA。经济17表不变。原字体409无原件后原key恢复；设备失败仅受控MODEL模拟|真实HTTP+新PG/RR/file；t07-independent `01da7c4beb1e84302d717603de8880e30ae54531fe77af82423b6cc9f1deed1b`；原首因保留|软件通过；无真实打印机失败/出纸证明|
|T08|内部bill58/63与tax example5→bill72分入口|标题内部账单与醒目NON TAX区分；普通14上传/下载/printrequest原bytes同SHA；17真403；三audit paper unknown；预览不替换原文件|正常HTTP/独立RO/实际1页例件；tax-original-independent `e88a9dc47a3886fd84277a926dac2be441ac0d13c817c67eb55d1ca67a48d53a`|软件通过；真实税票/票种未提供，真实分支NOT_RUN|
|T09|actualarrival517/events291/292；pay7昨日/refund3今日；nativecredits；lot253，214/280|唯一患者distinct、到店/执行分事件；18金融日期scope对账；consume仅2排receipt10；待交付sent1与planned/waiting复诊责任；原生source drill/CSV一致，不追改历史/现价|正常HTTP/CSV/drill+独立RO；金融65c…/库存 `2b80ee6286d00edb5447010938e022d742c269e6e287156634c914be711cd8d1`/加工 `b942cb8db0ae2cc765270ce7a5ed33d66c9f54bdc18c2ffceaaa3975c93009a6`|软件通过；as-of历史余额未实现且明确不冒，正式经营政策待审|
|T10|固定5cb/source bytes、同一有数据目标、普通配置/权限变化|真实安装2新模块与若干完整pre/post限定升级已验；纯文本注入负例/撤权/恢复13权限通过；最后一次最终6模块即时pre→upgrade→post与独立总签待完成|31回归/各中间独立升级及13nativegrant恢复；最后pre/post/固定执行candidate在证据索引补|PENDING最终升级；不预签完成|
|T11|bill76=270/77=200/pay8=300；bill79=600/price281→282=620|真实nativepartial32/33=270+30、欠170；确认价/账单/原件63不重定价，当前quote620另显；无旧经济链重付|正常HTTP/原生RO/实际PDF；65c74ae1…|软件通过；同币种合成演示价，不批准正式价格|
|T12|店1/2同意策略；A16/B9真实PG；source273v2→3/original30；typed QR修复|新店不继承已签、旧版明确批准才接受；两连接实际交错保持旧v2一致快照；正常view/download/print独立audit；QR同码随机PNG不进sourceSHA，真实两preview稳定/错digest版本409/93唯一|真实双PG/RR/native renderer同步hook（MODEL，不冒HTTP并发）`ebc047413d21de4742f079c06b107f38659927ea61131bf54049e651ce9cb570`；113b…/c378…；两个新encoder/auth seam明确另层|软件通过；正式政策/设备验收不在此PASS内|

全部失败原始状态和时间层级在证据索引保留：旧31之前的FAIL、不正确收尾exit2、QR409及普通配置guard拒绝均未改成成功。后续合法推进的最终状态与文件冻结旧状态分开：214现sent而93仍draft版文件；670已handover而701仍pending；254已inactive/canonical656而旧源273历史patient254保持。
