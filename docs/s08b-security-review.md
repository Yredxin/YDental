# S08-B 安全自审

这是Codex源码自审与实际测试记录的索引，不代表GPT独立审核或生产安全认证。

|边界|产品实现|验证与限制|
|---|---|---|
|POST身份/CSRF|Odoo auth=user/http POST默认CSRF；S01 session/revision，S06连接hash|真实HTTP/RPC否认例；无公共任意model/domain/values接口|
|权限撤销与旧页|锁内重读membership/currentstore/company、连接、持有人与文书版本；实际项目能力/资质|模型/并发与浏览器否认；隐藏按钮不作为授权|
|普通ORM与context伪造|read-only ACL、当前门店source_domain、create/write对象identity令牌、unlink拒绝|JSON true/dict不能成为Python对象；RPC私有方法拒绝|
|库存可信来源|精确dataclass类型+actor/store/consumption/immutableevent/frozenprice/实际执行复验|默认S07拒绝不变；adapter仅原生stock.move，真实操作者保留|
|历史恢复|原fact/source/time/price保留；S07仓库有据原pending补账，B仅核对|缺价须独立price-write核价；无后来价格默补；原始材料事件时间传递|
|价格提权|闭合S05只读取价+冻结；price-review单独price-write|doctor/pharmacy无price-write或warehouse-write也可合法派生；无任意价目写|
|受控sudo|固定内部模型/字段、明确门店/类别/患者域；订单药房必要投影；产品公司限制|不接受客户端模型名、SQL或任意domain；历史经济原单无跨店共享|
|转诊|精确ReferralSource+完整参数hash+原执行/文书；S05原锁/容量/权限|不指定目标人椅；目标公司必须账号显式授权；失败不留半占额|
|附件/导出|B来源加入原S01附件阻断tuple；source域与export授权|HTTP拒绝普通附件、普通export_data及直接write；本批无PDF导出入口|
|XSS/注入|QWeb t-out、无t-raw/Markup/eval；固定SQL标识/参数化值|产品无shell/filesystem/raw客户端SQL；请求长度100000；字符串原上游限长|
|事务/并发|上游有序fence→S07→B；savepoint；DB唯一约束；无产品commit|首轮独立backend/barrier、有界serialization retry，native move完成后异常验证整笔回滚|
|患者与工位释放|上层受控S06 finish、原execution/entry/task/append同事务关闭，再lease退出|余量唯一原处方新任务待报到；不占原门诊容量，不自动入队|
|日志/审计|治疗、费用/库存来源、order、review、return、referral各分事件；只保留必要ID/状态|仓库交付只合成截图及脱敏摘要/hash；私有日志/凭据0600本机保留|
|外发与测试隔离|B DB命名/marker/cluster/OID/config/hash/PID/dbfilter/data_dir/SMTP和DNS/socketguard|历史库不接管/重置/删除；不更改核心、odoo-12或系统依赖|

尚未证明生产稳定性、50活动会话性能、真实药物审核政策、S09设备来源或S10已出账更正。S07历史SIGSEGV及共享内存长期增长根因仍UNKNOWN，生产继续BLOCKED。
