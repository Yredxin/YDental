# S06-A修正安全自复核

这是Codex使用odoo-security及适用odoo-guidelines/odoo-web-guidelines的工程自查，不代表GPT技术PASS或用户验收。范围仅review6117074066的四个BLOCKER、关联测试/runner和UI；[原安全材料](s06a-security-review.md)继续保留。

|扫描/边界|判断及最小控制|
|---|---|
|actor/多店围栏|统一查询未解决execution，serving和verify均约束真实lease actor；进入/call/start均拒绝同actor再执行，S01 store fence优先execution。新session/目标店有membership及write也不免除围栏。GET只读，不执行自动完成。|
|统一资格|entry、当前task mapping/reporting/execution area/catalog能力/人员权限均从固定服务器记录取得；合法祖先链同店且有效。call/start/UI共用helper；start再次校验，不能以call时结果续权。|
|资质来源|产品private hook默认False且仅接受严格True。测试冻结Source及object写入身份仅在库名/运行环境guard内；无普通ACL，无客户端资质标志，无真实资质表空壳。RPC直接创建/JSON context/dict伪造均有负向验证。|
|sudo|新增actor execution查询和eligibility读取仅固定模型及已限定actor/task/station；没有任意模型/字段/domain或request vals透传。actor参数仅server调用，公开POST不接收。|
|with_user|唯一新增产品切换为固定base.user_root，仅用于不可变timeout审计准备/创建，不调用业务授权、不持久修改用户、不接受请求actor。after仍记录实际holder/station和结果。|
|SQL/锁|无新增产品SQL或账号锁；原四业务fence及RR锚点不变。跨店拒绝在业务动作锁后再次校验；产品无commit/rollback；真实脚本只提交自身独立cursor。|
|missed/order|服务器call rank/order字段不可普通CRUD；N在call前fail-closed。区域混合能力及其他live call锚点共同参与排序；fault只恢复，不记真实missed。|
|audit|请求/cron共用自动化actor与source；并发只生成一次timeout事件，after保留holder_user_id、lease、station及call/execution结果。不同用户碰巧触发不承担该自动事件actor。|
|HTTP/RPC/CSRF|原auth=user、POST、CSRF、16KB上限和固定schema保留；新增无公开route/action，无管理员强抢/接手/核实完成出口。原32项模型/HTTP负向仍回归。|
|XSS/静态|state_label和eligibility原因均静态翻译字符串，通过t-out/textContent输出；无innerHTML/Markup/t-raw。JS只保留服务器禁用状态，不承担授权。|
|字段/附件|两个排序字段是受控entry事实，无token或患者新增敏感数据；既有secret NO_ACCESS和附件阻断未变。测试provider无普通读取/写入ACL。|
|文件/反序列化/复杂对象|产品未新增open/eval/exec/pickle/getattr/setattr；私有资格hook返回布尔值，eligibility返回字符串，status返回普通字典。令牌比较consteq及摘要持久化原样。|
|证据/运行|只全新隔离S06-A库和合成数据；端点/cluster/OID/config/data/log/dbfilter/PID/port/外发guard保留。原失败链不覆盖；原始日志/config/access/cookie/token不发布，浏览器默认sandbox。|

适用扫描覆盖原产品全部命中及新增差异；细节、实际方法、竞争、Firefox和失败链以修正报告及固定证据为准。execution终态/历史部分唯一、原生账号logout整合均按review留后续授权，不以此次修正提前实现B/C。全局串行锁正确性不代表S13性能通过。
