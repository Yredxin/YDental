# S07 交付报告｜YD-N1 R1

本批完成真实库存侧开发和 Codex 自测，申请 GPT 独立技术复核；不是用户验收或生产发布。唯一授权为 [GPT-ACTIVATE6119956887](https://github.com/Yredxin/YDental/issues/31#issuecomment-6119956887)，需求为 [#23当前总计划](https://github.com/Yredxin/YDental/issues/23) 和 [#31](https://github.com/Yredxin/YDental/issues/31)。上游 [S06技术PASS6119723325](https://github.com/Yredxin/YDental/issues/30#issuecomment-6119723325)、[状态回执6119803450](https://github.com/Yredxin/YDental/issues/30#issuecomment-6119803450) 已完整读取。工程资料不另立业务计划。

## 固定版本和环境

|点|固定提交/事实|
|---|---|
|baseline|`46833f0ac4bd37b778f3a5a80d51be430e4ebde6`，S06-C final|
|product|`916492719e5d299fa0326330ac798cd6cda237bd`|
|test|`be4a282dc0ebb54fc32dfafa7ac05cfa7535d939`|
|final|完整SHA固定于#31本批交付评论；test→final只文档/AGENTS/脱敏证据|
|分支|`codex/s07-inventory-r1-20261012`，从baseline新建，正常推送|
|核心|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地fork声明20.0；非同SHA官方上游比对|
|Python/依赖|核心`.venv/bin/python`；原有process-local phonenumbers、PDF、字体、Firefox资产；无新系统依赖/OCA|
|最终全新库|`ydental_s07_test_20261012085648_03913c2a`，仅合成资料；专属localhost:18142|
|运行边界|S07 runner、创建记录/OID/cluster、独立config/data_dir/log、精确dbfilter、外发guard；见environment.json|

初始路径/remote/clean worktree/基线核对通过；父目录未跟踪AGENTS保留。产品新增`ydental_inventory`，另有只能装入受guard新库的测试模块。S01/S03/S04/S05/S06既有源码、核心、odoo-12、历史库、既有服务未改。产品→测试仅新增原生单位factor/祖先路径修改负向测试，没有测试后产品漂移。中间修正提交和失败证据均保留。

Project实施前完整读取21字段/15条目/6视图/7公开workflow；只将#31自定义执行状态待启用→进行中一次，阶段S07、原生Todo、Issue OPEN。两次完整读回深差异仅该字段name/optionId。#30仍S06/待用户验收/Todo/OPEN；#29待用户验收、#23PLAN/进行中、#32—#37待启用。首次读回TLS超时后未重发mutation，只重做完整读取。开工评论 [6120104358](https://github.com/Yredxin/YDental/issues/31#issuecomment-6120104358) 已逐字读回；交付前再核对来源和完整Project，不自行改待复核。

## 需求落地

|要求|完成状态/实现|范围限制|
|---|---|---|
|R19 原生库存、三类库位、批次/单位/效期|完成：product/stock/uom/product_expiry，独立门店warehouse及药品/耗材/义齿/待核查库位；native move/quant唯一数量事实|收货按实际证据，不实现采购订单/应付账款|
|禁负/过期/停用新执行、并发幂等|完成：服务端范围/单位/粒度/批次校验；request和source双unique；native移动/审计同事务|采用单一库存fence，50会话吞吐未验证|
|来源分类及不双扣|完成：补货真实仓管动作；治疗/椅旁/带走处方的可信私有来源契约和隔离合成适配器|真实S08治疗/发药待接入；不创建临床/药房任务|
|R20实退核查、退款不回库|完成：原实际出库→quarantine→release/discard，累计限额；已消耗不能退成未用库存|真实退款/处方剩余量S08/S10未建，不冒称闭环|
|真实已做缺料恢复|完成：保留原合成实际事件、责任人、pending、原价/费用引用；真实补账后原ID唯一补move|真实S08事实、S10费用单/钱款NOT_RUN|
|权限/工作台/审计|完成：集团主数据与price/warehouse拆分；本店最小投影、native/RPC/export/附件拒绝、S01审计|真实病历和任意患者历史不向仓管开放|
|预警/义齿日期/扫码|完成：显式策略、有效批次汇总低库存、近效期/过期/停用、首次真实入库当地日起待取、识别钩子|演示60/0/3未生产批准；S11未装unsupported，不冒充加工入库|

字段与native映射见 [数据字典](s07-data-dictionary.md)；前置、动作、错误、事务、配置见 [工程契约](s07-contracts.md)；安全自审见 [security-review](s07-security-review.md)。

## 实际测试逐项追溯

以下PASS只指本次明确授权的S07库存侧及标记合成来源。每个真实执行方法、命令/退出码、版本、数据库和结果见 [证据索引](evidence/s07/README.md)。全部在固定test提交执行。

|TC|结果|实际覆盖与证据|
|---|---|---|
|S07-T01 / F1|PASS|实际入10/发3/可发7；相同请求及不同键同来源只原event/move；模型、HTTP、Firefox、双连接|
|S07-T02 / F2|PASS|两个不同PostgreSQL backend竞争最后1份，仅一成功；不足无半move/audit；native已done后注入异常全回滚；最终7类SQL不变量0|
|S07-T03 / F2|PASS|过期/停用产品及批次、伪造跨店/非法ID服务端拒绝；HTTP直传ID也拒绝；禁用先提交/出库先提交两种真实锁交错|
|S07-T04|PASS|10件包装→库存单位、小数、配置粒度、非有限数、错单位/祖先变更拒绝；无静默舍入|
|S07-T05 / F1|PASS|实退1入待核查，可发仍7；核验release后8，discard真实去向；累计退回/核验并发上限；独立退款无库存动作；已消耗治疗/椅旁不自动回库|
|S07-T06 / F3|PASS（S07范围）|已发生合成源缺料→pending责任人→实际入库纠正→原event唯一recover；同来源/并发恢复只一move；真实S05演示快照20→调价99后仍原20/原版本；observed盘点事件恢复拒绝|
|S07-T07|PASS|两同法人门店+第三跨法人店；reader/none/warehouse/stock-manager/medical/pharmacy/price/master分离；跨店写、患者/附件/public、native search/read/CRUD/export、旧revision及实时撤权拒绝|
|S07-T08|PASS（S07范围）|新库install42/upgrade40；盘点差额与零差额、同法人调拨真实native move且保留lot、目标授权；带已提交业务数据再次真实-u后ledger签名守恒|
|S07-T09|PASS|三类库位、主数据/price/warehouse拆分；默认policy未配置、低库存按有效batch汇总、近效期/过期、真实入库当地日期边界和首次日期不重写、仅药房权可信发出/实退；scan fail-closed；S01审计和普通删除拒绝|
|T06真实S08临床及S10费用链|NOT_RUN|未授权/未安装，仅可信hook及合成来源+真实S05演示快照契约|
|T08跨法人完整成对交易|NOT_RUN|本批实际拒绝，完整交易由S10联调|
|S11真实加工单/扫码到货|NOT_RUN|无上层模块，stable reference字段及识别钩子，不返回入库成功|
|生产阈值、50会话、正式部署|NOT_RUN|参数待发布，性能/生产责任阶段另行验证|
|GPT技术复核/用户验收|NOT_RUN|本次为Codex交付申请，不替代独立复核/统一用户验收|

最终汇总：install **42**（其中S07 **40**＝模型29+真实HTTP/RPC11，另2为原生web资产初始化；不将资产初始化称完整浏览器测试），首次upgrade **40**；带业务数据再upgrade **40**。全部0failed/0errors、exit0。12/12真实双连接竞争，deadlocks=0；Firefox36项/10图、pageerror=0；翻译218/218、guard5均PASS。S00—S06测试源码未改，但本批未重跑所有旧阶段全套UI/并发，不能冒称全项目验收。

## 可重放的运行与效果步骤

使用固定test提交、核心`.venv/bin/python`，命令工作目录为sd-addons；db须每次生成新的`ydental_s07_test_14位UTC时间_8位hex`。不能用已存在库执行install，不能把下面命令改成历史/业务库。runner读取已有私有核心连接配置，不在Git或报告放密码。

```bash
../.venv/bin/python scripts/s07.py install --db "$S07_DB" --port 18142
../.venv/bin/python scripts/s07.py upgrade --db "$S07_DB" --port 18142
../.venv/bin/python scripts/s07.py probe --db "$S07_DB" --port 18142
../.venv/bin/python scripts/s07.py export --db "$S07_DB" --port 18142
../.venv/bin/python scripts/s07_translation.py --db "$S07_DB"
../.venv/bin/python scripts/test_s07_guard.py
../.venv/bin/python scripts/s07.py serve --db "$S07_DB" --port 18142
# 另一个终端，只操作以上匹配PID/config预览
../.venv/bin/python scripts/s07_browser.py --db "$S07_DB" --port 18142
# 停止已证明属于本次config/PID的预览后，audit → upgrade → audit
../.venv/bin/python scripts/s07.py audit --db "$S07_DB" --port 18142
```

probe自建真实库存/独立连接及全新合成UI夹具；私有access.json只保留本机0600。Firefox不是静态截图或单线程伪并发；36项检查包含真实表单POST、原生RPC拒绝和多个角色。两次运行同一browser流程会消耗原fixture，不可重置旧业务记录；需要新fixture时使用guarded `preview`，保留旧记录。

用户效果回放（仅隔离演示，非用户已验收）：

1. warehouse-write账号在S01选当前门店，打开 `/ydental/inventory`；查看三类批次、实存/可发/待核查及策略提示；集团主数据入口另为 `/ydental/inventory/catalog`。
2. 本次夹具的药品有效批次实际收货10可见；选择真实批次与单位，确认实际领用3，页面可发7。
3. 重发原请求仍原event/move，可发仍7；不是新申请刷新数量。
4. 按原出库实退1，只增加待核查1，可发仍7；核验release后才可发8，discard则不回可发。
5. 退款请求不属于库存动作，拒绝且库存不动；停用批次后手工POST出库也被拒绝。
6. material合成已做缺料事件显示pending/责任人；不足恢复拒绝，原事件保持；仓管实际入库5再恢复原事件2，可发3，只一move。
7. reader可看无写表单，手工写拒绝；warehouse无患者全文/附件/native批次/quant/export绕过；master可维护主数据而无库存读。
8. 查看义齿首次真实入库日期/待取标志和近效期；未装S11扫码明确返回unsupported/未入库。

10张最终截图已逐张目视核对，均为合成资料；截图、sha256与36项检查结果一一保留。早期Firefox把正常303跳转误判为失败，动作实际已提交，未重置旧库存；修正脚本并新建fixture后通过，原失败仍在证据目录。

## 数据、审计、升级和回滚

新增模块/字段/约束，不改S06表语义，不迁移或接管旧隔离/业务库。本阶段不存在已发布旧S07生产schema；安装从全新库执行，升级为真实 `-u ydental_inventory,ydental_inventory_test`。probe/Firefox持久业务事实之后再次-u，event/batch/move/move_line/quant五组签名前后相同，不删除/重建库存事实。不能把这项说成完整旧S06源码树生产迁移。

最终native trace展示真实lot→event→move/move.line→quant及S01movement审计。只读检查7类不变量均0：负internal库存、来源重复、半事件、event/move不符、movement审计不唯一、quant与done move.line不守恒、quant归店不符。演示缺料事件在复核前仍可保留pending，无量强制补库；有move事件每个恰一movement审计。

业务回滚：失败动作由savepoint原子回滚；成功历史不通过删move/改quant回滚，按实际实盘修正、实退核验及有据调拨追加反向事实，临床/原价不抹除。代码回退须先停止本次新预览并审核新数据与依赖，不在有S07库存事实的库直接降级卸载或重置；本批没有做破坏性卸载/删库。历史失败库/文件继续保留，不默认生产回滚已验证。

## 失败链、限制与复核申请

完整运行尝试、各提交/退出码/测试计数/原日志hash见actions-summary.json；不发布原日志、配置、token/cookie或凭据。主要链包括首次ACL CSV字段名错误、native confirm自动建议行未指定lot、负向夹具预期错误、S05调价时间夹具错误、Firefox303误判，以及证据脚本工作目录误记核心SHA；均有原记录，修正后最终全新库再验证。早期probe/invariants中tested_commit为核心SHA的两次记录元数据错误，不据此冒称核心库存测试；对应runner actions记录实际addon HEAD，最终脚本显式git -C repo修正并重跑。

安全核对还冻结原生单位存储factor/祖先路径、收紧observed盘点不能走临床pending恢复，清理未使用原生lot重复启停/入库/加工字段，只以store×lot batch为生命周期权威；新增模型/HTTP负向均通过。最终功能/权限/库存不变量回归通过。最终Firefox首次登录选店后专属预览子进程SIGSEGV退出（runner245，尚无库存动作）；只读核对仍10份后，仅重启本次专属预览并开启进程本地fault handler，再跑36项/10图通过。该次底层崩溃原因尚未确定，未改核心/依赖，详见preview-recovery.json和原失败result；不能据重跑通过声称根因已修复或生产稳定性通过，交GPT复核裁定。生产参数、真实临床/发药/检查、收费退款/跨法人交易、加工来源、50人性能及生产部署均未执行。交付只申请GPT技术复核，#31保持OPEN/进行中/Todo，不改待用户验收、不关闭/合并/强推，不启用S08。
