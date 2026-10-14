# S10 D1.8-P1-R1-S0 合成用户通知与文件源头只读审计

## 授权、身份、边界

唯一授权为 [#34 评论 6166877292](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166877292)，上轮交付为 [评论 6166791285](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166791285)。本批起点与当时远端 HEAD 为 `b7e2c75a2dc9093fb68e13ff83d32b046c74bd4c`，分支 `codex/s10-settlement-finance-r1-20261013`，起始工作树干净。Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，Python 3.12.15；S07 候选文件 SHA256 `633da04a93a4ba4f9d28dd748838833558b7f3b45c22d3ac5090d9baaddc8807`，本批未修改。

GitHub GET 完整读取 #23/#29/#31/#34 当前正文和全部有效评论，分别为 3/7/8/70 条；最新 #34 评论正是 6166877292，其评论 GET 正文与分页列表逐字一致。#35 OPEN/0评论。PG 管理库只读身份查询确认 127.0.0.1:5432、cluster `7694897083368259627`，历史 OID2056451、2100080、2100086、2100087、2100096、2100105、2100114 及本批旧新库 OID2100123 均匹配；没有新增目标业务查询，因此没有额外 PG 查询检查点。

本轮 CREATE0、Odoo/GDB-Odoo/Firefox0、产品修改0、配置/业务写0、Project 修改0。没有触碰任何历史库、filestore、日志、core 或备份。

## 真实旧观测：保留了什么，丢失了什么

上一轮私有 `observation-Aprice-after_settings_user_create.json` 原 SHA256 `0b44de0515ed45489a4fdf05c8f003d808451f20eefa90258a1b714d07ded2ef`，权限600，未修改。记录中唯一意图为 `scope=settings_actor`、`target_model=res.users`、`type=other`，数量1；目标 ID、载荷均未输出。四项事务内计数仍为 mail.mail0、bus.bus6、account.payment0、account.partial.reconcile0；mail.message853，较基线851新增两个内部消息（res.partner、res.users）。旧 GDB 日志 SHA256 `607dca2b67288c23a57177ebaa08177fe930410bf1b4ba113b7c530c614a5a62`，记录 Odoo PID2683611、PG PID497372、`after_settings_user_create` 断言退出1，未见 signal11。

**PROVEN**：旧私有诊断器 `.local/s10-d18p1r1-20261014-6166455763/p1_fixture.py:83-95` 从 `cr.precommit.data['bus.bus.values']` 取出原始 `kind`，但第92行仅在 `kind == stock_group_sync` 时保留，否则写为 `other`。原始事件类型既未存入 JSON，也未见于旧 GDB 日志；因此实际事件类型为 **NOT_CAPTURED**，不能从 `other` 逆推出 `mail.record/insert` 或任何其他类型。观察到的合成用户目标类别、所属阶段和数量不是通知生成调用栈的证明。旧 P1 四合一失败触发者仍 UNKNOWN。

## 锁定源码调用矩阵

下表的文件路径均相对 Odoo20 core checkout；各源码 SHA 收录于[机器索引](evidence/s10-d18-p1-r1-s0/diagnostic.json)。`PROVEN_CODE` 表示当前锁定源码可证明的调用关系，`STATIC_POSSIBLE` 表示缺少本次运行时分支证据。

| 路径与行 | 静态事实 | 与本次意图的关系 |
| --- | --- | --- |
| `odoo/tests/common.py:268-308` | `new_test_user` 设置 group_ids、公司、合成邮箱，经 `res.users.sudo().with_context(...).create`；上轮私有夹具在创建 Settings 用户后才调用观察器。 | 用户创建动作 **OBSERVED_LOG**；具体 Odoo override 分支未捕获。 |
| `odoo/addons/base/models/res_users.py:664-681` | `create` 调用 `super()`，为内部用户建 `res.users.settings`，为无图像内部用户调用 `partner._avatar_generate_svg()` 并写 `image_1920`。 | 头像候选 **PROVEN_CODE**，本次具体写入归属 **LIKELY**。 |
| `odoo/addons/base/models/avatar_mixin.py:79-88` | `_avatar_generate_svg` 用名字首字母、seed 色盘构造 SVG 字节。 | 两个文件的字节/路径核对见下。 |
| `addons/mail/models/discuss/res_users.py:14-17` | 用户 `create` 后检索其 group_ids 对应的受限 `discuss.channel`，调用 `_subscribe_users_automatically()`。 | **STATIC_POSSIBLE**；本次未保存命中的 channel/member。 |
| `addons/mail/models/discuss/discuss_channel.py:831-854` | 自动订阅计算新增成员并创建 `discuss.channel.member`；`_get_member_store_list` 给相应 bus channel 构建 Store。 | **STATIC_POSSIBLE**；频道身份及跨公司范围 UNKNOWN。 |
| `addons/mail/models/discuss/discuss_channel_member.py:259-303,429-436` | member.create 可更新 Store；成员的 `_bus_channels` 经 partner/guest 得到；`_get_member_store_list` 建立目标 channel 列表。 | **STATIC_POSSIBLE**，尚不能证实本次这一条意图来自这里。 |
| `addons/mail/tools/discuss.py:195-238` | `Store(bus_channel=...)` 默认通知类型为 `mail.record/insert`，调用 channel 的 `_bus_send`。 | 默认类型仅为 **STATIC_POSSIBLE**；真实 type **NOT_CAPTURED**。 |
| `addons/bus/models/bus_listener_mixin.py:15-25`、`addons/bus/models/bus.py:92-109` | `_bus_send` 将 record target 交给 `_sendone`；后者写入 precommit 意图，record channel 转换为数据库/模型/ID tuple。 | `res.users` 目标模型与此格式相符，具体上游源 UNKNOWN。 |
| `addons/bus/models/bus.py:118-165` | precommit 才可能建 bus.bus 行；postcommit 才通过独立连接发送 PG NOTIFY。 | 本次事务回滚，持久行保持6；不能把意图称为已发通知。 |
| `addons/mail/models/discuss/res_users_settings.py:49-64` | `set_volume_setting` 创建 volume setting 时能以 `mail.record/insert` 发送。 | 需要调用该方法；本次无调用证据，**STATIC_POSSIBLE** 但不能当作本次来源。 |

另外，`addons/mail/models/res_users.py:192-207` 的用户创建覆盖可能有 portal 跟踪；`addons/hr/models/res_users.py:177-195` 仅在 create_employee 参数存在时另建 HR 员工。旧夹具未给 create_employee，不能把 HR 扩展认定为本次原因。`addons/mail/models/discuss/res_groups.py:8-13` 的组写也可能触发自动频道订阅，但本次组快照未变化。权限/跨公司审计结论：bus target 是本批合成 Settings 用户类别；频道、其他订阅成员、集团副作用仍无运行时证据，不能放宽全局组政策。

## SVG 与 GC checklist 的只读字节证据

旧新库私有 filestore 两个文件保留原位，未打开/导出敏感患者资料。305B 文件 SHA256 `1eb9b55f2eb2b4ec77289bd0e54a4d762071cf0787791edb431b2b222a21b648`；0B 文件 SHA256 为 SHA256 空文件 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。私有只读工具核对：

- **PROVEN 字节机制**：305B 文件与锁定 `avatar_mixin._avatar_generate_svg` 对本批合成用户名首字母的模板，在源代码定义的颜色集合中某一颜色下逐字节一致。其相对路径等于自身内容 SHA1 的 `前两位/SHA1`；符合 `ir.attachment._file_fname` 内容寻址形式。
- **PROVEN checklist 形式**：0B 文件的相对路径精确等于 `checklist/` 加该 SVG 相对路径；`ir.attachment._file_write:155-162` 在写文件前调用 `_mark_for_gc:230-244`，后者建立0B checklist。`orm/fields_binary.py:163-179,199-222` 说明附着 binary field 会创建 `ir.attachment`，`ir.attachment.create:921-960` 可调用 `_file_write`。
- **LIKELY 具体归属**：两文件 mtime 均在 GDB 记录的合成 Settings 用户创建窗口，源码的 `res.users.create` 有头像生成路径；但本轮无调用级 tracing、旧用户/附件行已回滚，不能把具体调用者称为已证实。前轮保存的独立只读 PG 汇总（SHA256 `d4f626e116b0cae6179c79518ab9479a324d32789a331a5898f2340a3d987c8c`）记录这两个相对路径在 OID2100123 的 `ir.attachment` 引用数0；本轮不重复查库。

文件原始相对路径、SVG 字节和任何用户值只在权限700/600目录。两文件仍原样保留；本报告只给安全文件大小、SHA、机制与证据强度。

## 未来事件白名单决策，不是本批放行

当前结论是 **STOP / NOT_CAPTURED**。现有 `type=other` 无法建立真实事件类型白名单。下一次若获新授权，必须先在另一个全新安全合成窗口被动、私有地保存原始事件类型常量及调用来源标记（不保存 payload、用户 ID、邮件或 token）；在事件发生动作前后记录可验证的合成目标角色及所属公司/门店类别。只有当真实类型、`res.users` 目标、唯一 Settings 合成用户、用户创建动作、上游频道/成员范围均有证据时，才可提出精确 `type + target category + source action + count <= 1` 白名单。该白名单仅适用于用户创建阶段；仓库 setup 的 `stock_group_sync`、全局组变更必须单独审计。任何未知类型/频道/跨公司目标、不明新文件、mail.mail、account.payment/partial 或非预期 bus.bus 增量继续 STOP。回滚后计数恢复不能抹去已保存的事务内异常。

离线 [分类契约](../scripts/s10_d18_p1_r1_s0_contract.py) 的 `FUTURE_AUTH_COMMENT_ID=None`，没有 Odoo/PG/网络入口；`mail.record/insert` 只作为**模拟候选**。13 项正负 `unittest`、`py_compile`、AST 无 Odoo/PG/文件执行入口检查均 exit0，全部 **SIMULATED**。测试覆盖真实脱敏类型的 NOT_CAPTURED、来源不明、目标/数量越界、跨公司/组改变、四项各自增量、内部消息两类来源、回滚后异常保留、SVG/GC 精确 SHA 和未知文件 STOP。模拟允许不等于本次真实意图被批准。

## 决策和保全

已证的是一个被脱敏的 `res.users` 合成目标 precommit 意图、确切的头像模板字节和 GC checklist 形式。意图真实类型、实际生成调用栈、频道/成员范围仍 UNKNOWN/NOT_CAPTURED。建议先补被动取证设计并等待新的 GPT 授权；不得直接再建一库跑产品场景。S07 候选 **NOT_ACCEPTED**，S05×S07 产品兼容 **UNRESOLVED**，集团全局权限政策 **POLICY_PENDING**，Native SIGSEGV 根因 **UNKNOWN**，S10 技术和生产持续 **BLOCKED**。

私有源：`.local/s10-d18p1r1-20261014-6166455763/`、`.local/ydental_s10_test_20261014105200_6bc8a41f/`；本批新私有审计索引：`.local/s10-d18-p1-r1-s0-20261014-6166877292/file-proof.json`，SHA256 `ef72c0e5368cd11856767cf93fea5247f71a157e957ce92dd1c6502546eceac2`。历史数据库、附件、filestore、日志和 core 原样保全。本轮没有新的 Odoo、Firefox、CREATE、业务写、Project 修改、S11 或部署。
