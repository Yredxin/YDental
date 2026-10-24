# S13 UX 脱敏证据索引

本目录只公布索引和必要SHA，不上传原件、截图、原始审阅报告、请求日志、身份/provider、认证散列或运行连接配置。下列相对路径均位于本机忽略的 `.local/s13/`，不是可从Public下载的文件。正常角色及权限、源码边界见[summary](summary.md)，适用断言见[矩阵](acceptance-matrix.md)。

最终独立fresh与软件总验已完成；远端同步待收口，缺证据不补PASS。历史错误scope页眉不用于新准入；实际模板/布局、每页审阅及源码候选分开。

|证据|实际层级/限定|私有相对路径|SHA256|
|---|---|---|---|
|before14|BROWSER旧S12/静态资源差异限定|`verification/before/result.json`|`037905a67cd9e1093c401bc700fc6f8eb5b75cfdf7161b14e04c70a6884c29b2`|
|initial-full|RO/RR初始145业务/13技术/37附件|`verification/upgrade-initial-baseline.json`|`3c61bbfc6f65adcb246eb97cf7b6c96c9acb4fddcd6439ed5d5e3d275d40c974`|
|final39|30MODEL+7HttpCase+2显式seam/实际退出0|`checks/final-tools-suite-suite/result.json`|`9270342550f956279c8c5297163d86e959dc9b447dc5c7b35f4bade5dd28e39e`|
|final39-independent|未实现者原始日志/提交保护|`acceptance/final-tools-suite-independent.json`|`8bad928bc9737bbb98348993921d58fe57daff4fcf1aa6b6778ced3be62eea8e`|
|layout7-load|限定print正常加载/独立保护|`acceptance/layout7-final-load-independent.json`|`c388b6b81eacfc8a342ff62ce51dc0e55b7252b93b5ba34b6936b8dcb241f582`|
|common-long|11共用件中的长同意7页独立|`acceptance/final-long-all-pdf-pages-independent.json`|`92724467a7dd41c88ac07c46d54e44502969c7c807fae3280a5b9dc2290a6527`|
|common-rest|共同布局9件14页独立|`acceptance/final-rest-all-pdf-pages-independent.json`|`3cb547530ec7cbea01da1607d7819eae95e26d86a710306d0c870e82dd01bd28`|
|finance-new|新来源6件6页/8张办理前后独立|`acceptance/final-finance-pages-and-positive-independent.json`|`21fece23f77a3a0e01fd5d7d7c6b06f8e7aa5d662e3e46c6f085aeb263531145`|
|economic-new|新740/收500/批准100/退100正常提交|`first-loop/s13-ux-resume740-v1/result.json`|`1eab52e3ee5e6780eebfa524ea945535521c2c026e995870c4f909777f9544c1`|
|economic-process|实际外层/子进程0|`verification/process-new-financial-recovery-positive-v1/result.json`|`de8e65056787cf703dd0fc002772f5d8ab3767a4ade4ffb44b2c2cc74e6e2bb5`|
|auxiliary|免单10/日结/取消正常提交|`verification/auxiliary-settlement-s13-aux-waive-close-v1/result.json`|`a21c7bc0b7a651a368d2dad2a61fdbe6cb75912f6a1f3053369ca659b626fa52`|
|auxiliary-independent|免单/日结/取消/撤权独立|`acceptance/auxiliary-cancel-positive-and-revocation-independent.json`|`bac7ae0a0f64c9bac83b15ae001769706659f185fdb1911e7af7fc054e71a795`|
|long-label|新215/308长标签2页独立|`acceptance/long-label308-independent.json`|`bca428b3b5c570b73a15a18f7925e9f53a5af013a0702bc131e3d61b8ee343b1`|
|long-table|新309三页52行独立视觉|`acceptance/long-table309-independent-visual.json`|`d5a725a34c4d6795320f2a086b3f58813797ae5ebce9a28516a8cc38d240f6b4`|
|long-table-text|兼容字形归一/原生PDF文本|`acceptance/long-table309-independent-native-text.json`|`28b7bf1de6f0dcc8f2eff7c1007ff302ad46221197d707dac12963926aa99496`|
|long-table-corrected|原字节只读检查/真实exit0|`verification/long-table-corrected-inspection-v1/result.json`|`0ba55f2783fee080a32b2e3d8abbd39f7794c45be70d0ed9de41dac86e349879`|
|external20|正常303/同用户跨店403/旧5字节|`acceptance/external-original20-independent.json`|`e44f4d7b9ef883da59119765136a92e56c70d37557e03c8d81a9dae00d1e790b`|
|followup282|新postvisit/未接通后仍待联系独立|`acceptance/new-followup282-positive-independent.json`|`6f9f4b975afa19dce363adb25418be4d1134169e6f5b5095144f575e47b818cc`|
|closed277|真实旧页直POST终态409/前后同|`verification/followup-closed277-negative-v1/result.json`|`281525dc3532e84428f36efd35a5d6b350c330a015877e8dd631edbeb37055a5`|
|qr|真实原菜单/载荷一致/无业务副作用|`verification/internal-qr-locate-native-internal-qr-v4/result.json`|`42a8e2c91383326d8b48d7201b23bb992dd677706e1dc472dc990853116994a0`|
|qr-independent|4张两视口/独立完整保护|`acceptance/internal-qr301-native-locate214-independent.json`|`782bbac775a1145c59d60cff28142861a246eb6399f50b71a2508306783a7aa7`|
|http12|12实际CSV200/11字段/全部实际页|`verification/http-final-export-present/result.json`|`b3a33d63374f5b6aaad05172402975893a0e9599b3c3efc84d21450d00252036`|
|read-export-present|正常HTTP来源/导出present组合|`verification/read-export-final-present/result.json`|`eac2c51a81b5dcfa3bbe1a2431175180c8153a2e2c08ceefb10d97b82f8beb5d`|
|read-export-absent|正常HTTP来源/导出absent组合|`verification/read-export-final-absent/result.json`|`7c181d9986fee73fb074e753112716b12e52a5efe51e4924e742e6fb9337a46d`|
|permissions-independent|四组合/纯仓库/恢复独立|`acceptance/final-permission-csv-warehouse-independent.json`|`f248785ad874c05e87a5a26ed4b4e99e9ddf9837d93aa9a897bc514732aed5b1`|
|warehouse-only|正常17仅warehouse read真实请求|`verification/warehouse-only-http-v3/result.json`|`343b6d7e72ab91999107795102a30fdc9065494e1bae84df285406e83e609002`|
|warehouse-restored|正常管理恢复原有效none|`verification/warehouse-only-scope-v1/restore-result.json`|`f5bc7851b86f24817d867d517d88f55b5d26b6129a5e4c46d5e1a8ed843f8ee3`|
|export-restored|正常管理恢复5角色原有效none|`verification/export-scope-v1/restore-result.json`|`d6851098d25a2be4588768c3c2687ee7373f4c1a62e14bedec605358274de3cf`|
|frontdesk-restored|正常管理恢复8原有效none|`verification/frontdesk-settlement-scope-frontdesk-positive-v1/restore-result.json`|`40a0333eb20ac15c3bf4c5b49ecf7809e0abef1e712f16dc460f59abb6e95958`|
|frontdesk-old-new-denied|旧/刷新读写403及正常注销|`verification/frontdesk-revocation-frontdesk-revoke-final-v1/verify-result.json`|`3e4f0a9f6c465252f36104c0630c1447af0a38815b6a1ce601da0248a4cbf2b0`|
|contributions|API逐源求和旧1073/新230/全1303|`verification/report-new-source-contributions-final/result.json`|`2b4d59d0b3f6838349e7bd2022e2094e4d05547b4946e1ae04336dfb8ec50c9e`|
|browser42|42路由视口/116主截图与4额外详情图|`verification/browser-final-ux-v1/result.json`|`830242abafedc0a6af11ae273c361b612c0f2470a95306d3951a7bac76938999`|
|browser-process|实际父子0/不以JSON冒退出|`verification/process-final-ux-browser-v1/result.json`|`087a4141ebb254c185eb13a795d1f29f6b363cce1baa1c2ce81a2599656fcae8`|
|paired6|同期间同视口6财务对照|`verification/paired-financial-final-same-filter-v1/result.json`|`37b60b012728d478599480707ac59d106d73fada980c45f63f5e7a8e4a881b8c`|
|paired-process|实际父子0|`verification/process-final-same-filter-financial-v1/result.json`|`69b75019b4df2f2d0812dab5eec4e1b7eac208753bd562658c1c78877ac8f264`|
|native139|首真实139/根因UNKNOWN|`verification/browser-native-exit139.json`|`18f1e081da9513444b5edb2f5a77e6a9fece5528ef85e9b38bf12703759e4b7c`|
|native-corrective|私有依赖修复SOURCE独立|`acceptance/browser-native-corrective-source-review.json`|`e631123e45dea7073779c835b4df858eb7e8e7c98ae5adcc61fbee8be8eb2741`|
|native-bounded|无DB无登录同入口小验证独立|`acceptance/browser-runtime-probe-independent.json`|`fb6dfc59c504d984fcd46a971fbcf6be20b5620ac692a7cd8c58b4e75963575a`|
|translation-source|实现者native同中文/同DOM/原生PO|`prepared-translation/applied.json`|`65044f0a66a8f517acc2256bc2e5b68de4125c3e08c6c1224885fc2cd8f278bb`|
|wrong-scope-refused|错误S12scope页眉，未获绑定，原件保留|`verification/upgrade-ui-final-baseline-baseline.json`|`e62c78272fd40e24d897e4a84f3f3008da0f8e350f84c318cedd3a8c879763c6`|
|current-scope-baseline|当前S13scope只读基线，不授权升级|`verification/upgrade-ui-s13-final-baseline-baseline.json`|`9dffc9d975be83fbba00a27d42db0a06f60465cf6d2b82c2ae02e074fd59d437`|
|final-pure7|最终工具7PURE/实际exit0|`verification/final-pure7/result.json`|`3b5559a66fc5f4a7c2d66f7be0a168116cbedd8d38e62fd3b1d3c70f9f52ace6`|
|ui-native-source|未实现者UI5文件同中文/DOM/AST与当前scope|`acceptance/ui-s13-final-runtime-review.json`|`1d345583f5f7448d97a13c7516576701eef24eefa42d5af23735178862ad9769`|
|ui-pre|最终3模块即时RO/RR前态|`verification/upgrade-ui-s13-final-pre.json`|`72c946e61e1ed7e10217fec394038b1169126de93a8c5ab856b9d32478cbe000`|
|ui-upgrade|实际access/followup/settlement-u exit0/ERROR0/noNative|`checks/ui-s13-final-upgrade/result.json`|`0418b529eac15a610228ee67964b39e3108d98a833911010b31c5e1d7d70082d`|
|ui-post|最终3模块即时RO/RR后态/83附件|`verification/upgrade-ui-s13-final-post.json`|`30a38a1cc938f79d7225e5d2c2af8a08b42744aa4fbba2a2753e557f11a475b5`|
|ui-diff|离线逐字段差异非自动PASS|`verification/ui-s13-final-diff.json`|`cb3f9610ab90f1a8d217f88866ef0f93caf591e74b5549bdfcc2244ec9558d2a`|
|ui-load-independent|权限原值/互斥fence/元数据/83SHA独立分类|`acceptance/ui-s13-final-load-independent.json`|`4e1c0ce678ad5ef386be33297dbefe07cc713a7c46858eeb0c7e5fa45abe10c2`|
|ui-delta12|12已完成视口项；工具后在无模板fixture处exit2|`verification/ui-translation-final-delta-v2/result.json`|`accb31ca042c9c7650ff60fb8d778898353511ddd7577399a07b8464195f502d`|
|ui-delta12-process|真实exit2/signull，普通夹具错误保留|`verification/process-final-translation-ui-v2/result.json`|`e2915dfd383c6458088e10fa693f8a1a8719f69ecd19a2f842c98cbc895f921e`|
|ui-remaining2|其余2视口/实际400中文；未建权限模板|`verification/ui-translation-final-delta-v3-remaining/result.json`|`c4b942783e13ce7124a662d62167ef2c2e9351b7824a64a6292a015af18932dc`|
|ui-remaining2-process|实际父子exit0/signull|`verification/process-final-translation-ui-v3-remaining/result.json`|`76cd5b0dfed75cf9f27f2786d92ffd970faf76b91de4dfc0edf5b1928d3c0d77`|
|final-template-map|19原件/实际content版本/布局7只读映射|`verification/final-template-original-map.json`|`b8f8fb355027ecec91e4a48778d62089b53612a2aacf03a937490713b591e71f`|
|final-protection-root|最终145/13/83全部投影，独立fresh另列|`verification/upgrade-final-protection-baseline.json`|`ce48307f50440312729a8fa2824adf2a05c20f09738de40eab81c69a195d7628`|
|normal-service-stop|owned092730真实child0/signull/noNative，停止|`runs/20261024T092730Z-868987ca8c34/exit.json`|`db77dae82a7a0f2f1c068ed6fbabe26feff5fcfb7e5aa6fa98ea04ef5b2a68c2`|
|view-package-readback|只读0400/全部ZIP成员SHA验证|`viewing/package-readback.json`|`e57193a66ac1403b14d915a8ae42e62190e268d3b685afdfca10f13eaf32d893`|

