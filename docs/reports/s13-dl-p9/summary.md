# DL-P9 文书主页面间距与留白

YD-S13-DL-P9 / 1.0。实施中；技术及同步尚未签完成，用户亲手效果待确认。[完整用户计划](../../execution/S13_DL_P9_IMPLEMENTATION_PLAN.md)。

## W0 有界接管

从clean P8报告756df60286d078a4243f87c885dc7a10de1f9b8b正常建立`codex/s13-dl-p9-documents-spacing-r1`，无reset/clean/强推/从main重建。P8产品bd8411d4、唯一回执6406133603及P1—P8/P5 PARTIAL/旧包/失败/UNKNOWN保持。准备候选ee15b39；产品仍P8，实际前态另采。

主控root唯一产品/报告/状态写者与调度；runtime_p9运行/保护工具，testing_p9真实浏览器/测试工具，acceptance_p9未实现者独立验收。同OS不冒隔离。当前真实新scope及独立准入不修改旧时间/STOP/guard；唯一既有synth OID2171423/cluster7694897083368259627/原filestore，core f0c5a9b固定。

原生loaded主view1618+扩展1621的en_US/zh_CN完整合成arch已核，扩展XPath仍`//details[@name='document_template_review']` before，三个继承details均直接main子节点。无模块wrapper，不移动继承内容。独立before新physical454445 RO/RR完整145业务/13技术/九区与root同，83引用/80真实路径/80不同SHA逐文件字节核，4原生依赖保持。

## 间距责任表（16px根字号，待最终实测签结）

|关系/明确layout边界|唯一负责人|目标/保持项|
|---|---|---|
|前模块border底→后模块border顶|后模块`spacing_module` leading margin|1.5rem；前模块bottom0；页头到页面上缘原1rem保持|
|搜索section border底→preview form border顶|preview form leading margin|1.5rem；hidden busy无盒，无泛化查询grid|
|query label盒底→可见input/trigger盒顶|query_field flex gap|.5rem；标签/字段margin0；P1内部padding/弹层保持|
|并列字段/字段最后一行→preview按钮|原query_preview grid gap|1rem已有合格值保持|
|query按钮→说明/busy|说明或状态leading margin|.75rem；bottom0，hidden不占位|
|已有header/query/originals卡片边界→内容|原卡片padding|桌面1.5rem；原45rem断点及以下1rem；每层一次|
|原header标题/用途/导航/说明、originals标题/说明/表格/分页|原容器gap与已清零子margin|1rem合格值保持，不把所有子组加24|
|预览标题/两追溯/iframe外框/生成form|明确preview容器gap|1rem；各直接子margin0；iframe内文及属性不改|
|版本label文字布局盒→原select|原label标记spacing_field flex gap|.5rem；标签不改关联/顺序|
|版本label组→生成按钮；管理字段/动作|原form标记spacing_form gap|1rem；隐藏字段不参与布局|
|目标summary底→第一正文盒顶|正文leading margin；原件dl保原margin|.75rem；只open后出现|
|旧查看/下载同组动作盒之间|原read_actions flex gap|.75rem已有合格值保持|
|读动作组底→打印details顶|打印details leading margin|.75rem；正文到打印按钮.75rem由正文bottom负责|
|原件追溯dt底→自己的dd顶|dd leading margin|.25rem；dl gap0；下一dt leading margin.75rem，首dt0|
|管理summary→说明→第一form|说明leading .75rem / form leading1rem|不叠默认p margin；两独立管理form之间后form leading1.5rem|
|继承临床/失败/同意三块外距|仅各顶层details spacing_module margin|1.5rem；内部所有样式/字段/动作冻结|

空间变化允许目标纵向位移、可用宽度和自然换行，不要求目标rect与P8全部相同。冻结映射：原form边界/label关联/字段顺序/type/name/value/action/method/target、csrf/revision/key/operation、hidden/required/disabled/权限/时机；P8按钮内部与spinner、P1JS及控件内部、iframe正文/PDF、表格列/单元padding、继承三块内部；库存/报表/结算与全局主题不改。
