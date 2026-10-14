# S10 D1.8-P1-W1 单用户 Bus 见证报告

## 身份、授权与额度

唯一授权为 [#34 评论 6167210882](https://github.com/Yredxin/YDental/issues/34#issuecomment-6167210882)，上轮交付为 [评论 6167098306](https://github.com/Yredxin/YDental/issues/34#issuecomment-6167098306)。起点/当时远端 HEAD `90b385d55c7de599a4700f07b7a61082822dab04`；Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；S07 未验收候选文件 SHA256 `633da04a93a4ba4f9d28dd748838833558b7f3b45c22d3ac5090d9baaddc8807`，本批保持字节不变。

GitHub API GET 完整读取 #23/#29/#31/#34 当前正文及 3/7/8/72 条全部有效评论，最新授权评论逐字复核；#35 OPEN/0 评论。PG `127.0.0.1:5432`、cluster `7694897083368259627`；旧事故/模板/L1/各失败库 OID2056451/2100080/2100086/2100087/2100096/2100105/2100114/2100123 均只读匹配。唯一模板 OID2100080：92 installed、所查业务表空、70 系统附件、124 文件逐 SHA 一致、mail.message851、bus.bus6、外部连接0。

在任何 CREATE/Odoo 前发布[强制检查点 6167531256](https://github.com/Yredxin/YDental/issues/34#issuecomment-6167531256)，随后 GitHub GET 逐字读回一致。离线 `py_compile` exit0，私有 FakeEnv/Mock 13 项 exit0，AST 单 CREATE/单 Popen/单 `new_test_user`/显式 rollback/无 commit exit0；仅 **SIMULATED**。本批预算与实耗：CREATE **1/1**、Odoo shell **1/1**、GDB 父进程1、Firefox0、模块安装/升级0、业务事务 commit **0**、额外重试0。

唯一新合成库 `ydental_s10_test_20261014114000_8ec49d73`，OID **2100124**，端口18262。一次 `CREATE DATABASE WITH TEMPLATE` exit0，独立只读 `check` exit0。config SHA256 `e38157a0af2ab04c15dd4e96faf8f5616e38dbcd662b8cfea09830b31475a991`；marker SHA256 `7175fcc6df365a4f3300aedddd50cb46ca9f0deccacabcdf7ab05892c3a4a0fb`。独立 data_dir/filestore、严格 dbfilter、loopback、禁 SMTP 和 cron0、一次性 attempt ledger 生效。

## 唯一 Odoo 目标的真实见证

GDB 父 PID **2711500**，Odoo OS PID **2711506**，PG backend PID **507647**；GDB/目标均 exit0，无真实 signal11，原始 GDB 日志 SHA256 `ce9183f37bd3bbd6774bed2b374a37e51170b37e604653126c8ecf4c47b7ddab`。仅在自有 cursor 中创建一个合成门店，再以原 P1 的组/公司/抑制通知 context 创建一名合成 Settings 内部用户。没有会话、仓库、价格、患者、治疗、库存收发或资金动作。所有阶段快照在判断前写入权限600文件并 flush/fsync/读回；`finally` 中显式 rollback。

| 阶段 | 门店 | 用户 | partner | mail.message | mail.mail | bus.bus 行 | Bus precommit 意图 | account.payment / partial | ir.attachment |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BASELINE | 0 | 4 | 5 | 851 | 0 | 6 | 0 | 0 / 0 | 70 |
| AFTER_STORE | 1 | 4 | 5 | 851 | 0 | 6 | 0 | 0 / 0 | 70 |
| AFTER_SETTINGS_USER，断言前已 fsync | 1 | 5 | 6 | 853 | 0 | 6 | 1 | 0 / 0 | 71 |
| ROLLBACK_AFTER | 0 | 4 | 5 | 851 | 0 | 6 | 0 | 0 / 0 | 70 |

**OBSERVED_RUNTIME**：唯一意图的安全原始 `notification_type` 为 **`mail.record/insert`**，目标模型类别 `res.users`，目标角色是本批合成 Settings 用户；不是用户 ID 或 payload。进程内 `sys.setprofile` 只观察 `_sendone` 入口，没有替换该方法；仅一次 `_sendone` 调用与仅一次 precommit 意图相对应。捕获到的非敏感调用位置链：

`odoo/tests/common.py:new_test_user:312 → addons/mail/models/discuss/res_users.py:create:16 → addons/mail/models/discuss/discuss_channel.py:_subscribe_users_automatically:841 → addons/mail/models/discuss/discuss_channel_member.py:_get_member_store_list:435 → addons/mail/tools/discuss.py:Store.__init__:238 → addons/bus/models/bus_listener_mixin.py:_bus_send:22 → addons/bus/models/bus.py:_sendone:91`。

这是 **本次合成用户创建** 的 Bus 类型和来源证据；不倒推上轮 R1 的 `type=other` 原始类型，也不证明其它用户/集团场景相同。意图只是 precommit 缓冲，bus.bus 行在事务内仍6，显式回滚后仍6；没有已提交 Bus 行、已证 postcommit NOTIFY 或 SMTP 邮件。两条新增 `mail.message` 在事务中出现并回滚；本批未读取或导出消息内容/收件人，不能把它称作 mail.mail 外发。集团 `base.group_user` 的 multi-warehouse/multi-location/pricelist 布尔状态整个窗口均为 false；独立审计的源/目标 implied_ids SHA 同为 `982aab7716015636e1a458975ffaae4126c4c07912cf13cc99cb35ab802b3351`。

## 文件与独立事后保全

唯一新 filestore 增量为 305B SVG（SHA256 `0bef0d6cd8eb624768807b7f89619558733fef976a553f41c2b020ef046ec01d`）和 0B GC checklist（SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）。私有只读字节比较证明 SVG 与锁定 `avatar_mixin._avatar_generate_svg` 对本批合成用户名首字母的模板逐字节一致；内容 SHA1 对应文件路径，checklist 路径精确对应该 SVG。`res.users.create` 的头像写入与 `ir.attachment._file_write/_mark_for_gc` 是源码链；具体哪次内部调用写入仍只标 **LIKELY**，未有头像调用级栈。

Odoo 退出后，独立只读 PG 确认新库所有所查计数与模板相同：92 installed、mail.message851、bus.bus6、mail.mail0、account.move/payment/partial0、门店/价格/S07配置/stock.move0，原生 group implied_ids 相同；新库活动连接0，旧 OID 全部不变。源124文件及其克隆逐 SHA 保持一致；上述两个回滚后未引用文件的 `ir.attachment` 引用数0，**原样保留**，不清理。无真实患者和支付资料，未见未经授权外发。

## 证据分级和下一步

- **PROVEN/OBSERVED_RUNTIME**：W1 合成用户创建路径产生 `mail.record/insert` 向本批 `res.users` 目标的唯一 precommit 意图；一条非敏感 `_sendone` 调用链；四项独立计数、消息/附件事务内增量及显式回滚；新库/模板及文件字节核验。
- **LIKELY**：该用户创建路径中的原生头像字段写入留下 SVG/GC 文件。字节机制已证，具体写入栈未捕获。
- **UNKNOWN**：上轮 R1 被抹掉的真实事件类型、其它用户/频道/跨公司下的通知范围、真实集团仓库设置的全局副作用、原 Native SIGSEGV 根因。W1 的正常退出不等于 Native 修复。

本次见证可作为未来**另行授权**的产品实验设计输入：只能在相同创建阶段、真实类型/目标/来源/数量和独立资金/邮件/组/文件证据均匹配时考虑限定分类；未知事件及后续仓库 `stock_group_sync` 必须单独 STOP。没有执行 S05×S07 仓库价源场景，当前 S07 候选 **NOT_ACCEPTED**，兼容性 **UNRESOLVED**，集团全局权限政策 **POLICY_PENDING**，S10 技术与生产 **BLOCKED**。

私有原始目录 `.local/s10-d18-p1-w1-20261014-6167210882/` 与 `.local/ydental_s10_test_20261014114000_8ec49d73/`（700/600）。脱敏[机器索引](evidence/s10-d18-p1-w1/diagnostic.json)列出脚本、阶段快照、原始日志及事后审计 SHA。历史数据库、filestore、卷、日志、core 和备份保全；Project 零修改、#34 不关闭、S11 未启用，无合并、强推或生产部署。
