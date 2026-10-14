# S10 Native D1.6-0：Registry 字段元数据与 Native 证据缺口

## 1. 授权、身份与边界

唯一授权为 [#34 GPT 评论 6162669294](https://github.com/Yredxin/YDental/issues/34#issuecomment-6162669294)，承接[已复核 D1.5-C 交付 6162562086](https://github.com/Yredxin/YDental/issues/34#issuecomment-6162562086)。开工分支 `codex/s10-settlement-finance-r1-20261013` 的本地及远端 HEAD 均为 `49501f75d9b5e3cf8fb91d2826296686c01bf3fa`，工作树干净；固定 product `4b168a84254882a2e1e3e5037c372ab57fc3dfdd`、test `255b48f54495eb99638af8ffc824771b9a5af3e7`、Odoo20 core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。`gh api --method GET` 完整取得 #23 正文及 3 条评论、#34 正文及开工时 46 条有效评论，最新为本授权；#35 OPEN、0 评论。GitHub 代理/TLS 在本批 GET 和评论 POST/GET 检查点均可用，没有修改系统代理。当前 Ubuntu venv 是 CPython 3.12.15。

PG endpoint 为 `127.0.0.1:5432`、cluster `7694897083368259627`。事故库 `ydental_s10_test_20261014020300_8b6c1d4e` / OID2056451、纯92库 `ydental_s10_test_20261014044700_4f6a8d2c` / OID2100080、L1库 `ydental_s10_test_20261014052222_5457e39f` / OID2100086 均由只读管理查询核对；旧 OID2078375、2100078、2100079 仍存在。新增事故库元数据查询前发表[强制检查点 6163037394](https://github.com/Yredxin/YDental/issues/34#issuecomment-6163037394)，API GET 逐字相等，正文 SHA256 `d71144477bf32106639d127b04463f08173f252df2e8e56974e7ff58d4c923d5`。本轮 Odoo、GDB-Odoo、Firefox 启动 **0**；CREATE、业务写入、Project mutation **0**。

## 2. 锁定 Odoo20 的可证调用链

`../odoo/cli/shell.py:130-148` 先构造 `Registry(dbname)`，再建 cursor；以 `uid=1` 和空 `{}` context 调用 `api.Environment(... )['res.users'].context_get()`，成功后才创建交互 `env` 并进入读取 stdin 的 console。`../odoo/orm/environments.py:64-89,227-250` 中 uid1 环境为 superuser 模式，公司由用户默认公司路径取得。

`../odoo/addons/base/models/res_users.py:791-820` 的缓存 `context_get` 首先在第797行调用 `self.env.user.read(['lang','tz'], load=False)[0]`。`lang/tz` 在该文件第248-249行是 `partner_id` 关联字段；`share` 在第223行是 `compute_sudo=True, store=True` 的计算字段。第805-814行在用户语言不属于已安装语言时才选择请求语言、默认公司 partner 语言及最终回退。事故栈停在第797行的 `read` 内，**不能说后续回退已经执行**。

`../odoo/orm/models.py:2818` 的 `read` 调用 `fetch`；第3148-3152行对未存储且缓存缺失的字段调用 `mapped`，第5627-5638行进入字段 `__get__`。`../odoo/orm/fields.py:1912-1920` 由 `__get__` 调用 `compute_value`；第2073-2091行先按 `compute_sudo` 调整权限，随后在第2078行取 `records.pool.field_computed[self]`，其后才在第2091行调用 `_compute_field_value`；`models.py:4452-4458` 中该后者才 `determine(field.compute,self)`。因此日志证明触及**计算字段元数据获取**，尚不能证明某个具体业务 compute 方法执行。

`../odoo/orm/registry.py:600-638` 的 `@functools.cached_property field_computed` 首次求值遍历每个 registry 模型的 `Model._fields.values()`，以 `field.compute` 分组；同组字段再比较 `compute_sudo`、`precompute`、`store`。`../odoo/orm/fields.py:482-490,642-674` 表明 related 字段也可设置运行时 `compute`（`_compute_related`），普通计算字段的 `compute_sudo` 默认受 `store` 影响。`field_computed` 出现在事故 Python 栈，**不能定位到某个字段或模型，更不能确定 C 内存损坏的起点**。运行时 Field 对象及 cached_property 状态无法由本轮静态阅读重建。

原 PID2383730 的日志在 UTC 02:08:26.114 记录 registry loaded，随后 `Fatal Python error: Segmentation fault`。faulthandler 可见链是 `shell.py:139 → res_users.py:797 → models.py:2818/3152/5638 → fields.py:1920/2078 → registry.py:608`；这是 Python 可见栈，**不是 Native C backtrace**。未见 actor stdin 执行业务操作的证据；另一 PID2383729 的 SIGINT/-2 是守卫中断，并非第二个 SIGSEGV。

## 3. 已安装 YDental 字段的静态差异审计

|模块与源码|字段或覆盖|是否可能进入元数据遍历|事故因果证据|
|---|---|---|---|
|`ydental_access/models/res_users.py:7-13`|`ydental_job_title` Char、`ydental_capability_ids` Many2many；同文件第15行以后是写入/登录钩子|普通字段属于 `res.users._fields`，未声明 compute/related|无该字段造成事故的证据；无 `context_get` 覆盖|
|`ydental_supply/models/res_users.py:5-16`|仅 `write` 覆盖|不新增计算字段|无 `read`/`context_get` 调用证据|
|`ydental_patient/models/res_partner.py:8-27`|存储的 `ydental_patient_owner_id` 和访问保护|普通字段属于 partner 元数据；uid1 `su=True` 时自定义 `not self.env.su` 条件不满足|不能推断全部动态副作用不存在|
|`ydental_access/models/hr_employee.py:5-13`|两个 `user_id` related 字段，均 `related_sudo=False`|related 在运行时可有 compute 对象|字段定义可能被遍历；没有读取员工行的证据|
|`ydental_supply/models/ydental_supply_assignment.py:18-24`|`ydental_warning`，`@api.depends` 用户/员工 active 与能力等|是计算字段定义|没有其 compute 方法执行证据|
|`ydental_space/models/ydental_space_area.py:28-48`、`ydental_space_station.py:16-36`、`ydental_space_resource.py:24-32`|队列区域/能力/上传字段的 compute 或 related、`@api.depends`|可能进入同一 registry 元数据遍历|没有其对象或记录触发崩溃的证据|

静态搜索当前 `ydental_*` Python 源的 `compute=`/`related=`/`@api.depends` 与 `context_get` 覆盖，并查阅模型继承；未发现已安装 YDental 模块覆写 `res.users.context_get` 或扩展 `res.company` 字段。此结论只覆盖当前锁定源码和实际安装模块，不代表所有 Odoo 原生计算字段，也不证明事故进程内 Python 对象图等于当前源码状态。测试目录中的 Python 文件存在不等于其 addon 已安装。

## 4. 三库只读 SQL 元数据对照

检查点读回后，私有 `schema_probe.py` 先用 `information_schema.columns` 核对允许表的真实 schema；`metadata_compare.py` 再用独立 psycopg2 连接，**任何查询前**开启只读事务并断言 `transaction_read_only=on`、`statement_timeout=5s`、dbname/OID/cluster。仅访问 `ir_model`、`ir_model_fields`、`ir_module_module`、`res_lang`，以及 uid1 相关的 `res_users`/`res_partner`/`res_company` 四项上下文输入。无业务表、患者/员工/session/会计行明细读取。私有结果含只读元数据，GitHub只给聚合、布尔及 SHA。

|指标|事故 OID2056451|纯92 OID2100080|L1 OID2100086|
|---|---:|---:|---:|
|`ir_model` 模型|591|591|591|
|`ir_model_fields` 字段|11380|11380|11380|
|`store=true` / `related` 非空|7518 / 1426|7518 / 1426|7518 / 1426|
|SQL `compute` / `depends` 非空|0 / 0|0 / 0|0 / 0|
|installed 模块 / `res_lang` 全部 / active|92 / 93 / 2|92 / 93 / 2|92 / 93 / 2|

三库完整模型元数据哈希 `ce6f4a99ac1ca955e857f6278ca64b9e5acf73faa0a64f4650fd0ab3b2a10ba0`，字段元数据哈希 `2f890c551f5608a41d23bdb50b88711a6b2ffd28f8c51c270e007e81fcb64944`，installed 模块及版本/状态哈希 `69ffec40e70c0c86c98dc9da1be2ecbdde543250a5e929f9d380f81b3a0082b8`，语言行哈希 `b3c2bc9a2e3bc4a4afdba3c637a1d1e67407b6d78640e6dc8d00b17b9e419045`，均三库一致。三组两两对照的模型/字段/模块新增、缺失、属性变更均为 **0**。`res.users` 292 字段、169 related；`res.partner` 192/13；`res.company` 213/16；`hr.employee` 208/81，三库各自相同。

uid1 默认公司数字 ID、用户关联语言/时区、默认公司关联语言的三库**相等性布尔值**均为 true；用户及默认公司关联语言存在且已安装，关联时区为空。这里不公开 ID 或语言值。即使 `read` 成功，该静态持久状态也不需要语言回退；事故发生在 `read` 内，不能据此说该进程已到回退分支。

真实 schema 的 `ir_model_fields` **没有 `compute_sudo` 或 `modules` 列**，故 SQL 计算权限和字段归属模块统计标记 `NOT_AVAILABLE`；没有扩查 `ir_model_data`。SQL `compute` 全空与源码中的计算字段并不矛盾：此数据库列没有完整承载 Python 运行时 `Field.compute`/related 的对象图。元数据相同也不能推出进程内 Field 对象、缓存、GC、地址空间或 Native 堆相同；L1 与事故库的业务记录状态本就不同。

## 5. Native 文件、符号与真实事故证据

事故配置 SHA `34f2a7cff12ef31c69090fb7b1f990b008bebf850290e2747d868c6a9d8ae778`、原始 `race-bill-b.log` SHA `f7795b360a80afc8fdfff8cd9c7e389da25064c36480bdb98bceccd9a2c0eef6`、crash marker SHA `d1785e5f111f0c2358fce04895092b81f1c4455f3e0774f82b1646a447e48d78` 重新核对匹配。原日志枚举17个已导入扩展，但不是事故时完整共享库映射。

私有 GDB17.1 可用，binary SHA `e5272927fc1b40345748dfa4133ec2a50caeb5f209a44099dd2c48679911c59c`；**单独执行 `--version`** 时必须给 GDB 私有库路径，不向任何 Odoo 目标注入该路径。本轮未运行 GDB 目标。现有 glibc ELF Build ID `066527e430a32768d82741e00b81eebb1a872294` 与私有 `.build-id/06/6527e430a32768d82741e00b81eebb1a872294.debug` 对应。CPython3.12.15 可执行文件 Build ID `7713d416ece8f53a2b37e61dd06defd7bf795954`、SHA `0886fb76ceec8ff568d23079b5da6342bb41675e216e11525d4d6a9e65988d10`；有 `.symtab`，无 `.debug_info`。D0 留存47个 native `.so` 的路径/SHA/Build ID清单，本轮逐文件核对47/47 SHA匹配，原清单无缺依赖；`readelf -S` 显示37个有 `.debug_info`、10个没有，例如 psycopg2 有而 lxml.etree 无。当前文件一致性**不能证明原事故瞬间加载的对象、映射或内存相同**。

事故现场没有可用原 PID2383730 core、`/proc/<pid>/maps` 快照或真正 Native C线程栈；当前 `core_pattern` 是 Apport 管道，事故后文件搜索未见 core。历史 S07、S08-C、S09、S10 均曾报告 native 崩溃和 Python 栈/日志缺口，但无同一根因所需的共同 C 栈证据，不能合并归因。GDB 工具和部分符号**具备未来捕获能力**，不是旧事故 C 栈的替代品。

## 6. KNOWN、UNKNOWN 与下一次可证伪决策

**KNOWN：** 崩溃目标在 shell 默认 uid1 context 初始化、actor stdin 前触及 `field_computed`；三库本次查询的 schema/注册元数据和 uid1 上下文输入相同；原事故是真 SIGSEGV/-11，另一目标是守卫 SIGINT/-2；当前 GDB、glibc 符号和部分扩展符号可用。

**UNKNOWN：** 崩溃 C 指令/调用栈、线程、共享库实时映射、损坏发生点，具体 Field/model 是否相关，事故瞬间资源与堆状态，Python/native 低频并发条件。最后一个 Python 帧不能代替 Native 归因。

- **方案 A（仅若未来找到可解释元数据差异）：** 在独立新纯合成库只控制该字段所属模块或合法定义差异；先静态核对来源、guard、业务副作用，再申请明确 CREATE、准备及双 GDB 目标预算。以同一固定配置下“该差异存在/不存在时真实 signal11 与 C 栈定位”证伪。**本轮三库没有发现这种 SQL 元数据差异，当前不建议为此启动窗口。**
- **方案 B（当前建议）：** 先补充匹配 CPython `.debug_info` 的安全可行性和 C 栈采集设计；若 GPT 单独授权新的 Native 窗口，GDB 作每个目标父进程，真正 signal11 时保存 `info threads`、`thread apply all bt full`、shared libraries/Build ID、映射、OS/PG PID、registry/资源同时间轴，并在首个真实 SIGSEGV 立即 STOP。即便下一次未复现也只能写 UNKNOWN；不能无限重跑或恢复 S10 D2。

方案均**只设计、未执行**。S10 技术和生产继续 **BLOCKED**，Native 根因继续 **UNKNOWN**。

## 7. 真实命令、退出与失败边界

|动作|实际结果|
|---|---|
|`gh api --method GET` 读取 #23/#34 正文及分页全部评论、指定授权与交付、#35，检查 HTTP/正文；`git ls-remote`、本地 SHA/status|各 exit0，#35 OPEN；远端固定 SHA 未漂移|
|`gh api --method POST .../issues/34/comments --input checkpoint-request.json`，随后明确 GET 评论 6163037394 并逐字对比|各 exit0；在三库新增元数据 SQL 之前|
|独立只读 PG 管理目录核对 cluster/六个固定 OID|exit0；无 DDL|
|`../.venv/bin/python -m py_compile` 私有 schema/metadata 脚本；两次脚本各执行一次|各 exit0；只读、5s timeout、固定 OID/cluster|
|`git show`、`rg`、`sed`、`readelf`、`sha256sum`、`ldd` 与私有 GDB 单独 `--version`|源码/ELF只读命令 exit0；GDB 缺少私有 `libbabeltrace.so.1` 时单独 `--version` 实际 exit127，随后指定**仅 GDB 进程**的 `LD_LIBRARY_PATH` exit0；从未启动 GDB/Odoo 目标|
|原 D0 native 清单47扩展逐SHA核验、`readelf -S` 调试节统计|exit0；47/47匹配，37有/10缺 `.debug_info`|
|检查点再次 `gh api --method GET`|API exit0；`--jq .body` 输出多一个换行导致原始文件 `cmp` exit1；改用原始 JSON 的 `body` 字段按字符对照 exit0、完全相等，未重新发表检查点|

第一次不带私有库的 GDB `--version` 失败及一次文本 `cmp` 格式差异均如实保留；它们不涉及 Odoo、数据库或旧事故。上述 SQL 的范围由检查点限定；检查脚本只在私有目录，静态结果没有冒称真实 Native 实验。

## 8. 证据保全与交付界限

原始授权/检查点 API 响应、SQL schema、元数据结果、私有查询脚本及完整差异工作材料保留在权限700目录 `.local/s10-native-20261014-6162669294-d160/`，私有文件600。`schema.json` SHA `2e1386d2acbd0a24ce3d8bbec86633bc0143a11375d7b0f2f9e06497278bb6db`，`metadata.json` SHA `5490fb82a625456441f9996dd8047293d75362dd030c1843146a4fbc8a5e395f`；公开仅[脱敏机器索引](evidence/s10-native-d16-registry-fields/diagnostic.json)，不上传配置、凭据、用户值、患者或支付资料。原事故日志、marker、旧 GDB证据、所有历史数据库/filestore/volume/core/备份不删除、不覆盖；产品、固定 runner、Odoo20 core、odoo-12、venv及依赖未改。#34/#35保持 OPEN，Project 零 mutation；不启 S11、不合并/强推、不部署生产。最终评论和远端 SHA 将在推送后逐字核对，随后立即停止。
