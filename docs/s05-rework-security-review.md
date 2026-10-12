# S05定向返工安全自复核

这是Codex实施方自复核，不是GPT技术PASS或用户验收。仅对GPT-REVIEW6115823569三个BLOCKER的修正及相应测试复核；原安全报告/失败链保留。当前固定SHA及实测结果见s05-rework-report.md。

|事项|检查与结论|
|---|---|
|集团目录授权|内部用户与真实SID/revision、live集团身份；不依赖或补门店price grant。读取例外只传给catalog/native product；mapping/business/price来源不因目录身份开放。真实HTTP/RPC覆盖仅目录管理员及撤身份下一请求。|
|门店价格授权|mapping/price/review/publish/snapshot仍_check price-write；集团price-none和伪造POST均403。原生mutation对象和CRUD/复制保护未放松。|
|预约日期|比较S03门店当地日；现有held/供给/到期校验保留。future拒绝不产position/queue、不扣额；同日九小时早到及余额0用原claim成功。没有按客户端日期授权。|
|转诊入口|普通HTTP/operate先拒绝referral模式；private server hook默认fail-closed。test permit必须精确类型+actor/store/action/hash/category，dict/context不可伪造；private RPC被框架拒绝。|
|跨法人目标|去掉user.company_ids作为转诊授权，但没有授予目标company或membership。只在可信来源验证后，对固定active/open target mapping使用原受控容量/患者接口；任意目标CRUD、reserve/cancel/price或切店仍拒绝。|
|真实actor与分类|来源hook返回medical/exam，锁前及锁后实时检查对应业务write；receipt/audit记录真实doctor、源/目标店、源task/目标mapping，S03仍有目标claim/event；medical和exam分支均断言。|
|事务/merge|patient→supply→intake、savepoint、RR有限serialization重试保持。未来预约拒绝/目标失效/停接/末额无半建；原13组竞争及S04真实merge回归保留。|

odoo-security全模式扫查：ACL无变更、无public/portal新权限；sudo仍仅服务器固定模型/字段，controller只输出批准的目录和本店price读取；SQL仍仅原固定参数化锁/mutex；无请求domain/field/model选择。没有新增公开模型方法、routes或CSRF例外。QWeb继续转义，不新增Markup/innerHTML/t-raw。无secret/related附件新字段，无产品open/eval/exec/pickle/getattr/setattr、可变默认参数或富对象HTTP返回。冻结permit不是认证token字符串，不涉及可变时长密钥比较。测试手工commit仍只属于自行打开的独立cursor；产品无commit/rollback。

新权限、日期和跨法人源契约采用模型、真实HTTP/RPC及Firefox验证；原始日志/配置/访问凭据只留私有run。公开证据使用合成材料和白名单摘要；Firefox默认sandbox、进程沿用外发保护，不改系统依赖或既有服务。

S06真实waiting/calling/叫号/租约、S08真实治疗/医嘱来源、S09/S10、生产锁价和S13吞吐仍NOT_RUN/待责任阶段；不能用合成permit或全局串行正确性代替真实临床、生产或用户验收。
