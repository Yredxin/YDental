# P14 验收矩阵

状态仅限下述实际层级；PARTIAL 不等于全项通过。

|编号|结果|证据及限制|
|---|---|---|
|T01|PASS / SOURCE|产品三个允许文件，QWeb 限未付清 section，独立 diff 和 C14N。|
|T02|PASS / SOURCE，PARTIAL / 合成 QWeb|五列、顺序、取值及分页表达式不变；无真实岗位带账单 GET。|
|T03|PARTIAL|空态、只读与正常内存合成 QWeb 分支；真实可写/只读权限未验。|
|T04|PARTIAL|SOURCE 属性及顺序一致；双浏览器合成 FormData、submitter；真实令牌与真实岗位未验。|
|T05|PARTIAL|原生 details、Space/Enter 与合成 href；真实取消导航及完整真实页面未验。|
|T06|PARTIAL|局部共享 mixin、SCSS 编译及合成截图；真实 frontend bundle / HTTP 未验。|
|T07|PARTIAL|双引擎、五视口、三种缩放及 JS on/off 有合成 QWeb 和简化外壳证据；真实岗位页面未验。|
|T08|PARTIAL|长单号金额单行、300字与横滚有合成证据；焦点裁切见 T09。|
|T09|FAIL|Tab 焦点可被横滚容器裁切；转移焦点手动滚到两端不能代替聚焦可见。|
|T10|PARTIAL|冻结区源码不变；真实最终页面影响回归未完成，P12 A04 原失败不改写。|
|T11|UNKNOWN|无经济 POST；未做本轮历史库独立前后物理读回，不能声称全库或全部保护对象无变化。|
|T12|PARTIAL|固定候选、独立复核、证据及自有资源停止；真实权限、资产、保护与完整焦点验收未完成。|
