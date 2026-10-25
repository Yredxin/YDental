# DL-P6：仓库物料／批次查询与只读定位

计划：YD-S13-DL-P6 / 1.0。当前实施中；本轮SYNC_PENDING；用户亲手效果待确认。未完成动态和独立总验收前不预签TECHNICALLY_COMPLETE。

## 范围与固定候选

承接P5最终报告ede6205976f28f6367bcd2a33aa785d96f6aff21，产品beea6d3不重开。P6准备/工具/真实前态候选539d147d659a6214d16e2796460728912f810ccf；首版产品/加载候选aec20359d6f0cdc0e7a1f1070bcc870fd0798b95。core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb固定；同一合成目标/OID2171423/cluster7694897083368259627与原filestore，无新建/复制/改名库或合并部署。

仅四个分离片段：原查询section；批次标题/九列表；来源标题及article只读前缀；scan后原来源nav。每条来源wrapper在原can_write前闭合，不包办理。使用现有request.httprequest.path门控工作台主题，can_catalog保持原能力含义；目录不应用P6主题/帮助。13办理details、scan标题/form/help、页头、错误页和原投影/循环/链接SOURCE保持；最终运行冻结对照待实际结果。

产品唯一写者p6_product；p5_resume_tester实现私有工具/运行浏览器；p5_resume_acceptance未实现产品或相关测试工具，独立审源/真实事务/原图请求/进程/包/总项；root唯一主控、运行/模块加载/状态/报告/GitHub写者。共享OS不冒权限隔离。

## 字段、查询与定位契约

|位置|原投影与保持语义|
|---|---|
|GET查询|q、maxlength100、原回显；不提交event_id/page，不自动选批次，输入/失焦不预请求|
|批次集合|visible_lots；term.strip().casefold()在product＋name中包含；不扩展编码匹配、不排序或分页|
|来源集合|原本店来源或当前店为target的transfer；product.name/default_code/lot.name的原ilike；合法目标调拨不被额外过滤|
|批次列1—3|l.product / l.name / kind_labels[l.kind]，原row顺序和lot锚点/data-lot保持|
|批次列4—6|l.on_hand / l.quantity / l.quarantine三种原值，不相加、不互代、不新建总量|
|批次列7—9|l.expiration / l.received_at原UTC；l.flags原顺序、data-flags及flag_labels，不补今日/0或“全部正常”|
|来源身份与状态|e.id原event锚点/data-event；kind_labels[e.kind]、e.product、state_labels[e.state]/data-state|
|来源内容|原e.quantity/lot/responsible/summary/synthetic/move_id；不推断单位或成本，实际负责人及待核对默认可见|
|状态|pending待核对；done库存已确认；observed盘点相符、无库存移动，不外推治疗/责任全部完成|
|来源链接|原/ydental/inventory?event_id=<id>#event-<id>，不带q/page，不改变批次集合|
|来源分页|id desc，每页30、第31条探测has_more_events；search_url只q/page，不保留event_id，不伪造总数|
|空态|批次与来源分别说明本范围/本页，均不推断无库存、无责任或已完成|

仓库13/store1为普通有权主路径；读取16/store1和无权17按真实HTTP另验。真实样本3批次/50来源，30＋20两页；代码S11V12-material的真实批次0/来源23与名称筛选差异已采。当前无带target的transfer记录，不能称真实HTTP incoming通过；原域SOURCE、未改产品循环及明确组件分别记录，不造库存事件。真实来源状态只有done，pending/observed及长值使用内存组件，不冒真实业务。

## 前态、加载与保护

初始完整145业务/13技术/现场83文件与P5 root/独立末态九区逐值同，原1269审计全部保留。未实现者新physical228803 RO/RR核后形成真实初始准入；新产品又由physical232577核当前完整pre，精确绑定新候选/probe/runtime/launcher。旧准入、scope、STOP和旧脚本不改；本阶段运行scope原expiry18:50:34.860616UTC不延长。

真实前态窗口20261025T105814Z-0a10c7d9f83c于2026-10-25T11:04:27.713209Z正常停止，服务child0。before-v1主链12分项/五视口/catalog完成后同context旁路重登录等待超时，实际client2；before-bypass-v1只补三旁路6分项，正常close后Process.poll元数据API错，实际client2。原源/日志/退出均保留，不将整client倒签PASS；已独立审适用分项及24原PNG。后续只修fresh角色context和实际asyncProcess.returncode，不重采已成主链。

唯一inventory模块加载实际exit0/ERROR0/noNative；即时完整pre dd6cd60d…→实际退出2ff56f02…→post33b1c264…已采。原件文件清单/bytes/SHA保持；加载仅49 ir_access/group69/mutex1写日（revision0不变）及9技术类元数据差异，须独立逐值分类。运行后最终完整保护和本阶段全程独立结论待实际收口。

## 普通岗位7步复现

默认正常复开后执行，不承诺当前在线或自动化窗口可接手：

1. 普通仓库岗位正常登录，选择授权门店，从原菜单进入库存。
2. 输入物料或批次名称，用搜索按钮或Enter明确查询。
3. 阅读九列原值，区分在手、可用与隔离；注意UTC日期和具体告警。
4. 窄屏聚焦批次滚动区，用左右键阅读全部列，不把无告警解释为全部正常。
5. 阅读来源类型、库存状态、数量、负责人和摘要，点击“打开来源”定位原锚点。
6. 浏览器返回；按原来源上一/下一页翻页，观察批次表不受源页码影响。
7. 需要时只展开/收起或取消原办理面板；不填写或提交库存动作、扫描、PDF或原件操作。

## 收口边界

原P1—P5技术/同步结论、PARTIAL历史、新旧包、失败与UNKNOWN保持；用户亲手未确认不写PASS。完整S13未完成，#37 OPEN/#36 CLOSED；P6最终只新增一份结果，不改P1—P5评论。完整动态验收/独立保护/新包/总项成立后正常提交推送并实际读回；main只必要路由。P6交付后停止，下一计划、全链负载恢复/实机/正式政策/组合扫码/真实患者资金外部通道、合并部署生产未启用。
