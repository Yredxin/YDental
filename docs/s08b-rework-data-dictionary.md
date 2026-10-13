# S08-B返工数据字典

原字典docs/s08b-data-dictionary.md继续适用。本次新增如下，均为真实产品字段，不增加库存余额、财务账本或队列。

|模型/字段|类型/必填/来源|状态/权限及历史处理|
|---|---|---|
|medicine.link.ydental_store_id/category/actor_id|继承受保护来源；本店/price/真实发布者|本店price-write可信动作创建；普通CRUD/export/attachment拒绝|
|medicine.link.ydental_product_id|M2O真实S07 medicine SKU，必填|本公司或集团产品，启用，精确原生单位|
|medicine.link.ydental_catalog_id|M2O真实S05 medicine服务目录，必填|本店已有合法mapping；一个目录一个SKU|
|medicine.link.ydental_uom_id|M2O原生uom，必填|真实库存与收费目录同单位，无自行换算比例|
|medicine.link.ydental_price_id/currency_id|M2O发布时已发布有效S05价格版本及币种，必填|关联证据不代替价格表；实际执行按关联目录在实际UTC取价并冻结自己的snapshot|
|medicine.link.ydental_product_name/evidence/published_at/policy/state|发布时药名/证据/UTC/明确demo_confirmation/published，必填|关联行不可普通改写/删除；版本为不可变ID。未发布多SKU共价政策，拒绝泛化共价|
|event.ydental_medicine_link_id/product_id|M2O实际采用的关联及真实SKU，旧行可空|新药品确认必有；旧已确认行不自动推断，保留旧费用与库存，禁止无证据新更正|
|event.ydental_reported_materials|JSON，原始报送 `{rows: [...], catalog_id: ...}`|显式空rows可保存。原始选错批次不被核对结果覆盖；旧行空值不补造|
|event.ydental_medication_review|Char原负责人追加核对证据|仅pending实际事实、原责任人、有效关联、真实批次/数量；记录独立审计|
|fee.ydental_medicine_link_id/product_id|M2O冻结event关联及SKU|新确认药品费与真实move/lot/quantity/原价snapshot一致；S10未启用|

处方specification/usage/frequency/course允许未完善草稿；issue逐行强制非空白文本、最多240字符，并重验真实启用SKU/原生单位/正数及精度/服务方向。没有默认临床值；真实规格、剂量、用法、频次、疗程、签发规则仍待业务审核。

新增pending原因`medicine_evidence_missing`：原用药确已发生但SKU/批次/数量或价源关联证据缺失，不生成fee/native move。保留actor/time/station/quantity/原始材料；有合法关联时可保存已核实的原价snapshot。原负责人verify_medicine追加真实consumption后，原时间无价仍为missing_price，原库存不足仍按S07原pending证据恢复。原已领数量仍计入处方累计，不能重复领。
