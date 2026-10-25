# DL-P7 逐项验收矩阵

YD-S13-DL-P7 / 1.0。当前为验证中草稿，无动态缺项预签。产品f3f8e6114bda27eabc18140d60bd9b8eb044e99e；实际运行工具候选和最终原件按索引分别固定。

|项|必需断言|当前真实层级与结果|
|---|---|---|
|T01 覆盖/边界|全部目标族、精确主路径、旁路无污染|独立SOURCE PASS：43节点/13族合同，catalog/error原文保持；before六旁路已采，after待验|
|T02 风格/状态|统一tokens/default/hover/active/focus及分层disabled/busy/danger，实际对比|SOURCE入口齐；COMPUTED/BROWSER待验|
|T03 SVG来源/安全|固定tag/commit/原SHA/ISC+MIT、最小子集、安全静态|独立SOURCE及官方上游bytes/SHA PASS，七几何同源；运行待核|
|T04 语义/操作|原元素、中文/名称/焦点、图文/Enter原GET|before普通链通过；after真实SVG点击/AX待验，不冒屏读|
|T05 响应|五视口/长中文/根无新溢出/九列不改|before五view通过；after产品+组件待验|
|T06 双引擎/放大/无JS|两真实引擎、各native200/root200、无JS|after待验；不以UA/模拟器冒第二引擎|
|T07 读取合同|q/event/page/anchor/行集顺序/三数量/flags不变|SOURCE及before真实查询/来源/30+20页已采；after与原P6明确复用待核|
|T08 办理合同|13族条件/字段/submitter不改，真实开合取消，序列化只内存|独立SOURCE完整XML还原exact PASS；before9可见族开闭焦点无POST；13族loaded QWeb/内存待验|
|T09 角色/旁路|普通读写/无源拒绝，catalog/error/P1/P4/P5隔离|before六角色场景已采；none403不冒库存action-error，后者SOURCE+明确QWeb组件待验|
|T10 故障可用|缺图/无CSS文字原元素、nativefocus/forcedcolors/reducedmotion|后态明确组件及支持范围待验|
|T11 加载/保全|即时pre/exit/post，最终独立业务+全部文件保护、0新经济库存/scan/原件|独立初始physical266501/145业务13技术83实际文件九区同P6final；加载/final待验|
|T12 独立交付|固定源/原图/请求/退出/包/保护、实际收尾与最终同步|SOURCE已签；动态/包/总签/远端待验，最终技术/同步/用户分列|

接受冻结业务实现+合同不变+旧实证复用+本轮只读/组件组合；不执行live确认或scan POST、不补造缺状态、不称业务重执行成功。缺必需实证则PARTIAL。
