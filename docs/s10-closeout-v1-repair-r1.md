# S10-CLOSEOUT v1.1 R1：取证器 actor flush 修正（尚未继续业务）

R0固定执行53665a1，唯一副本OID2144127，native PID940956 exit1，无SIGSEGV。
A-owner-scope提交返回并独立读回；acquire事务的四mutex各+1、editor7、audit actor7，
但doc1.write_uid=1，原断言要求7，因此保存完整差异后拒绝并回滚。
最终尾审doc1 pending/v2/editorNULL，confirm/correct/release/B/C/D/E均未执行；
源前后645表与198文件相同，源两条RO已关闭。

代码依据：固定core environments.py:410–422的flush_all用调用env逐model.flush_model；
models.py:5859–5906 _flush经当前model._write_multi，4008–4011为缺失的log字段补env.uid；
fields_relational.py:397–418对相同Many2one值过滤不标dirty。原取证器snapshot(root_uid1)
在actor操作后先root.flush_all；旧write_uid已为7而新业务仍7时，该字段可被过滤，
低层flush默认身份成为1。原差异与此路径一致，不将其写成业务actor真的为1或产品缺陷。

最小修正仅新脚本：正常actor操作后先actor.env.flush_all，再由uid1只读投影取证。
不改产品/core，不手写write_uid，不放宽write_uid==7、四锁、版本、审计或经济门禁。
新增确定性core前缀隔离测试及原差异/回滚核验。受控首次acquire已回滚，不是已提交文书动作。
后续如获预算例外，只允许同一副本、同一既存身份续接，无CREATE、无旧经济重放。

预算问题：R0停止处理器过早执行了原计划“最终源RO”，已消耗源2/2。
这属于执行器收口设计不足，不能静默增加源预算，也不能把R0的源尾审冒充后续R1终点。
若要在同包修正后完成五组，需要项目负责人明确批准最多再1条相同P021源的严格RO/RR，
只在整个包最终保全时使用，ROLLBACK/CLOSE，不新增诊断、不写源、不建第二库。
其余总RO28、Odoo6、修复2及其他预算不扩大；C撤权/恢复改用合法经理的真实HTTP授权服务，
避免为这些控制动作额外启动Odoo进程。该待批准例外尚未实施。
