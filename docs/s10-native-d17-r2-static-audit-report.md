# S10 Native D1.7-R2-0：L2 前置闭合与队列配置静态审计

## 1. 授权、身份、范围

唯一授权 [#34/6164444983](https://github.com/Yredxin/YDental/issues/34#issuecomment-6164444983)。原分支 `codex/s10-settlement-finance-r1-20261013`，开工本地/远端 HEAD `7495120e9165aca7d6a9a2bbd68eb60b9ac27bb8`、工作树干净；固定 S10 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 均不改。Ubuntu venv Python 3.12.15。API 显式 GET 读取 #23/#34 现行正文及全部评论（分别3/55条）、授权评论逐字一致；#35 OPEN、0评论，#34 最新评论就是授权，无更晚裁定。GitHub正文、评论原响应保存在新700私有目录，文件600。

只读 PG 管理库 `postgres` 核对 endpoint `127.0.0.1:5432`、cluster `7694897083368259627`：原事故OID2056451、纯92模板OID2100080、L1 OID2100086、两次L2失败OID2100087/2100096全匹配。没有读取任何历史库业务表或`ir_config_parameter`值；**队列配置值PG查询0，因此无需且未发布可选的事前PG配置查询检查点**。没有 CREATE、配置写、业务写、Odoo/GDB-Odoo/Firefox进程。旧数据库、卷、filestore、core、日志、备份均未修改或清理。

## 2. 两次真实失败的因果边界

第一失败OID2100087：旧私有`l2_fixture.py`先正式S05 `_price`，后S07 `_setup`。锁定 `ydental_inventory_service.py:164` 调原生 `stock.warehouse.create`；`addons/stock/models/stock_warehouse.py:160,310-325` 第二仓库配置触发`res.config.settings.execute`，`addons/product/models/res_config_settings.py:38-45` 在价目表组关闭时归档活跃价目表，`ydental_intake/models/native.py:43-60` 阻止未持有真实服务mutation令牌改已受控S05价目表。GDB日志SHA `2961e7042afd54125f5c1839f411bf69dc3e60fd25a7c0de549bd10507a9e666`。此是价源/仓库顺序造成的真实保护拒绝，不是Native根因。

第二失败OID2100096：R1私有夹具将唯一仓库setup置于S05价格前，GDB shell执行到`front._operate('report')`，`ydental_queue/models/ydental_intake_service.py:93-97` 在队列接受之前调用`ydental.queue.service._settings`，后者从两个空默认的配置键读入并在`int('')`处抛`configuration_required`。GDB日志SHA `7003652da2b2cd9aecd14c0ed3298423638bcf125897fdd30bf170d1f30b9071`；目标 exit1、无signal11。R1私有夹具SHA `0123ae7a9392680a08cf41bd06f85926d42c40a9ddc682537ec544d7330b3641`，与前版SHA `72d76cd84b0d78e28fd454ad65f66ec6d7988672f3f21203c30ec8c4daca6cbb` 的顺序diff原样保留。**遗漏原因**：R1仅调整已知价源冲突，静态检查覆盖仓库/价格guard和事务后验，未把`common.py:87-88`显式队列参数设置及`treatment_common.py:13`延长timeout纳入真实`report`闭包；一段已存在的测试辅助setup被缩小为私有L2夹具时漏掉了此配置节点。此前离线测试只验证旧已知顺序，未跑原`_settings`负向。两个失败库各有6个未引用filestore文件，来源仍UNKNOWN，全部原样保全；数据库回滚不能推导文件副作用为0。

## 3. 完整最小方法图与配置闭包

[逐方法依赖和副作用矩阵](s10-native-d17-r2-dependency-matrix.md)列出S01员工/门店/HR/会话/权限、S07仓库/product/lot/收料/耗用、S03空间/策略/本地日/slot、S05目录/映射/价目、S06资格/报到/队列、S08文书/执行/快照/fee的源码行号、角色、前置、幂等键、记录、原生/邮件/bus风险、失败保护及与Native事故的关系。锁定源码的必要顺序是S01选店授权后**先唯一S07仓库setup**，再正式S05受控价目表；S06 queue参数必须在首次`report`（其`_queue_accept`会调`_settings`）前显式发布。S07收料必须早于S08实际耗用；S03已发布槽和本地business open是预约/报到前提；S08真实已保存文书版本、医生/工位capability、当前租约和S05有效价格是确认费前提。不能用直接SQL伪造这些事实。

配置闭包静态扫描范围是矩阵所列YDental模型和本次会触发的Odoo仓库/产品设置源码：

|配置/策略|实际位置|本夹具处理与状态|
|---|---|---|
|`ydental_queue.heartbeat_seconds`、`timeout_seconds`|`ydental_queue_service.py:51-60`；首次`report`由`ydental_intake_service.py:93-97`调用|**必须提前显式发布**；未来仅新授权合成库可用`set_str('2')`/`set_str('600')`，并立即读原函数确认；生产未批准|
|`ydental_missed_limit > 0`|`ydental_queue_service.py:312-320`|私有夹具care area设2；字段不是全局配置，生产N未批准|
|S03 demo supply政策与business open|`ydental_supply_service.py:174-217,345-401,481-515`；测试适配器`ydental_settlement_test/models/ydental_supply_service.py:7-12`|须显式创建；纯92模块适配器调用原`pre_init_hook`，不能绕过|
|S05价格与发布|`ydental_intake_service.py:263-332`、`ydental_treatment_service.py:429-439`|正式服务review/publish，执行只用demo_confirmation；生产价政策未批|
|S07仓库配置与有效lot|`ydental_inventory_service.py:75-117,157-177`|仓库先于受控价；lot有效/同店/数量可用|
|患者编号sequence|`ydental_patient_service.py:204-220`|真实Odoo序列存在才可创建；未测试动态损坏情形|
|`ydental_access.manager_policy`|`ydental_access_service.py:124-130,511-512`|当前私有夹具未调用任免/离职，故不需私自发布|
|`ydental_space.svg_max_bytes`|`ydental_space_resource.py:83`|仅SVG上传；本夹具不上传，非本次闭包|
|原生多仓库/价目表设置|`stock_warehouse.py:310-325`、`product/res_config_settings.py:38-45`|可变更原生group并发bus同步、可归档价目表；需未来独立后验|

`ydental_queue_push.py:75-117`说明队列对象创建/状态变化可产生scope/outbox与内部`bus.bus._sendone`；`stock_warehouse.py:318,325`也可发内部group同步。`new_test_user`、原生warehouse/stock/HR/mail、原生文件存储可产生间接副作用，静态扫描不能穷尽。未来必须loopback/禁SMTP/cron0并以实际SQL/文件SHA核对；任何无法解释的邮件、posted会计、原生库存超额或孤立文件即STOP。S03 floor/area/station在旧私有夹具中由sudo ORM直接创建，仅为合成基础设置；真实库存/临床/费用事实仍通过现有服务API。

## 4. 原 `_settings` 函数体的离线验证

[安全测试脚本](../scripts/s10_native_d17_r2_queue_stub.py)使用AST提取并编译未修改的`ydental_queue_service.py:51-60`真实函数体，在纯Python FakeEnv/Params中运行，非重写相似谓词。源码SHA `a5b3a037a2be9992edf5867b3d401b351e4a74820d36fcc8764d46e0cc1c2a6e`；`py_compile` exit0，运行 exit0：2/20、2/600、1/86400共3正；缺双键、缺任一键、空字符串、两种非数字、heartbeat0/负数、timeout等于或低于heartbeat、timeout86401共12负，均由真实函数体抛原`configuration_required`。标记**SIMULATED_ACTUAL_AST_BODY**，不是Odoo运行或生产参数批准。值2/20来自`ydental_treatment_test/tests/common.py:87-88`，2/600来自`treatment_common.py:13`；Python helper代码可供静态参考，不意味着将`ydental_treatment_test`插件装入S10库。

新私有权限700/600目录中保存的下一轮完整夹具草案 `future_l2_fixture_draft.py` SHA 4966f710c4f6b801537f689da7637defad1126470f808b7dae3521c895e67d94：`FUTURE_AUTH_COMMENT_ID=None`、目标库和fixture_key均无效；`run_once`首先抛PermissionError。它提出在S01之后、首次`report`之前显式写两键，立即调用原`_settings`验证2/600，继续只经真实服务构造event/fee/库存，保留单次attempt ledger、OID/cluster/core/config/marker/source_oid/网络guard和自有cursor内重新验证。其后验清单要求account.move/payment/partial、S10 source/payment/refund/close、mail_mail均0，唯一event↔fee↔S05快照↔S07 done move，且每个新增filestore SHA与附件来源可解释。公开[不可执行设计](../scripts/s10_native_d17_r2_draft.py)也将授权和目标留空、`run()`固定拒绝。私有AST/mock检查 `py_compile` exit0、17正2负 exit0（SIMULATED），旧R1漏两键及原失败日志负向被核实；公开草案执行闸门模拟拒绝 exit0。未执行任何未来写入代码。

## 5. 技术结论与下一步条件

在现有服务保护下，最小L2状态**有合理合法路径，但尚未被真实构建证明**。静态上未发现必须新增患者/门店或突破S05/S07/S06保护的依赖环；动态原生配置、HR/mail/bus/filestore、门店时区、当前slot/lease时序和库存估值仍UNKNOWN。为避免第三次因基础配置失败，下一轮若获授权，应在任何CREATE前由独立复核逐节点核对本矩阵、实际queue函数体测试、原生仓库价目表组状态、漏配参数负向、试验时长与lease超时、后验文件/会计边界。不能预填授权ID、复用旧失败库、边跑边补值或将静态PASS写为Odoo PASS。

未来是否授权一座新纯合成库（CREATE≤1、准备Odoo≤1、双独立GDB只读shell≤2）应由GPT根据依赖覆盖和事故前置相似度另定；旧R1未消耗B配额**不可继承**。若动态未知无法安全控制，应暂停L2复现方向，先独立解决S05受控价目表×S07第二仓库产品兼容风险；A顺序规避不等于B真实反序业务问题已通过，**B仍UNRESOLVED**。原事故SIGSEGV位于actor业务stdin之前，L2数据只增加环境相似度；实质推进Native归因仍需真正signal11时的C线程栈、共享库映射/Build ID、两个OS及PG PID与registry重叠时间线。未复现不能证明修复。

## 6. 实际命令、退出码、证据与治理

|命令类别|实际结果|
|---|---|
|`git` origin/branch/HEAD/status/ls-remote、Odoo core SHA、venv版本|exit0；固定身份匹配|
|`gh api -X GET` #23/#34/#35正文、分页评论、授权评论|exit0；授权逐字一致、#35 OPEN/0|
|独立psycopg2管理库只读OID/cluster断言，5秒statement timeout|exit0；五个固定OID匹配；**未查queue键**|
|`sha256sum`两失败GDB日志/ledger/夹具|exit0；见脱敏机器索引|
|现存源码`rg`/`nl`及配置闭包检索|exit0；本矩阵所列固定行号；一次误用不存在的`ydental_intake/models/ydental_supply_service.py`路径未产生证据，随后按实际`ydental_supply/...`核查|
|`python -m py_compile`私有stub/草案及公开脚本|exit0|
|原函数体AST stub、私有AST/mock与公开草案硬闸门|各exit0，全部SIMULATED|

本轮私有原始材料目录 `.local/s10-native-20261014-6164444983-d17r2/` 权限700、文件600；授权正文SHA `4817276d5810be2efb32dd3c0b563a795e33bcdcd4ad2bfb01ad122deeaea67a`、私有stub SHA `c6e5b14843f63b22613f8797c3e69d1403a643050ce1bdb9937c1e9890fdf9ba`、私有模拟脚本SHA `6f3e416a8930aa090f87e0854f4b36d1b5328777b7fff7cb8ce3e9662cdba3c6`。两个旧失败库的各6个额外未引用文件、所有历史库/filestore/卷/core/日志保全，文件来源UNKNOWN且未清理；相对纯92模板124文件，OID2100087和2100096各为130文件/额外6，额外文件名与SHA的合并清单摘要分别为 `3ea6a8ea79749431fe34dc9b926f9b874c8577f88b59ce2506353736158104f0`、`31f971d8c6c9a0c5a36d6c1adfa78f8e81b9cfde7a1f34f783c3ae98053db89d`。本轮Odoo0、GDB-Odoo0、Firefox0、CREATE0、配置写0、业务写0；Project零修改、#34 OPEN、S11未启用、未合并/强推/部署。**S10技术及生产持续BLOCKED，Native根因仍UNKNOWN。**
