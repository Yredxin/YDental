# S10 D1.8-P1：S05×S07 产品兼容候选在唯一单库测试中阻断

## 授权与固定版本

唯一授权为 [#34 GPT-AUTHORIZE 6165734052](https://github.com/Yredxin/YDental/issues/34#issuecomment-6165734052)。从原分支 `4ceb3efddb15e4bdd300c79d155e04b9cbeabd0c` 前进，旧 S10 product 审核基线 `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、固定 test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` 均不改。当前 S07 **产品候选**是另一个版本，文件 SHA256 `633da04a93a4ba4f9d28dd748838833558b7f3b45c22d3ac5090d9baaddc8807`，基线到候选 diff SHA256 `4025dc904491fa44c59a8f82e1fdf5f688d9039e91fb8ba253218c4c416d731b`；因真实测试未完整通过，本候选明确标为 **NOT_ACCEPTED**，不能称产品技术 PASS。只修改 `ydental_inventory/models/ydental_inventory_service.py`，并新增一个离线静态测试脚本；S05 guard、原生 Odoo、manifest/ACL/schema、固定 S10 runner 均未改。

已用 GitHub API 明确 GET 完整读取 #23/#29/#31/#34 正文与全部有效评论，#35 OPEN/0 启用评论。起始 origin、分支、远端 HEAD、干净工作树、venv Python 3.12.15、core SHA 和 PG `127.0.0.1:5432`/cluster `7694897083368259627` 匹配。事故 OID2056451、纯92模板2100080、L1 2100086、旧三座失败库2100087/2100096/2100105均只读身份匹配且保留。[强制预检检查点 6166015900](https://github.com/Yredxin/YDental/issues/34#issuecomment-6166015900)在唯一 CREATE 与 Odoo 启动前发布并 API 逐字读回。

## 候选机制及权限界限

原已证实链为 S07 `_setup`→`stock.warehouse.create`→`_check_multiwarehouse_group`→`res.config.settings.execute`→product `set_values`→全量 `product.pricelist.action_archive`→S05 `_ydental_guard` 拒绝。Odoo 原生在每公司最大活跃仓库数超过 1、内部用户尚未隐含 multi-warehouse 且 multi-location 未启用时，会执行全量设置。product pricelist group 为 false 时该设置可归档全库普通与受管价；S05 guard 正确拒绝受管价写入。

候选仅在需要原生全局仓库组转换时要求**原执行者、非 sudo 环境**具备 Settings 权限；必要时用 Odoo 支持的 `res.groups._apply_group` 预先启用 multi-location，再交由原生 warehouse 创建来同步 multi-warehouse，绕开不相关的 `res.config.settings.execute`。原始本店 `warehouse:write`、当前门店和公司权限、幂等键、savepoint、S07 审计仍在；全局组变化标志放入操作审计结果。multi-warehouse 已开而 multi-location 关的不一致状态先拒绝。普通门店库存账号不能借原有 sudo 触发全局设置。该候选没有通过真实完整验证，不能断言其它原生、副作用或权限路径已安全。

## 预检、唯一库与真实执行

纯92模板 OID2100080 再审：92 installed 同版本、患者/治疗/费用/结算/原生账务/stock.move 等交易表0、70系统附件、124个安装 filestore 文件逐 SHA 匹配、模板外部连接0，旧 config/marker SHA 匹配。`py_compile` exit0；执行从真实 `_setup` AST 提取的 9 项 FakeEnv/Mock 正负试验 exit0，私有 clone/GDB/单目标 7 项 Mock exit0，均 **SIMULATED**。私有 Mock 首次以普通 `Mock` 假游标测试上下文管理器而 exit1，仅修测试后 exit0；此失败保留。私有 GDB17.1 依赖隔离验证，目标 `LD_LIBRARY_PATH` 已配置 unset；未触发真实 signal11。预检评论中列有候选 diff、四场景、负向、精确命令和 STOP。

唯一新库 `ydental_s10_test_20261014100600_d18a9c4e`，OID **2100114**，原 cluster，端口18260，独立 config SHA256 `e5aa67ce2a5351d1ea76c897915f5cea4d191dc41faceeb73c36f6d4d313eac4`，marker SHA256 `469f66a01681194c277e2566dd793df28e3ac17f7a5ca8aa723ba5d0a5b44abd`。管理库 autocommit+IDLE、`psycopg2.sql.Identifier` 的唯一 `CREATE DATABASE … WITH TEMPLATE OID2100080` exit0；新库独立只读 guard/92模块/124文件检查 exit0。新目录700、文件600、严格 dbfilter、loopback、SMTP 127.0.0.1:1、cron0；无真实患者与资金数据。

**唯一 Odoo 目标**由 GDB PID2658423 启动，Odoo PID2658430，Registry 92模块加载完成，随后进入第一个 A 场景。GDB exit1、目标 exit1、signal11=false，原日志 SHA256 `42c6b5169c227adbd81e5b39909c43551545f4556887a8c8ef32528521b0d37d`。实际 traceback 指向私有测试夹具 `p1_fixture.py:316`：`AssertionError: Outbound or native finance side effect`。该断言合并了 `mail.mail`、`bus.bus`、`account.payment`、`account.partial.reconcile` 四项，夹具没有在异常前保存各自的**事务内**数值；因此具体哪项发生变化 **UNKNOWN**，不能把它归为产品失败或安全 PASS。A 的价源/quote/幂等/受管价直接写拒绝断言从源码顺序看已越过，但该场景结果未写成机器记录，不能作为独立完成的 A PASS。B 同法人双店和跨公司、C 普通/受管价共存、D group组合及其余负向均 **NOT_RUN/BLOCKED**。纯模板没有非零 confirmed fee；本授权禁止治疗，所以不能冒称真实已确认费用不变的动态检验。

失败即停止：没有修改夹具或产品后重跑，没有第二个 Odoo 目标、第二次 CREATE、Firefox、安装升级、Native L2、财务或库存收发。两个自有 PID 已退出，未触碰常驻服务。源代码显示原生 `bus.bus._sendone`把通知放入 precommit，postcommit 才发 NOTIFY；本次未 commit，但事务内是哪项触发断言仍无证据，保留 UNKNOWN。

## 独立只读回滚和文件取证

事后独立 PG 只读对照：新库与模板的 20 类受控表计数**完全相同**，包括 `mail.message` 851、`mail.mail` 0、`bus.bus` 6、`res.company`、S05价/快照、S07仓库/config、stock.move、account.move/payment/partial、患者/费/结算；installed 92。所有固定旧 OID 保持，模板124个文件逐SHA不变。测试事务未提交，未留下半仓库/半价目/财务记录。

新库 filestore 保留 124 基线 + 2 新文件。首次只读分类脚本错误地采用了锁定 Odoo20 的另一个 SVG 生成函数 `generate_text_avatar_svg`，把 305 字节 SVG 标为 UNKNOWN 并按 STOP 退出（post-audit exit1，原始结果 SHA256 `93d4fcc87d5334d93bb86f5d4539b4016dd7754249d6b0fa5b877a7205526fee`）。停止 Odoo 后再只读取证，对照真正由 `res.users.create` 调用的 `avatar.mixin._avatar_generate_svg`（`../odoo/addons/base/models/avatar_mixin.py:79-88`）：新 SVG 与合成账号首字母 P、允许色、完整 Odoo20 字节逐字匹配，SHA1 扇出路径一致；另一文件为对应零字节原生 GC checklist。两个文件在回滚后均无 `ir.attachment` 引用；这能解释来源，但不删除文件，也不把所有未来孤立文件一律认定安全。私有复核索引 SHA256 `3f5a380f13d1fa4b70ef1886a295a29eb2f5436dc608987093711bf749fb0f49`。原日志、配置、原始私有汇总只保存在 `.local/s10-d18p1-20261014-6165734052/` 和新库权限700/600目录，GitHub仅放脱敏摘要及哈希。

## 结果、缺口与停止

本批 CREATE **1/1**，Odoo shell **1/1**，Firefox0，额外 Native actor0，模块安装/升级0，真实患者/资金/临床/收退款0；Project mutation0，#34保持 OPEN，#35/S11 未启用，未合并/强推/部署。历史库、filestore、volume、日志、core 和备份保留。

**S05×S07候选产品 NOT_ACCEPTED；S10技术与生产持续BLOCKED；原 PID2383730 Native SIGSEGV 根因 UNKNOWN。** 下轮若有授权，先分解夹具四项断言并在异常前保存事务内计数，独立审视 bus/邮件是否仅由合法原生设置产生；再决定是否允许新的单库测试。当前绝不追加进程或扩大业务场景。
