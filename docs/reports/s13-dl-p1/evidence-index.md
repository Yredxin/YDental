# DL-P1脱敏证据索引

所有原始材料只在本机忽略的`.local/dl-p1`；Public仅代码/设计/计划/脱敏报告与本索引。以下是实际文件完整SHA256，不包含凭据、Cookie、session、连接配置或原始请求正文。最终产品/执行8dea2647760f6d6738abfc9db132cfa9d7feaee3，公共运行工具31ef；私有验证工具按实际源SHA归档。最终与63ae初版证据分层，旧长项真实FAIL不反签。旧before候选31ef的addon仍为06c7基线。层级不能相互替代。

|层级|私有相对文件（`.local/dl-p1/`下）|SHA256|真实范围|
|---|---|---|---|
|最终BROWSER|`verification/after-final-v1/result.json`|`b89e74e675294368ebaebb469a978c76b0296f03e6bd0a05c3ef78eff2c8b175`|8dea最终15图+2真实iframe裁剪|
|父/子退出|`verification/process-after-final-v1/result.json`|`c7ec64239187fa1cde06deb3ca8db92d49ed591dae70f64398d596ec0e40706c`|最终产品实际0/signull|
|最终前后|`verification/before-after-final-comparison.json`|`75511e87ed213be2d75ab6c47ae8f8afcce182493bb4de81bdecd6392b13e946`|15对未改区computed同/3旁路PNG同SHA|
|最终BROWSER|`evidence/controls-final-chromium-core-v1/result.json`|`529231be02f0b6f57e613d2d8219714cc915330ee1bdcbdab2c806aa624b1dd6`|8dea核心/真实preview/键盘/AX/busy；有效截图另选|
|最终BROWSER|`evidence/controls-final-chromium-popup-v1/result.json`|`a52bb4cfb08400e4ea87b1273a628a67c03561f891bf5eba06c89d7483769e32`|5视口+nativezoom/rootfont7真实展开图/真实computed|
|最终BROWSER组件|`evidence/controls-final-chromium-long-v1/result.json`|`c2dbf9378aa9505e5f34dd7c435bbe2cf2bc8363ee7f726126cf662e7d219374`|8dea长项完整Range/局部滚读，旧3白图不签视觉|
|最终BROWSER补图|`evidence/controls-final-chromium-visible-v2/result.json`|`8366f5f5801bc3a1f170693e1e52222dde80fd0c0dda6a7b98886882e9ba865c`|320实际viewport fallback/nativezoom原生CDP真可见图|
|最终独立视觉|`acceptance/final-chromium-and-after-independent.json`|`052aae29c5d1a0761f54c6aa6b9eff8b6d1103f15c64f0da88782ef16da1f187`|最终core/popup/long/17after实际逐图与复用同SHA|
|最终独立长项|`acceptance/final-chromium-long-visible-independent.json`|`363abf7ff2f5177df0d68ea279afdb028ee48db409f1287ad19f1e91b2adab93`|8dea修复旧14/26px缺陷，原白图不反签|
|最终WebKit应用|`evidence/controls-final-webkit-keyflow-v1/result.json`|`817ef757551f77fe865a31d6189407cf9174da210f02cd5f86cf9606ed0fc5cb`|真实27.2普通9/menu/search/选取消/显式preview/3视口，原clip图不签|
|最终WebKit补图|`evidence/controls-final-webkit-zoom-capture-v2/result.json`|`3139b6b47bd26f0103428a2e0ad02885f5cc89eb73a2432f65991b380121ce73`|正确原生zoom2完整viewport实际图/主进程0|
|最终独立WebKit|`acceptance/webkit-final-application-independent.json`|`b4619566cbd85a8cef18e1d122e4c2bcc551d209ef0b9b631f0962dbc18b194b`|真实应用及正确zoom图亲看，T14限定双引擎软件|
|工具作者选图|`evidence/tester-selected-screenshots.json`|`e117af0c039f61e907c9ed0ba1bd43697fa3f4aadd03c717dbe25a71fe240561`|最终8dea40图，排原缺陷/白图/错clip，不是独立签字|
|首次长项FAIL|`acceptance/long-fixture-visual-failure-independent.json`|`5eef89bd40da8f5b4286877e33b759267b728c3a4f45b56c29d84b06223be428`|63ae真实14/26px候选不可读，保留不反签|
|第二引擎原失败|`evidence/webkit-native-capability-v1/result.json`|`618c216fc274b7de3c23f21b028f95a45fa273da499a82b762559a620ae028f9`|原TargetClosed元数据缺口UNKNOWN，无app/auth/DB|
|原生诊断|`evidence/webkit-diagnostic-once/result.json`|`618c216fc274b7de3c23f21b028f95a45fa273da499a82b762559a620ae028f9`|同环境DEBUG见EGL platform缺口，renderer信号未知|
|私有普通依赖|`acceptance/webkit-mesa-v2-source-independent.json`|`eec4dbdeaf4ecb58415b641219b831134f650250bfe114fbea2df09f7350d69c`|official Mesa vendor库/JSON逐字/hash/ldd，无控制变更|
|依赖后明确缺库|`evidence/webkit-mesa-capability-v2/result.json`|`7b41b484c035508e5e940c177f94c9365cb825f9c475f969f4b2b2a170253234`|actual2/main0，原生缺GLES，未冒appPASS|
|私有普通依赖|`acceptance/webkit-gles-v3-source-independent.json`|`2a3b893d704ce80dcc37006a330df4fdcec8483735fe5d571f1806fce07d2e1b`|official GLES库/ldd，与原context/API/控制不变|
|真实DATA能力|`evidence/webkit-gles-capability-v3/result.json`|`43e737c46348a6e12b41ecc191f2e9154be68f1a2f35448d7d443c6e24238afd`|实际0/main0，CJK/nativezoom2/reset，非app证据|
|独立DATA|`acceptance/webkit-gles-v3-data-independent.json`|`91303e51938f7bf3df7519a13ce91e12f988dc73e4fc02006f38dc5af6e30d12`|两真实DATA图片亲看，不代应用验收|
|正常停止|`runs/20261024T113302Z-ca515f78a9f8/exit.json`|`0c913ad015cdca5da795717e1eb15a7d244c499700b2b4a5b3ff327868f8c065`|末owned Odoo实际0/signull/group stopped/noactive|
|SOURCE/PURE|`prepared/source-check.json`|`ae069f841bd8db262e3d45154df97070196168a600315550e895d1c16f7d6301`|AST/XML/PO/Odoo transpiler/libsass/Node|
|SOURCE/PURE|`evidence/popup-fallback-source-check.json`|`b8b34e83f16f3ff89476cc3db6287c9b53105255e9b5ec7e4c73a3beed421c6b`|8dea JS-only open/setActive修复；动态另验|
|SOURCE/PURE|`evidence/component-source-map.json`|`1e91f386e11c61fae746d3501fbdf87634082a0bedb066e91eb53cb4ef6bc997`|实现者映射，不是独立签字|
|独立SOURCE|`acceptance/product-v1-runtime-review.json`|`6c640c0bf6633a6a1bb2fe5c1846c64716f0dd33064b0fb5e1201b373905f01f`|产品范围/原生能力/精确候选准入；不是动态PASS|
|独立加载|`acceptance/product-v1-load-independent.json`|`e92b30b3cae680121e0c5f7a428249910b416a7b4f26ef2cd865e64fb50a9dc0`|限定print加载实际0及即时完整pre/post分类|
|旧BROWSER|`verification/before-v1/result.json`|`2b994d01730a525a42d9fc82eb2691c121004a89c2a2e925d2ce76fa9e937124`|纯旧产品15图，非新版证据|
|父/子退出|`verification/process-before-v1/result.json`|`7f67ba349c61f3ab15c3eb5740813b150f3d515b4c47912a9a6539d286cdc0b2`|旧图实际0/signull|
|新版BROWSER|`verification/after-v5/result.json`|`79cf11a8407fcb427478bdf778d638459025f8493c8c46fa5094bec6c26310a9`|15图+2实际可见iframe裁剪|
|父/子退出|`verification/process-after-v5/result.json`|`8c3424cf4b086248733e38a2b67ba15562d29da015be014bfa52d3c5b2dfa4f0`|实际0/signull|
|前后离线|`verification/before-after-comparison.json`|`e1f0ebbf6680f1126b89d57eaef5401236d1878800011d4b00dc5270b09d7971`|15pair未改命名区域computed同/3旁路PNG同SHA|
|独立视觉|`acceptance/before15-independent.json`|`17f187acb11885a740f8d7aa4c638971efcfc4dbeef7d3aa8f9562bc5c67a9df`|全部15旧图亲看|
|独立视觉|`acceptance/after17-and-comparison-independent.json`|`179e8e5d7a4605eb0771a59f4cc9a58979c1fc0aa137634c458eccc4a5ef74c8`|全部17新图/旁路与时点差异亲看|
|HTTP|`verification/http-v5/result.json`|`b53f42209c0cfb522dd67963f8fad42232c4fdd554874ba952f96d28447a489e`|17类正常表单/权限/旧revision/原件下载|
|父/子退出|`verification/process-http-v5/result.json`|`cc448d3da84fe884fd73bc31509494374d0422c33d8be2f65fa9d8c7914f428f`|实际0/signull|
|已提交授权负例|`verification/revocation-v2/result.json`|`5d950ac8d731401f3a90b0d0c378d62096e1b56bb324e6af080f8e8af895cf27`|正常9医疗撤权/同旧页拒绝/精确正常恢复，独立物理RO每步|
|父/子退出|`verification/process-revocation-v2/result.json`|`3c843b8922e53a97495f4f30fc24865a66a3dcef4f1a5bc3195b4dce687c8c24`|实际0/signull|
|独立HTTP/授权|`acceptance/http-revocation-independent.json`|`2a1c2540a3744b53e884789c54c485345dded8763d7846aca77ea17a60520bfb`|原始请求收据/独立物理投影离线复核|
|BROWSER|`evidence/controls-chromium-complete-v5/result.json`|`88cd75f17d9721ca7d848fb8621605105bdad49d7f4c9ea2c806442b409ed62d`|核心交互/真实preview/IME/AX/真实zoom；其中全页popup图不用于视觉PASS|
|原生AX|`evidence/controls-chromium-complete-v5/native-ax-tree.json`|`e598ad7ff5b4c1bae119d2a7f3a72ae0a247804876f2f0a78289d9df7cd0d077`|293原生AX节点/真实关系；非屏幕阅读器实测|
|BROWSER降级|`evidence/controls-chromium-native-fallback-v2/result.json`|`4f536b270bd6e9741a73d0e2912c15b052284982bb0bc1350aa226c3ec5f8faf`|JS禁用，正常同context HTTP认证+原生查询/选择/preview|
|BROWSER|`evidence/controls-chromium-popup-capture-v1/result.json`|`6fbe84d680e356be6c79399faf742b4304852d80335db4253caf58d837382c69`|7真实viewport展开图+14组真实computed颜色|
|独立视觉/公式|`acceptance/chromium-popup-contrast-edges-independent.json`|`934a531ac7ab2f4ff13fdf034785a2765dd887d2a4d09874f513a9a83306cf53`|7图亲看/14组独立重算/edges-touch-none层级|
|BROWSER/组件|`evidence/controls-chromium-edges-v6/result.json`|`275a0f8e3626f35f4118ac5821b5173e4e3eed965c5058a07b2f205f8092be4f`|外点/滚动/resize/reset；组合typeahead事件夹具明示|
|BROWSER模拟|`evidence/controls-chromium-touch-v1/result.json`|`22122c3ea4723d5d67281b104b6fc7bd53c44d12fa7a886b13b21560c743528f`|触摸模拟，非设备|
|BROWSER|`evidence/controls-chromium-none-shell-v1/result.json`|`a253a0cb4957b312f00c9810a021dc9e6a9082658d6d4e7d8d6857c02073a9dd`|真实无源shell200/disabled，不冒403|
|BROWSER组件夹具|`evidence/controls-chromium-long-fixture-v4/result.json`|`2a1b54ee4a330b15cfeadb856f959b96e277f644079c812f814c14703c456747`|正常响应文本替换，仅标签/错误；原业务value不变、不写库|
|BROWSER组件补图|`evidence/controls-chromium-long-fixture-capture-v1/result.json`|`952ebb78c081b131cbd0cc4fbe830e9bcc3e36c9b232f896883ac46b79734901`|长项viewport真实展开/zoom与根字号分列|
|Firefox实际交互|`evidence/controls-firefox-controls-v5/result.json`|`d3eb85fff83d87fdbc7cdf36bacd5c55d1718f154a65dd790f7f0d6df0db6c71`|真实交互/原生fullZoom2；中文tofu视觉不通过，不能总PASS|
|Firefox原缺口|`acceptance/browser-initial-partial-independent.json`|`911321baadf1bbdbbbb42125509af0efda8def231672705cddc7e85d02f89222`|旧Chrome截图/Firefox中文缺字真实PARTIAL保留|
|工具作者索引|`evidence/tester-browser-index.json`|`0a6984e20d93944f6ee3e5c92bfd8f8e4afaec6a5c5ccd247974f1648c4cb01b`|每轮源SHA/真实退出/图片及原失败；非独立验收|
|ROOT最终保护|`verification/upgrade-final-protection-post.json`|`ece0dfc088475222f57cb3ee912475efe52347d193e6afafadc67c43a7817f55`|145业务/13技术/83实际文件，正常读/授权/资产差异分类|
|ROOT离线差异|`verification/baseline-to-final-diff.json`|`f285bcdabe74e7c39838b2c255242f24769ae64dc513ac0b4e45b7cbf900ffe8`|跨候选全P1比较，非同轮upgrade；保留原snapshot状态与合法祖先|
|独立最终保护|`acceptance/final-protection-independent.json`|`0b5d0d276abddfb740d6347529019b134d61e5e537cd26a42ce61d60cc99465c`|未实现者新物理RO与原始文件逐值对照|
|独立总验收|`acceptance/final-acceptance-independent.json`|`7286c7ad8fd7af8774da6dfb671826843c26cbbad7cd471bfff9ff3e7ff56b9c`|全部P1适用断言和真实限制|
|独立私有包|`acceptance/view-package-independent.json`|`93821599c06abadc384fe0321565cfe8fb6ac828b10d1c40805ecc415e9aab40`|只读包逐成员/SHA/无秘密/真实图片核|

`tester-browser-index.json`为工具作者索引；独立验收者另签实际读取的receipt。旧非零/缺字/全页截图关闭浮层均保留，最终替代证据不能反签旧失败。源码、HTTP、真实浏览器、组件夹具、模拟触摸/CDP IME、原生AX、独立已提交RO各自分层；真实OS IME/屏幕阅读器/Safari/设备/用户亲手仍未验。

最终私有包SHA/字节/成员清单、独立总签与报告HEAD/正常停止/实际同步见summary。旧Firefox视觉未过、WebKit前期失败与renderer UNKNOWN不反签；最终适用多引擎为Chromium156.0.8078.4+WebKit27.2，不声称所有平台通过。