|final-browser-independent|120全图/42route-viewports+paired6逐张亲看|`acceptance/final-browser120-and-paired6-independent.json`|`b9f4ec6938a7974a01c325b7618f44c3462502803d73dceda2d65acaab255ab7`|
|before-independent|14旧页面亲看/非冻结CSS条件明示|`acceptance/before14-static-comparison-independent.json`|`0fda7ab131ce4084e8c5fef545bb3ca9d270db7286f8856c5270872344bdf545`|
|translation-delta-independent|19+2图/14route-viewports及实际400中文|`acceptance/final-ui-translation-delta-independent.json`|`12e58af248a7a49dc00c6b158b8f6eeab1a8f2ea19a65a3a195441408ca93de1`|
|fresh-independent-raw|验收者另开真实物理RO/RR145/13/83投影|`verification/upgrade-independent-final-protection-baseline.json`|`aa763a8b7c40019e24c77f57d89b32e53a4fd62fc55b9a3c2672a764a87f114f`|
|fresh-independent|旧20原件/37文件/全费库款审计责任、新45+1贡献独立分类|`acceptance/final-fresh-protection-independent.json`|`25549707147b58e3f771879548f6254f6a6752502b42869ebbd1a15cc81375c3`|
|view-package-independent|222ZIP成员实际读回/36PDF/183PNG/0400|`acceptance/final-view-only-package-independent.json`|`126c9c0114458803ccd45f6fe6d918fa05f2ab87ced5b81e5aba9a085cd6a84e`|
|independent-final|未实现者总验收/必需软件缺口零，remote不预签|`acceptance/final-independent-acceptance.json`|`cf9bbc6cc4a5bd3cfda972478136add714afd0da950dfdb584177ad9664abd7d`|
|public-delta-check|全部新增Git blob+当前报告，当前provider值/强模式0发现|`verification/public-secret-check-before-final-reports.json`|`11fc3ab143254cbf539734d2d06311c42678d86341c841f759bac3de14f19012`|

