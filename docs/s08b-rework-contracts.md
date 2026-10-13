# S08-B定向返工边界契约

唯一依据#32 GPT-REVIEW6135903692，基线7ccb25cf6a54732caf7007c39498d393b6a96929。本文件与固定产品0a49fac对应。原docs/s08b-contracts.md继续适用，但其中目标法人账号要求、按处方queue mapping直接取药价及草稿必填的旧描述由本文件替代。最终实测另见返工报告。

|动作/事实|准入与结果|禁止/恢复|
|---|---|---|
|新椅旁药实际执行|当前medical-write真实serving，已发布本店药品SKU↔独立S05 medicine收费目录及原生单位关联；各真实batch同SKU、chairside类别，合计等于实用项目量；原生扣库后才确认费用|空批次、错药、错单位、数量不符、缺价/库存不足整笔拒绝|
|已发生但药品证据不足|保留原actor/station/time/qty/原始报送材料与pending原因；不确认费、不伪造move|原负责人提交有据的原用药批次核对，追加审计与真实consumption；取原实际时点价，未知价继续人工price-write核价；S07原pending仍按原恢复合同|
|药品SKU收费关联发布|当前本店price-write，经可信连接和全锁序；明确本店真实medicine SKU、单位、S05 medicine目录、本店合法mapping及现有已发布S05版本、关联证据，演示策略|每店一个目录只绑定一个SKU/单位，一个SKU/单位只绑定一个目录；不可普通改写/删除；无明确共价政策，不支持泛化多SKU共价；不发布生产政策|
|处方草稿/冻结|草稿可缺规格/用法/频次/疗程；issue服务端逐行复验真实active medicine、单位、数量及全部临床字段|空/空白拒绝且仍draft、无task/queue/fee/move；不自动补医学决定|
|同药房方向多SKU发药|统一pharmacy task/queue；每行真实SKU独立解析已发布收费关联，冻结于实际事件，S05价格版本在实际时间取价|缺关联的新发药整笔拒绝、余量不变；已发生事实pending且占用真实已领数量，费用不得借另一药价；后续调价不重算历史|
|跨法人受控转诊|来源A本店medical-write+真实当前来源；复用S05封闭定时/不定时来源服务，目标合法mapping/open/容量|不要求目标company_ids或membership；不授目标普通read/write/RPC/切店权限；无额/停接/非法目标完整回滚，原来源保留|

原S08-A文书、S06统一队列、S07真实库存、S05原生价格/快照保持。新增关联是审计来源元数据，不是第二套价目或余额。历史已确认旧记录不自动绑定、不改费/价/库存；显示未经本次SKU核对的历史状态，新动作必须重新符合合同。S10真正出账未启用。

正式规格/用法/频次/疗程/签发和生产药价政策仍待业务审核；合成测试值不是医学或生产决定。本次Project零mutation；S08-C/S09不启用，生产部署BLOCKED。

## 动作与权限补充

原12动作及严格签名、连接绑定、CSRF、锁序、CAS、receipt/source幂等继续适用。本次新增两项，总计14个封闭动作；没有公开ORM动作入口。

|动作/参数|角色及状态|审计/错误/恢复|
|---|---|---|
|publish_medicine(`product_id,catalog_id,uom_id,evidence,policy`)|当前本店price-write、可信连接；policy仅明确demo_confirmation；已发布合法S05版本+本店mapping|medicine_price_published；medicine_price_unverified/policy_unpublished；失败无link/receipt，修正真实关联证据后独立新key提交；已有link不得改写或共价重绑|
|verify_medicine(`event_id,materials,evidence`)|原actor，chairside为medical-write、prescription为pharmacy-write；已发生pending且reason=medicine_evidence_missing；尚无consumption|medicine_evidence_verified；medicine_evidence_missing/medicine_price_unverified；原始报送JSON不覆盖，追加核对审计，原时间/actor/qty/价保留；同key只返回原结果|
|execute/correct/dispense（原参数）|药品新执行同时符合link+SKU+batch+qty/unit+现存岗位合同|同源同key唯一；新失败整个事件/快照/费/库存回滚；已发生证据不全pending，处方实际累计占用但无假费/假move|
|order/edit_order/issue（原参数）|草稿临床文本可不全；开立时服务端重验每启用行，药房实际发药再验|不完整草稿保存不生成实际任务；开立失败仍draft且无号位/费用/扣库；完善后显式开立|
|refer（原参数）|只有来源A公司账号授权亦可，当前医疗真实source及目标合法mapping、open、capacity|沿S05原来源与原claim；满额/停接/本店或非法mapping拒绝，原serving/文书/有效转诊receipt不变；不拓展目标普通权限|

所有写在原S01→S04→S03→S05→S06→S07→B锁序内二次验权与连接，native stock在后；新link独占唯一约束。新错误前缀medicine_evidence_missing、medicine_price_unverified，原前缀和中文保持。

新SKU关联只证明明确的本店商品、收费目录、单位及发布时版本；后续实际取价仍调用S05 `_quote(...instant=actual_at)`，不是永久冻结关联发布价。事件快照与fee保留实际采用版本/币种；后来99元不重算既往10/27元事实。关联发布本身不创造执行、费用、库存或药房任务。

## 历史与回退

旧已确认药品事件可能没有新增SKU字段。升级不推断SKU、不补费、不重价、不更改原move；展示原事实，不能据未经核对的旧关联执行新的药品差额。旧字段默认形态通过真实执行后的明确旧schema夹具验证，不能称完整旧源码树升级演练。

只停本批精确configSHA/PID预览或禁用本批业务入口，保留DB、filestore、日志、原生move及所有Git历史。不得对带实际历史的库卸载B、清表或退到A；代码回退不撤销已发生用药/费用来源。若需要反向迁移，应另开新隔离库制定保留历史迁移并独立审核。本批没有执行生产回滚。
