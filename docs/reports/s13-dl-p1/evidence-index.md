# DL-P1脱敏证据索引

所有原始材料只在本机忽略的`.local/dl-p1`；Public仅代码/设计/计划/脱敏报告与本索引。以下是实际文件完整SHA256，不包含凭据、Cookie、session、连接配置或原始请求正文。最新产品8dea2647760f6d6738abfc9db132cfa9d7feaee3，尚待动态复验；以下已采63ae初版证据分层承接，长项真实FAIL不得总签。旧before候选31ef的addon仍为06c7基线。层级不能相互替代。

|层级|私有相对文件（`.local/dl-p1/`下）|SHA256|真实范围|
|---|---|---|---|
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
|工具作者索引|`evidence/tester-browser-index.json`|`34e6ee169f8463518a8e230c9ea98f7cdae78fc59259c68fbeb653d29b038294`|每轮源SHA/真实退出/图片及原失败；非独立验收|

`tester-browser-index.json`为工具作者索引；独立验收者另签实际读取的receipt。旧非零/缺字/全页截图关闭浮层均保留，最终替代证据不能反签旧失败。源码、HTTP、真实浏览器、组件夹具、模拟触摸/CDP IME、原生AX、独立已提交RO各自分层；真实OS IME/屏幕阅读器/Safari/设备/用户亲手仍未验。

最终私有包SHA/字节/成员清单与报告HEAD、正常停止和同步事实见summary；未完成事实不得藏入总PASS。