## 新原件与模板/布局映射

全部19件布局为 `YD-S13-UX-LAYOUT-7`；默认code/version `YD-S13-SYNTHETIC-7 / 7`。明确选择的既有已发布内容模板或本轮正常发布的合成模板保留其实际code/version，不伪称全部内容模板改成7；原件版本另计。没有更改旧模板快照。下表均为正常新原件/后续版本，实际生成时点为UTC；没有回填成旧时间。

|新原件 / 原件版本|类型 / 源 / 源版本|前版|内容模板ID / 实际版本|纸型|生成时点UTC|PDF SHA256|
|---|---|---|---|---|---|---|
|291 / v9|consent / ydental.clinical.document:354 / v2|261|29 / `S12-consent-a4-s12-consent-summary-fdi-ready`|a4|2026-10-24 08:25:02|`b5b7601e5588d732307d63bd252b648f352b1d86f5bf8dfc7a6e41b6a62fe8e3`|
|292 / v10|consent / ydental.clinical.document:354 / v2|291|30 / `S12-consent-80mm-s12-consent-summary-fdi-ready`|80mm|2026-10-24 08:25:04|`048663c2f3206e4925201c313f20a838a6442b4ee1218081dc41d485135257b7`|
|293 / v4|receipt / ydental.settlement.payment:8 / v0|249|默认 / `7`|a4|2026-10-24 08:27:01|`acf275902f74bba65c883f205e67f956096098cefee9b55377abe75a32a46634`|
|294 / v4|bill / account.move:79 / v0|250|默认 / `7`|a4|2026-10-24 08:27:03|`217c42e9b9d1e6c9be3fef54b20a662a32dfa2be6723e45a425806ac8c94cc41`|
|295 / v7|clinical / ydental.clinical.document:273 / v3|251|默认 / `7`|a4|2026-10-24 08:27:06|`7e0d1512b6cbfb046798abd65f528539d97a81261ea0666921bab9248f0e2d0c`|
|296 / v4|exam / ydental.exam.result:22 / v2|252|默认 / `7`|a4|2026-10-24 08:27:08|`289835375c064159416149657d6610e1fc9f45ccaba9611585c49b378bbc5b9d`|
|297 / v4|prescription / ydental.treatment.order:15 / v2|253|默认 / `7`|a4|2026-10-24 08:27:10|`8e245809aeb8e82912aa9dafacd58108ae1452ee02051332e78f6911b44525ad`|
|298 / v10|clinical_summary / ydental.document.selection:14 / v1|256|27 / `S12-summary-a4-s12-consent-summary-fdi-ready`|a4|2026-10-24 08:27:12|`17ecc0e74d7cb095683f5b0507013a01bd58e50f924ded93c9310ceac182b96d`|
|299 / v11|clinical_summary / ydental.document.selection:15 / v1|298|28 / `S12-excerpt-policy-a4-s12-consent-summary-fdi-ready`|a4|2026-10-24 08:27:14|`3e543c4b628ac0f154370f85f4695367ce6cd54b331fc7003fec3dbb3a09c857`|
|300 / v12|clinical_summary / ydental.document.selection:16 / v1|299|27 / `S12-summary-a4-s12-consent-summary-fdi-ready`|a4|2026-10-24 08:27:17|`515baae41ed2785a8c28994ecd32e8fd303a172afbf18bbd68df73d2e261f560`|
|301 / v6|lab_label / ydental.lab.order:214 / v3|259|默认 / `7`|label100x70|2026-10-24 08:28:33|`e242305b294cb7a060022fffd17e4f0867968907c216575d19154d2cd979f41c`|
|302 / v1|bill / account.move:164 / v0|无|87 / `S13-UX-s13-ux-resume740-v1-a4`|a4|2026-10-24 08:29:31|`df5ac41ba01e4f84e4e3fc1673122325f94386b86c92e25019900e8d3212e08b`|
|303 / v1|receipt / ydental.settlement.payment:30 / v0|无|88 / `S13-UX-s13-ux-resume740-v1-a4`|a4|2026-10-24 08:29:40|`3f888fc3108c51f5bd05fd6dd14da9c80fd77f87a3262b11e11a801e97256062`|
|304 / v2|receipt / ydental.settlement.payment:30 / v0|303|89 / `S13-UX-s13-ux-resume740-v1-80mm`|80mm|2026-10-24 08:29:42|`fb0d495012108f2ce9f0c4041a6ef13699b01894a25a5c30f38a46fad9837d54`|
|305 / v3|receipt / ydental.settlement.payment:30 / v0|304|88 / `S13-UX-s13-ux-resume740-v1-a4`|a4|2026-10-24 08:29:56|`b478bb0230e72882570db1ee1af3fd2d4c84d8ac79d01232b70b9a3af82841e2`|
|306 / v1|refund / ydental.settlement.refund:11 / v0|无|90 / `S13-UX-s13-ux-resume740-v1-a4`|a4|2026-10-24 08:30:03|`75915fc4ea2f59ce3229e1246cfefa306fd079e63eb633450c64fa4de8b3a2ec`|
|307 / v2|refund / ydental.settlement.refund:11 / v0|306|91 / `S13-UX-s13-ux-resume740-v1-80mm`|80mm|2026-10-24 08:30:05|`5c44f7eca6ea4ef09f9c479865f3b07167760936f28c0799dee11dc86953ccbd`|
|308 / v1|lab_label / ydental.lab.order:215 / v2|无|92 / `S13-UX-LONG-s13-long-label-v2`|label100x70|2026-10-24 08:36:13|`e98b9eba8bab7a3aa5a7cec67dfb8183aa05d0351df0ed8dc663f8072f52fdf3`|
|309 / v1|clinical / ydental.clinical.document:508 / v1|无|默认 / `7`|a4|2026-10-24 08:44:28|`b2d813eb1e4477aeb40810550f7fbd184a524aabc8be1cd1599441d70fe4a4e3`|

## 私有只读效果包

`.local/s13/viewing/S13-UX-view-only-20261024.zip`，49275591字节，权限0400，SHA256 `761163a3d8b9e16265561b1db151d8051dfcbe079e65af333e7186184901b01e`。正常读取归档并逐件比对全部成员；19最终PDF/32页、17旧PDF对照、183PNG及README/派生审阅索引/manifest。未装入26个中间迭代文件不等于删除；它们仍在原库及私有证据，独立逐页失败/修复结论保留。

前态14图有已记录静态资源条件限制；整套120图为最后纯翻译前的等价业务候选，再以新候选14路由/视口补覆盖受影响页面。v2工具的12项完成后因“没有权限模板”的夹具断言失败，v3只补其余2项及真实400中文，不改原exit2。不存在模板未新建权限政策，预览ARIA采用实际已加载视图/翻译层核验，不声称做了不存在模板的浏览器预览。

本批仅软件二维码解码/被动正常内部码定位。浏览器自动化不代表用户亲手验收；生成/下载/打印请求不代表签署、正式开票或实机出纸。

## 最终同步

正常push/ref、main仅文档路由及#37唯一最终评论读回待末次追加。当前SYNC_PENDING；#37仍须OPEN，#36保持CLOSED。
