# S10 D1.8-P1-D0：四项副作用与全局组离线审计

## 身份、范围与结论

唯一授权为 [#34 评论 6166219654](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166219654)，上一批失败交付为 [6166122665](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166122665)。本轮从 `6d5905a175023d49ec6cde4d89644186f93b4ebc` 沿原分支前进。旧 S10 产品审核基线 `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、固定测试 `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。当前 S07 候选文件 SHA256 为 `633da04a93a4ba4f9d28dd748838833558b7f3b45c22d3ac5090d9baaddc8807`，仍 **NOT_ACCEPTED**；本轮未编辑它。

GitHub API 明确 GET 读取 #23/#29/#31/#34 正文及全部有效评论，数量分别为 3/7/8/65，最新 #34 评论为本轮授权；#35 OPEN/0 评论。开工 origin、分支、远端 HEAD、工作树、venv Python 3.12.15 和 core 匹配。独立 postgres 管理库只读事务及 5 秒 statement timeout 核对 `127.0.0.1:5432`、cluster `7694897083368259627` 和七座固定库的 OID/名称：2056451、2100080、2100086、2100087、2100096、2100105、2100114。首次人工抄写两座失败库名称的只读断言返回 `expected_match=False`；独立 `pg_database` 实值表明 OID 未漂移，改正**本轮只读脚本中名称期望**后七项完全匹配，未改任何库。P1 私有 config/marker/GDB 日志及夹具 SHA 重算分别为 `e5aa67ce…313eac4`、`469f66a0…44abd`、`42c6b516…b0d37d`、`a6c794ac…3209f`。旧现场未动。

本轮没有新增事故库或 P1 库业务聚合查询，因此无需新 GitHub 查询检查点；只用了授权允许的 postgres 管理库身份 SELECT。Odoo/GDB-Odoo/Firefox 进程 **0**，CREATE **0**，配置/业务写 **0**。

## 旧复合断言能证明什么

旧私有 `p1_fixture.py` 第 69—79 行的 `_counts` 用**同一个 Odoo `env.cr`** 对整个数据库表做 `SELECT count(*)`，不加公司、门店、记录来源或时间域。第 198 行在建合成记录前取 `baseline`；第 203—206 行在 `_build` 创建合成门店、用户、已发布价和快照后取 `before`。第 291—312 行执行唯一 A 场景 S07 `setup`、重复幂等请求、价源/quote 和 S05 guard 负向；第 313—316 行取得 `after` 后把四项条件合在一个 `or`，立即抛出异常。`run_once` 第 359—368 行每个场景用独立自有 cursor，`finally` 回滚，且**只在场景返回后**写进度文件。旧 A 因断言未返回，事务内四个分量、`before` 及 `after` 都没有保存。原 GDB 日志 SHA256 `42c6b516…b0d37d` 只证实 `_scenario:316` 的异常、Odoo exit1、无实际 SIGSEGV。其前的个别断言虽按控制流越过，不能替代完整场景 PASS。

|分量|旧判据/作用域|已固定模板基线；失败事务内|可由源码提出的来源；意义|分类|
|---|---|---|---|---|
|`mail.mail`|`after != before`，全表、同 cursor；非增量快照持久记录|纯92模板及 P1 回滚后均 **0**；`before/after` **UNKNOWN**|`new_test_user`/原生 mail hooks 可建待发队列；队列行不等于已对外发送。新增未获解释须 STOP，并单独核对外发轨迹。|模板数 **OBSERVED**；事务内 **UNKNOWN**；自动队列仅 **STATIC_POSSIBLE**|
|`bus.bus`|`after != before`，全表、同 cursor；未看 precommit 队列|模板及回滚后均 **6**；`before/after` **UNKNOWN**|仓库原生 `stock_group_sync` 会调用 `_bus_send`，先形成 precommit **意图**。该调用本身不会立即证明 `bus.bus` 行增加；直接创建或其它路径仍需查来源。内部通知也不等于 SMTP 外发。|模板数与源码路径 **OBSERVED/STATIC_POSSIBLE**；事务内行数及触发者 **UNKNOWN**|
|`account.payment`|`after != 0`，全表绝对值；不与 `before` 比较|模板及回滚后 **0**；事务内 `after` **UNKNOWN**|P1 不主动调用收款；仍应将任何事务内原生付款对象列为硬 STOP，不能靠回滚豁免。|模板数 **OBSERVED**；触发者与事务内值 **UNKNOWN**|
|`account.partial.reconcile`|`after != 0`，全表绝对值；不与 `before` 比较|模板及回滚后 **0**；事务内 `after` **UNKNOWN**|P1 不主动核销；任一事务内应收核销对象为硬 STOP。|模板数 **OBSERVED**；触发者与事务内值 **UNKNOWN**|

旧 `mail.message=851` 是系统模板基线，不属于复合断言，也不是 SMTP 发送次数。回滚后的四项基线相同只证明**没有留下相应已提交行**，不能倒推失败瞬间四项均为零。`bus.bus` 旧基线 6 必须按各动作增量和来源解释；绝不把所有 bus 意图放行，也不把合法内部意图自动判为违规。

## 原生 bus 与权限组真实路径

锁定 `addons/bus/models/bus.py:92-109`：`_sendone` 把 `(channel,type,payload)` 放到 `env.cr.precommit.data['bus.bus.values']`。第 118—137 行 precommit hook 筛选载荷并 `sudo().create` bus 行；第 139—170 行注册 postcommit，**提交后**通过独立 `db_system` cursor 发 `pg_notify('imbus', …)`。`bus.listener.mixin:15-22` 把用户目标交给 `_sendone`；`stock.warehouse._check_multiwarehouse_group:319-325` 组切换时发 `stock_group_sync`，前端 `stock_warehouse_service.js:6` 订阅后重新加载 context。四层须独立记录：未提交意图、事务内可见行、提交持久行、提交后通知。mail 队列与这些不是同一种对象。上轮没有 precommit 意图快照，也没有四项事务内计数；不能宣称该 bus 意图一定就是失败原因。

当前候选 `ydental_inventory_service.py:157-202` 在 S07 原 `_access('warehouse','write')`、幂等键和 savepoint 后，若全局多仓库组需要切换，要求原执行环境 `env.is_system()`，再用 `group_user.sudo()._apply_group(multi_location)`；后续原生 `stock.warehouse.create` 可追加 multi-warehouse 组。`res.groups._apply_group`（core `res_groups.py:399-404`）执行 `groups.write({'implied_ids':[Command.link(...)]})`，不是门店配置。`base.group_user` 是所有内部用户基础组（`base_groups.xml:26-29`）；其 implied group 的变化会影响跨公司/跨门店内部用户的有效权限。`res.groups.write:229-271` 清理访问缓存、约束/组闭包计算并可能运行 `_apply_group_regular`；改变内部组集合时还可批量重算 `res.users.share`/`res.partner.partner_share`。是否每次真的触发每支重算及通知数值，**本轮 UNKNOWN**；必须实测前后全局 implied_ids、实际用户有效组和模块状态。

`env.is_system()` 是 Settings（`environments.py:187-190`），`env.is_admin()` 是 Access Rights（第 182—185 行）。基础组 XML 中 Settings 隐含 Access Rights（`base_groups.xml:37-50`），故 Settings 用户通常也满足原生 `res.config.settings.execute` 的 `is_admin`；反向不成立。原生 `execute`（`res_config.py:347-402`）检查 `is_admin`，调用所有 `set_values`，并可能安装/卸载 `module_` 字段；product `set_values`（`res_config_settings.py:38-45`）在 pricelist group 未启用时全量归档价目表，S05 guard 拒绝受控价写。原生仓库 `_check_multiwarehouse_group:308-325` 按**所有公司中最大活跃仓库数**切换全局组；即便当前创建在一店，也不是一店的权限变更。仓库创建还会建立库位、route、规则与操作类型（`stock_warehouse.py:114-162`）。数据库异常可回滚普通行和组关系；缓存/文件、SMTP、已提交后的 bus/邮件、模块生命周期不能未经证据假定全部可回滚。

**安全建议，不修改产品：**全局多仓库与多库位组由有 Settings 权限的真实管理员按明确政策决定，记录跨法人影响、模块状态和通知；普通 `warehouse:write` 仓管在需要全局组切换时保持 fail-closed。不要赋予仓管 Settings，也不要以 sudo/假 mutation 绕过 S05 guard。当前候选可作后续复核输入，但保留、撤销或改写须新的 GPT 明确授权；不能按本轮模拟接收为产品版本。

本轮代码复核的未闭合项（未实施修正）：

|严重度与位置|具体场景|后续最小处理；审查依据|
|---|---|---|
|高：`ydental_inventory_service.py:179-185`|本店 Settings 管理员请求第二仓库，`group_user.sudo()._apply_group` 同时改变其它法人全部内部用户的有效组；现有授权只是操作者组检查，缺正式跨公司配置政策和完整 group/通知审计。|由正式管理员明确执行全局设置并记录集团影响，或另获授权设计受控的显式配置步骤；Odoo Security **Don't over-sudo**、本批权限影响判断。|
|高：同文件第 173—185 行与 `stock_warehouse.py:308-325`|S07 自有锁只能串行化本服务；并发的原生仓库创建可能在预判后改变全局计数/组，使后续 sudo 原生路径再次进入 `res.config.settings.execute`。本轮仅静态可提出，未实测。|后续测试必须含原生与 S07 交错、再次执行 settings 的监测和失败回滚；需要先明确全局组生命周期。审查依据：**Transactions and exceptions**、**Don't over-sudo** 及并发判断。|
|中：同文件第 180 行|`env.is_system()` 与原生 `execute` 的 `env.is_admin()`范围不同；有 Access Rights 而无 Settings 的用户在候选被拒绝。此收窄符合审慎边界，但是否为正式权限政策尚未批准。|继续 fail-closed；后续产品授权明确谁可改变全局组，不以普通仓管的 `warehouse:write` 自动提权。审查依据：**Access control** 与权限判断。|

审查范围：固定提交 `6d5905a` 对比 `4ceb3ef` 的唯一 S07 产品 hunk，`ydental_inventory/__manifest__.py` 与锁定 Odoo20 core；没有 enterprise 对应仓库可据以测试。**Guidelines read:** Odoo guideline Imports、Naming and model layout、Translate only static literals、Recordsets/domains/context、Methods and extension points、Transactions and exceptions、Batch ORM calls、Performance conventions、Plain ASCII punctuation；Odoo Security Access control、Don't over-sudo、public methods、raw SQL 及其它静态 sweep。此处仅对本批问题给出发现，不把未执行的全模块审计称为完成。

## 四分量诊断契约与下次试验门槛

新增 `scripts/s10_d18_p1_d0_contract.py` 是**纯 Python 离线模拟**，`FUTURE_AUTH_COMMENT_ID=None`，没有 Odoo/PG 导入或连接入口。它分别输出 `mail_mail_delta`、`bus_bus_delta`、`account_payment_delta`、`account_partial_reconcile_delta`、bus precommit 意图数量及 rollback 是否恢复。13 个场景加缺字段负向共 **14/14 SIMULATED exit0**：全零、合法内部意图、mail 新增、付款、新核销、多项同时新增、历史 bus 非零但增量零、回滚后恢复却事务内曾异常、无权仓管、跨公司组、未知外发/未知 bus 意图、bus 行无来源及缺分量。模拟里的“合法意图”也只标 `NEEDS_REAL_PROVENANCE`，绝不表示产品通过。

若未来另获单库运行授权，夹具必须在自有 cursor **开始**保存四项基线，在创建合成用户/价格后及每个受控动作后分别保存四项值与无敏感来源摘要；读取 `env.cr.precommit.data.get('bus.bus.values',())` 仅记录白名单类型/目标类别/计数，不输出载荷或用户身份。每个动作的分量结果须**在断言前**以 700 目录/600 文件写入且 fsync，异常仍保留；与 savepoint 的回滚结果及独立只读提交后状态分别核对。任何 payment/partial 增量立即硬 STOP；mail 队列或 bus 行/意图只有来源、作用域、时序解释充分才考虑允许，否则 STOP。不把 `mail.message` 当邮件发送，也不设全库绝对阈值；需记录模板基线、新增内部消息来源、mail.mail/outbound、ir.attachment/filestore 文件 SHA 及对外网络 guard。

四组未来**真实**场景仍均未通过，且须分别报告：

|场景|独立正负验收焦点|目前状态|
|---|---|---|
|A：本店已发布 S05 价后新增 S07 仓库|价目表与 rule active、原 quote/快照不变；warehouse/库位/route、S07 操作审计成立；重复 setup 幂等；非法直接 price.write 拒绝。若新增仓库必须改变全局组，需明确管理员行为与通知。|旧 P1 仅部分到达复合断言；**BLOCKED**|
|B：同法人两店及跨法人|B 店仓库不改变 A 店价源；跨店旧页/RPC、无 warehouse:write、跨公司创建拒绝；全局组跨公司影响单列，不能把它当作 B 店本地字段。|**NOT_RUN**|
|C：普通原生与 YD 受管价共存|原生普通价表是否改变必须有原生生命周期或审批依据；受管价/规则绝不静默归档，原 quote 保持；未授权配置变更拒绝。|**NOT_RUN**|
|D：multi-warehouse、multi-location、pricelist group 的不同初态|逐个组合记录前后 implied_ids、有效用户组、模块 installed、`execute` 是否被调用；不一致组合应安全拒绝，合法组合不越权或归档受管价。|**NOT_RUN**|

每组要在独立 savepoint 核验价目表/rule、历史 quote/快照，warehouse/业务库位/route 和 S07 audit，全局 implied_ids 与受影响公司用户的有效组，模块 installed，account.move/payment/partial，mail.message 增量、mail.mail 和 bus 意图/行/通知来源；附件/filestore 未知文件即 STOP；失败回滚后独立核查无半仓库/半价格/半账。真实 confirmed fee 不在上一批无治疗授权范围内，仍为未测。先证明监测契约能在**失败前**保存分量，再由 GPT 决定是否值得另批单库实验；本轮不执行。

## 命令、证据与保全

实际命令/退出：`gh api -X GET` 四 Issue 正文与两页评论及 #35 exit0；Git/core/venv/远端核对 exit0；锁定源码 `rg`/`nl`/`sha256sum` exit0，最初两个 `rg` 使用错误相对路径 exit2 后只纠正只读路径，保留失败史；`../.venv/bin/python` postgres 管理库 SELECT 第一次期望名称不符但命令 exit0、布尔 false，纠正只读期望后 assert exit0；`../.venv/bin/python -m py_compile scripts/s10_d18_p1_d0_contract.py` exit0；离线模拟 14/14 exit0；AST 禁止 Odoo/psycopg2/socket/subprocess 导入且授权常量 None exit0。未读取或导出新库业务明细；无新业务 PG 聚合。

原 P1 私有 `p1_fixture.py` SHA256 `a6c794ac94b676e2a6e1b110b5540c2093cc8e3e442d1238a89ec50c7993209f`，原 GDB 日志 SHA256 `42c6b5169c227adbd81e5b39909c43551545f4556887a8c8ef32528521b0d37d`；原始文件留 `.local/s10-d18p1-20261014-6165734052/` 与 `.local/ydental_s10_test_20261014100600_d18a9c4e/`，权限私有。GitHub仅本报告、纯离线脚本和脱敏 JSON。事故/纯92/L1/三座L2失败/P1失败数据库、全部 filestore、volume、日志、core 与备份原样保留；未清理上轮两份孤立文件。

本轮 Project mutation **0**、#34不关闭、#35/S11未启用、未合并/强推/部署。S05×S07兼容 **UNRESOLVED**，S10技术与生产持续 **BLOCKED**，原 Native SIGSEGV 根因仍 **UNKNOWN**。本报告是 Codex 离线审计与设计，不是 GPT/用户验收。
