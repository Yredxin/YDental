# P14 结构调整验收矩阵

|项目|结果|实际证据及限制|
|---|---|---|
|五列及账单信息|SOURCE PASS|原表格、字段和分页表达式保留；真实岗位单账单 GET。|
|唯一表单与对应|PARTIAL|SOURCE 和 loaded QWeb 双账单合成通过；真实岗位仅一笔。|
|表单字段、权限、取消|PARTIAL|SOURCE 原表单相同；真实写/只读及内存 FormData 通过；真实多账单、真实 PDF 权限未测。|
|T09 键盘焦点|FAIL|真实 Chromium 9组合中3个新增锚点轮廓被表格滚动框裁切；不能以转焦点横滚替代。|
|双浏览器、五视口、两种200%、JS开关|PARTIAL|简化静态合成矩阵有两引擎；真实页面仅 Chromium JS on 的9组合，不混签。|
|真实资产及页面|PARTIAL|候选 frontend CSS HTTP 200；真实写/只读单账单 GET；全场景尚未完成。|
|P12/P13与后续办理|PARTIAL|冻结区源码不变；本候选真实代表性回归未完整采集，P12 A04 原失败保留。|
|保护与审计|PARTIAL / UNKNOWN|升级前后34表摘要相同但前像未独采；HTTP后附件具体变化 UNKNOWN，审计新增32条；未发经济 POST。|
|独立验收与资源|PARTIAL|未实现者独复 T09 FAIL、对象与容器停止；测试岗位仍 active、Session 未测。|
