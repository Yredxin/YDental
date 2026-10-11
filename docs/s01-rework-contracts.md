# S01 定向修正契约

来源仅为 #25 当前正文、有效评论及 [GPT-REVIEW 6108433241](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108433241)。本页补充工程契约，不另立需求；旧 `docs/s01-contracts.md`、`docs/s01-report.md` 和 `docs/evidence/s01/` 保留为 e55f823 的历史记录。旧文中直接使用客户端 care 字符串的说明由本页取代。S02 未启用。

|复核项|本次固定契约|
|---|---|
|BLOCKER-1|`ydental.access.service._get_care_domain(model_name)` 默认 `Domain.FALSE`。源读取域仅把该服务器域与当前店实际拥有 read 的 medical/exam 类别相交，再并入当前店权限域。客户端 `ydental_purpose`、dict、记录 ID 不构成授权。写入域不使用 care 扩展。|
|合成 care 范围|仅 `ydental_access_test` 定义冻结对象，包含 actor/session/revision/固定目标 IDs；私有 issuer 只取服务器维护的合成标记。钩子校验对象类型及当前 actor/session/revision。测试字段 NO_ACCESS，普通写拒绝。合成页面不接受目标 ID 参数，不提供真实患者范围。|
|上层责任|S04/S08 获启用后，在服务器验证患者/任务后覆写 care 域；本批没有患者模型、真实病历授权器、患者凭证或 S02 空壳。原生 ACL/record rules 与源域继续相交。|
|BLOCKER-2|仅新 server session 首次创建消费 `_get_default_store_id()`。建议值必须为正整数，且门店 active、当前用户 membership active、员工 active；否则保留未选店，不授予任职或业务权。有效建议通过原 `_switch`，增加 revision 并记录切店事件。既有 session 不重复消费，手工切店仍遵守 revision。|
|BLOCKER-3：方案 B|store/capability 的普通 create/write 在模型层检查角色、原生权限、门店公司边界，并在同事务批量写 actor/target/前后值审计。store 服务不再重复记录 create。普通 res.users 公共字段 write 增加公司边界和 profile.change；原生字段写及 record rules 保留。私有 profile 服务预先授权后只用原有固定字段 sudo 写，再单独记一个事件；客户端没有可伪造的审计抑制标记。|
|原生资料写权限|只有应用集团组不足以直接写原生用户公共字段，本 fork 仍要求原生用户管理权限。普通集团角色继续走受控 profile 服务；测试的直接成功路径使用单独的明确原生管理权限夹具，生产角色、ACL 和字段 user_writeable 不扩大。|
|BLOCKER-4|count/name_search/read_group/formatted_read_group/grouping_sets 产生 model/query 级 `source.query`，category=query，target_model=真实模型，target_id=0 明确表示查询，无具体成功记录。after 仅固定 operation（count/name_search/aggregate），不存 domain、正文、分组值或统计结果。嵌套调用用不可 JSON 构造的模块内 object 去重，每个顶层成功查询一次审计。|
|查询可见性|query 事件只供原 actor、当前相同门店、仍具备源读取权限时查看；不自动扩成他人的临床查询日志。无业务读权限的聚合查询明确拒绝；普通搜索仍按原生权限域返回空集合。|
|COMPANY-SCOPE|保留按 actor 原生 `user.company_ids` 限制集团动作的设计，不把客户端 allowed_company_ids 当授权。公共资料和集团离职影响整账号，因此要求目标默认/允许公司、全部 active/archived 员工公司、全部 active/archived 任职门店公司都在 actor 允许公司内。公共字段与原生公司变更同次提交时，拟设 company_id、company_ids 的 LINK/SET 也必须属于写前 actor 允许公司；禁止以同次自改公司扩大授权。公司 CREATE/UPDATE/DELETE 嵌套命令不属于公共资料修改，需单独原生主数据动作。完整预检查发生在任何资料写、归档或停用前；共享 A/C 账号不能被仅 A 的集团管理员全局改动。|
|人员审计公司范围|有门店的 personnel 行校验门店公司；无门店的全账号行校验目标账号涉及的全部公司，其他无门店事件按 actor 全部公司保守过滤；模板 targets 另校验目标门店公司。有限公司集团管理员看不到被排除公司的人员或共享账号全局资料/离职事件。|

新增运行只使用本批全新 S01 库。runner 按完整数据库名持锁，阻止同库并发 install/upgrade/probe/serve；不同新库无需停止旧预览。端口继续限定 18000..18999，并核对创建记录。子进程外发策略只允许 PostgreSQL 和本创建记录指定的 HTTP 端口；浏览器只允许该预览源。没有更改系统依赖、既有配置或防火墙。

自然人复用仍以原生 login 或明确账号 ID 为准。真患者/病历/检查、S03 排班、S06 坐诊租约、邀请送达、真实 MFA/长期 idle、正式 PDF/实体打印、50 会话/持续备份恢复及 S13 美化仍 NOT_RUN，不以本次合成测试宣称通过。
