# S08-C PDF 字段与来源字典

三个静态模板共用 A4、zh_CN、原生 QWeb/PDF 引擎；正式审核标志均为未审核，文件均为演示副本。固定产品模板编号 S08C-CLINICAL-1、S08C-RX-2、S08C-CONSENT-1 在每份 PDF 与 job/audit 明示。早期 Firefox 样张为 RX-1，不充作 RX-2 验收。RX-2 长处方逐页人工核对 FAIL，固定 test 又发生 SIGSEGV，整体 BLOCKED。实际 source IDs、version_set、摘要及页数见 evidence/s08c 中逐份结果。下表字段缩写省略既有字段的 ydental_ 前缀，准确取数实现以固定 product 的 ydental_print_service.py 为准。

|PDF 字段|真实模型/字段与 source ID|版本/空值提示|
|---|---|---|
|患者姓名/编号|S04 patient service._patient(source.ydental_patient_id)，canonical name/ydental_number/id|保留 canonical ID 和原 source patient ID；当前合法关系必需|
|来源门店/查看门店|source.ydental_store_id.name/id；S01 session.ydental_store_id.id|版本集合和摘要覆盖门店身份；不把其它店签署视为本店|
|生成人/取数时间|当前 env.user.name；fields.Datetime.now UTC|真实生成者不是文书作者或实际药师|
|模板/摘要|服务固定 TEMPLATES[kind]；规范化 JSON SHA256；实际 PDF SHA256|job/audit 同时保存；PDF 不藏 token/病历全文元数据|
|文书/所选/当前版本及状态|clinical.document.id/ydental_version/state；clinical.version.document_id/number|仅选定独立文书；version0仅未有保存版本时可读|
|原作者/当前责任人|document.ydental_author_id / ydental_responsible_id|不被接手医生覆盖；未记显示“未记录”|
|所选版本作者/动作/UTC/前序/原因|version.ydental_author_id/kind/recorded_at/previous_id/reason/template|历史文字版本独立，确认是文字确认，非正式签署|
|原与当前接诊段|document.ydental_execution_id / ydental_current_execution_id|两个 ID 分列|
|原接诊操作人/工位/开始 UTC|原 execution.ydental_lease_id.actor_id/station_id；execution.started_at|不借当前工位或生成人替代原来源|
|七项临床文字|selected version.ydental_content（未保存则 document.content）：chief_complaint/history/findings/diagnosis/treatment_plan/suggested_materials/follow_up|沿 A 字段规则；空值“未记录；不推断医学结论”|
|FDI 牙位/牙面/状态|同一 content.teeth[].tooth/surfaces/state，52 恒乳牙及0|present/missing/unknown/not_applicable 中文；未列牙位不推断正常|
|处方/版本/原开立医师/状态|treatment.order.id/version/actor_id/state；kind 必须 prescription|draft/issued/done 明示，非正式签发|
|处方原文书版本/段|order.document_id/document_version/execution_id|保留开立时真实来源|
|药品 SKU/名称/产品规格|line.product_id.default_code/id/name/ydental_specification|不足显示未记录；不补医学剂量|
|行规格/用法/频次/疗程|line.specification/usage/frequency/course|草稿可不完整；生成不会 issue|
|开立数量/原生单位|line.quantity/uom_id.name/id|原草稿取消行仍列历史数量及 cancelled 状态|
|实际已发/未领|本行 prescription event.quantity 合计；issued/done 开立量减合计，draft/cancelled 待领0|真实 pending 发药也属于实际事实；不从报到/叫号推断已发|
|行状态/原因|line.state/reason|取消旧行原原因保留，不覆写或删除|
|实际发药事件/药师/UTC/门店日期|event.id/order_line_id/product_id/quantity/actor_id/actual_at/business_date/state|与原开立医师及生成人分开|
|价格来源/药品关联|event.price_snapshot_id/medicine_link_id|只显示来源 ID；非收款或会计入账|
|同意书八个空栏|静态受控模板：拟诊疗/风险替代/说明问答/患者决定/患者签署/医师签署/监护授权/日期核验|均待补全、待解释、待签署、待核验；无预填医学和同意结论|

临时 job 包含 actor/store/session/revision/kind/source_id/version/purpose/source_digest/pdf_digest/template/versions/expires_at/key/pdf。没有普通 ACL；会话、请求键和 Binary 字段 NO_ACCESS。write/unlink 拒绝普通及未受控调用；唯一约束为 session×revision×key。Binary 使用 Odoo20 BinaryBytes，数据库存储且不是 ir.attachment。

版本集合：临床含 document[id,current_version,state]、selected_version[id,number,kind]、原/当前接诊段、canonical/source patient；处方含 order[id,version,state]、line[id,state]、真实实发 event IDs、患者 IDs。规范化摘要还覆盖本表全部显示字段，故身份/责任人/内容/发药变化后的旧 job 会失效。
