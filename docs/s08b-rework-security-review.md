# S08-B返工安全自审

依据[GPT-REVIEW6135903692](https://github.com/Yredxin/YDental/issues/32#issuecomment-6135903692)，固定产品0a49fac；按odoo-guidelines、odoo-web-guidelines及odoo-security核读12个变更产品文件。原S01—S08-A产品零修改。此为Codex自审，不是GPT独立技术PASS。

[逐模式扫描与文件SHA](evidence/s08b-rework/security-sweep.json)记录全模块命中与判定。受控sudo均在固定实体私有服务、真实本店/来源/角色/连接与锁内二次校验后使用；product/lot只接受正整数ID并验证公司、品种、精确单位。唯一raw SQL为原参数化事务advisory lock。请求不能注入model/domain/context内部对象、实际单价或任意CRUD。无动态eval/pickle/任意文件入口、t-raw/innerHTML信任或富对象RPC返回。

新增medicine.link继承受保护来源、只给内部来源权限的ACL；本店price-write私有闭合动作生成，普通create/write/unlink/export/附件和私有RPC均拒绝。来源医生仅有A公司授权仍可通过原S05封闭转诊；B普通读/写/RPC/切店继续拒绝，不追加医生company_ids或membership。跨店UI仅展示受控转诊必需的目标mapping，不开放目标业务原单。

已发生用药由原责任人追加核对，不能由其他医生或价格/仓库岗位伪造执行；pharmacy-write经原S07真实来源适配产生自己的stock.move和fee，无warehouse/price提权。新缺料、错药、空批次、数量/单位不符、缺SKU价源整笔拒绝；已发生证据不全保留pending且不确认费用。费用SKU与event、关联、原生lot/move、原时点S05快照强对应。旧已确认事实不自动重写。

两条真实HTTP路由均auth=user；写仅POST、默认CSRF开启、大小受限、封闭签名、server-bound connection与receipt/CAS，无客户端自动重放；读取及错误no-store。QWeb t-out、JS textContent与JSON普通数据；原A终态冻结保留。中文稳定错误前缀单独实测。

验证包括真实模型、HTTP私有RPC/CRUD/export/attachment负向、来源仅A跨法人受控成功、原药房单权4+2、多SKU价源、35项SQL及独立双连接竞争；最终数量与固定test以[报告](s08b-rework-report.md)为准。

残余风险：药物规格/剂量/用法/频次/疗程及签发、生产药价/税币种和共用收费政策未获正式业务审核；仅明确演示策略，未伪造政策。生产50会话性能未验证；继承原全局事务fence。历史S07 SIGSEGV、原B及本轮候选Firefox页面崩溃根因UNKNOWN，未声称修复，生产BLOCKED。S08-C/S09/S10未启用。
