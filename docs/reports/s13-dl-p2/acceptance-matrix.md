# DL-P2逐项验收矩阵

产品`a0b33c14c121f2a489fdcf7abc529999fd15c1dd`。SOURCE、真实浏览器/HTTP、独立已提交RO分别列；不重跑历史业务，不冒用户亲手或实机。本地适用软件已获未实现者总签4e4b6b2c…；远端同步尚待实际执行，不预签。

|P2项|真实层级|预期与实际|证据（私有索引下）|结论|
|---|---|---|---|---|
|T01|SOURCE|4 addon产品文件、限定阶段工具/文档，保留原补记，P1/backend/ACL/PDF/core不改|product/source-check-v2.json；acceptance/final-runtime-review.json|PASS|
|T02|SOURCE+BROWSER|标题/用途/7新译文及3条逐字移位说明准确，默认可见，无伪状态/新动作|product/copy-map.json；最终两引擎实际图|PASS|
|T03|BROWSER|5原href/标签保持，3+2语义列表/真实Tab与暖色焦点，无自动请求|chromium-core-v1；webkit-core-v2|PASS|
|T04|BROWSER+独立公式|实际A色default/hover/focus；14组文字最低5.613，5焦点最低7.061|acceptance/chromium-and-comparison-independent.json|PASS|
|T05|双引擎BROWSER|5视口自然换行/关键内容无裁切；改区不新增横溢，旧320/345保留|after-final-v1；webkit-core-v2|PASS|
|T06|双引擎BROWSER|真实native200%与root32分别验证；WebKit两正确viewport覆盖214/214字符片段|evidence/webkit-native-zoom-visible-v1/result.json；独立WebKit图核|PASS|
|T07|BROWSER+HTTP|正常菜单/搜索/两select Esc与确认/Tab/显式preview200，字段唯一/选择无请求/P1窄popup保持|chromium-core-v1；webkit-core-v2|PASS|
|T08|BROWSER+SOURCE|标题/nav/阅读顺序；未新加details；P1帮助/错误ARIA保持；JSoff原生表单预览可用|chromium-fallback-v1；core ARIA|PASS|
|T09|SOURCE复用+定向BROWSER|后台源权/revision源码不变，复用P1固定拒绝实证；有源/none显示准确，不冒新撤权全验|chromium-none-v1；P1固定HTTP/revocation|PASS|
|T10|同条件BROWSER+SOURCE|11对字段/computed，3旁路PNG同SHA；只排除真实动态key；预览全文不可比，可见正文及摘要同|before-after-final-v2.json；独立可见iframe检查|PASS|
|T11|原生加载+独立RO|首限定print-u0/即时prepost；最终SCSS-only不重复-u，145/13/83全核、64审计/技术差异分类|final-protection-independent.json；baseline-to-final-diff-v2|PASS|
|T12|双引擎+独立收口|Chrome156/WebKit27.2实证及正确zoom图；私有包/7步/真实正常停止已齐；远端同步待实做|WebKit/保护/包独立核；远端实际读回待补|LOCAL_PASS / SYNC_PENDING|

T06 WebKit首locator错图未通过，已以同候选正确viewport补图替代视觉主证；旧图不反签。T10 before未存全文，不证明差异仅限原生提取时间。T09后端拒绝基于源码不变和P1真实固定证据复用，none shell200不是403。

屏幕阅读器、真实OS IME、Safari/iOS/设备、用户亲手、完整S13及生产未验/未启；Firefox/Native139 UNKNOWN保留。
