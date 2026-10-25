# DL-P5逐项验收矩阵（PARTIAL）

产品/运行固定 `beea6d3dc9223fa06d298984b80cb463f2fcafea`，core f0c5a9b。普通结算UID14/store1、HTTP reader16/none17。SOURCE/PURE、QWeb内存组件、HTTP、真实浏览器/nativeAX、已提交RO分层；没有用主控自签替代末态独立验收。最终缺口见T07/T08/T10/T12—T14。

|项|预期与实际|层级/证据|独立判断及状态|
|---|---|---|---|
|T01 范围冻结|四addon文件，prefix2150/suffix22764/shared分页原字节同；原GET/字段/href/foreach不变，无JS或后台变更|SOURCE/PURE，source-product1-independent|PASS，未实现者已实际核|
|T02 字段范围|q/规范patient分离，未选店范围；原三段集合/序/金额币种日期/患者号actor原因trace表达式保持；无总额|SOURCE＋真实Chrome原投影；独立290项比较|PASS；today/pending真实空，非空只QWeb层|
|T03 搜索|真实姓名/号/中文特殊字符/原生Enter与按钮/max100；输入失焦不GET，不自动选人；选中后draft不改上下文|core、native-querytop-v2、16HTTP；键盘协议非真实OS IME|已采断言PASS；不签未测OS输入法|
|T04 选择分页|原patient-only、两URL helpers/参数/边界保持；真实一页；19项原QWeb共享50门槛/候选has_more组件通过|BROWSER＋HTTP＋COMPONENT_QWEB；http-zoom-nojs-qweb-independent|PASS，组件与真实一页分列，不冒真实多页|
|T05 只读语义|三段默认可辨、待核对/禁止出账可见；空态非结清；原trace键盘无请求；他店最小摘要真实200|SOURCE＋BROWSER＋QWeb原因回退/转义|已采分项PASS；待核对非空浏览器另缺T07|
|T06 视觉对比|A色/1rem/1.6/1.125rem，真实computed54样本文字min4.7563、必要边界3.3191、focus7.0613|独立原图/数值重算；非全站认证|PASS，限定Chromium已采条件|
|T07 五视口长值|五视口真实前后字段/根宽保持；320实际320；三段内存长值QWeb已渲染，浏览器长值/末字符横读未执行|BROWSER真实普通值＋COMPONENT_QWEB|PARTIAL，缺非空/长原因浏览器组件验证|
|T08 放大语义|Chrome原生zoom2/root16及独立root32分别通过；nativeAX与原生table/label/details；补query-top原图|zoom-final-v1、native-querytop-v2、core AX|PARTIAL，Chrome已独立核；缺WebKit放大|
|T09 角色权限|普通reader可读，none17无源403、现存无本店关系60与不存在目标403；非法页/id/q拒绝400；0grant|16真实HTTP=4x200/3x403/9x400；原源码及旧通用撤权证据复用|PASS，独立核HTTP原记录/执行源；非本轮通用撤复全验|
|T10 零副作用能力|原bill展开后取消，无settlement/action/PDF等请求；原合法能力/字段/条件冻结；root末态原经济业务与文件保持|SOURCE＋BROWSER＋root全145/13/83；正常949访问审计另分类|PARTIAL，已采行为通过；缺最终独立完整保护|
|T11 旁路冻结|P4真实单选确认取消/多店草拟不改effective，P1—P3只读无preview/PDF；结算后缀内部computed前后同|bypass-final-v1、冻结比较/资源全scoped|限定代表检查已通过；未重跑历史全套；末总签未完成|
|T12 两引擎无JS|Chrome正常关键链/无JS同禁JScontext正常认证后原生链通过；WebKit27.2 preauth资源404，client2/native0，未进入结算|成功Chrome＋真实失败WebKit v1；root同URL200/原技术文件另证|PARTIAL，缺成功WebKit；不能用UA或Chrome替代|
|T13 加载保护|唯一settlement-u完整pre→实际0/ERROR0/noNative→post已独立核；新资产524139B/SHAa6a1f234…实际200；root末态完整145/13/83同业务保护，metadata/audit分类|load-protection-independent及root新RO末态/资产|PARTIAL，加载独立PASS；最终完整保护独立复核缺失|
|T14 收口独立|已有分项独立回执；私有包34PNG/39成员主控全bytes/decode核；正常服务/浏览器/profile收尾；最终技术/包/末态独立验收缺|已采9client含7×0/1×1/1×2；最终独立未执行|PARTIAL；首两ref/21正文/唯一评论已实际读回，末元事实另核；不以同步补PASS|

测试线程平台用量限制退出；当前没有可用独立线程。旧服务窗口06:49:51UTC正常到期、现有独立准入超过30分钟，launcher原生拒重启；不绕guard、不新建线程规避额度、不伪造独立review。可恢复正常资源后针对缺项补验P5，不启P6。

用户亲手效果待确认；Safari/iOS、实机、屏读、真实OS输入法及正式政策未验。P1—P4原结论保持，#37 OPEN/#36 CLOSED；产品合并、部署和生产未启。WebKit/Native139/Firefox等旧UNKNOWN不追溯倒签。
