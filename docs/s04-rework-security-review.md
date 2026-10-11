# S04 定向返工安全复核

范围是[#28 GPT-REVIEW6114781429](https://github.com/Yredxin/YDental/issues/28#issuecomment-6114781429)两个BLOCKER。产品固定`887d0a9772a9ee165992ccd77af87fbb2c287d93`；补充[原安全复核](s04-security-review.md)，以下为Codex工程复核，不代表GPT技术复核或用户验收。

## 记录级读取和必要行政资格

`res.partner._access_domain('read')`在Odoo原域上取AND，无资格只返回owner=False。每次direct read/fetch重查资格，不能复用已缓存的合法读取。主联系人、监护人及历史保留partner共用owner边界；field groups没有承担记录级控制。测试预热sudo缓存并随后撤权，读和查询仍拒绝。

`_can_read_patient_partners`仅调用已有patient workspace `_access`，检查有效user、真实session、revision、store、membership、employee以及patient/frontdesk/medical/exam至少read；拒绝时返回False。export权限单独不能赋予患者读取，患者partner导出另外检查export write。普通partner仍由原生ACL/domain决定，包括无YDental组/会话的内部账号。

Native DataSet会用RPC context替换request context；新增继承controller针对res.partner清除客户端ydental_binding，按真实SID+当前uid查已有session再注入服务器Binding。没有会话不创建关系/患者，也不封禁普通partner。继承原auth=user/jsonrpc路由配置，不新增匿名接口、不禁用CSRF或安全控制。字段、groups、allowed_company_ids或伪造JSON均不能产生服务器Binding。

普通image/content hook调用同一live read。ir.binary对core limited-field HMAC提前返回sudo的partner重新换回请求者环境检查，避免token充当授权。原附件分型/public/HMAC和源审计路径继续保留。新增HTTP对主联系人和监护人普通及有效limited-HMAC image请求均拒绝；旧临床附件、Notes/chatter/default context/附件改挂负向全量回归。

## Care/clinical 当前关系

`_current_relation`私有helper先canonical，仅查canonical patient/current store/superseded=False，不创建relation。care签发、care domain重新验证、clinical新建/维护均调用它；原生clinical来源域额外AND当前关系子查询，防本店直接RPC缓存读取脱离关系。

Relation查询的sudo只用来核验服务器已解析的patient/store，并返回内部关系记录或SQL域；它不提供独立公开查询入口或扩大医疗来源域。子查询使用ORM Query/TableSQL/Domain的组合，参数是服务器确定的store，未拼接请求SQL。current relation不要求first_arrival，行政显式建立relation不产生到店事实。

合并后旧ID解析target，只认target current relation；原scope若patient已canonical变化即失效。新增测试含真实受控merge和合并后历史superseded关系，以及私有隔离fixture使current relation失效后旧scope/local read/update拒绝。未新增生产关系删除/撤销接口。

## 扫描判断及验证

按odoo-security对sudo/with_user/with_company、SQL/domain、公开方法/RPC、routes、字段groups/related、XSS、文件读取、eval/exec/pickle、动态getattr/setattr、secret比较和可变默认值复查；新增产品代码没有任意SQL/文件/动态执行/反序列化/secret比较/XSS入口。公开override只保留原生模型/HTTP契约，新增业务hook全部私有。没有新ACL、字段、模型、外部依赖或下游业务模块。

原患者号/关系/merge/record模型文件与3b74b33相同；service原有方法只有_clinical增加当前关系前置，_lock/_operate/_create/_confirm/_business_patient/_active_business/_migrate_business及历史快照、旧号保护不变。

最终安装/升级、24模型+12真实HTTP/RPC、7组多连接probe、guard5、翻译及真实Firefox结果由[报告](s04-rework-report.md)与[final-checks](evidence/s04-rework/final-checks.json)固定。原forged care context、other session、撤权、跨店write、finance拒绝均保留；真实S05/S06/S08/S09/S10/S12仍NOT_RUN。
