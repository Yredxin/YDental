# [CODEX] S10-P0-23 异常证据纯文件核查预检

唯一授权6230563750（FILE_ONLY），P022裁定6230526897；本批不授权数据库或业务续跑。父HEAD `42107b731775e239ef516e718f46347382147171`；原分支codex/s10-settlement-finance-r1-20261013、origin=https://github.com/Yredxin/YDental.git、唯一目录/home/redxin/code/odoo/odoo-sd/code/sd-addons、core只读f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb匹配。初始工作树干净。#23/#34当前正文与全部3/264有效评论已API完整保存；旧260评论与P022初始存档逐字相同，P022预检/交付两正文与旧私有文件逐字相同，其后仅正式P022裁定/本授权。#35 OPEN/0。本批没有已有CODEX预检/交付或并行记录，无冲突。

新增核验器执行提交 **`68530112b26b7314a155f3808c1246e950e5fdd0`**（已线性推送）：[scripts/s10_p0_23_verify.py](https://github.com/Yredxin/YDental/blob/68530112b26b7314a155f3808c1246e950e5fdd0/scripts/s10_p0_23_verify.py)，SHA256 **`5c89930fff75dc972f83b355c4c4befb5855d4d9f92ff7fa8e24a63c6a5dfbce`**。此前654380305520a5b06181b6e244a446080af41b12是同一预检准备过程的初稿提交，保留历史；正式冻结使用本条上述HEAD及SHA，不执行初稿。只做过内存compile准备，尚未运行核验器。

[完整输入清单](https://github.com/Yredxin/YDental/blob/68530112b26b7314a155f3808c1246e950e5fdd0/docs/evidence/s10-p0-23/inputs.json)SHA256 **`42f6033edb2a547db7980b0e47560266ec39fe56cbdabda93ce49c9d6122a3e4`**：47项、708669083字节，列明确切路径、旧manifest SHA/bytes及公开Git blob。原P02260项索引自身SHA为04ababfaf68a0e168fa6cb04a815ec3f4c0566041727cbe8562364fe9563bcca，锚定父Git对象；私有manifest也锚定父Git/原索引，不重新生成。只核有限关键输入，不重算645表或访问任何库。

输入分组（前缀`.local/s10-p0-22/`）：

- scope前动作的`r0-A-fresh-owner-scope-1-intent-before.json`、`-before.json`、`-after.json`和`-full-diff.json`；用于核此前保存副本与目标字段是否存在，不执行旧fixture。
- `A-owner-scope-precommit.json`、`A-owner-scope-committed-RO.json`、`A-owner-scope-readback-before.json`、`-after.json`、`-full-diff.json`及`A-owner-scope-native-effects.json`。
- `final-tail-RO.json`、`final-tail-vs-scope-precommit-before.json`、`-after.json`、`-full-diff.json`及`failed-readback-vs-final-tail-before.json`、`-after.json`、`-full-diff.json`。
- 对应公开P022两份RO签名、四组diff-index/decision、integrity-stop、events、result、freeze、summary及静态结果；原native日志仅只读输入，不公开日志全文。
- 已保存STATIC frozen-candidate before/after/full-diff，仅解析，不导入/运行旧主程序。
- 固定P022 contract/runtime/control/cases/native/preflight/seal_blocked七份源码，只AST读取；仅可抽取canonical/sha/economic/diff/save/persist/exact七个纯函数，在本批私有输出目录对独立合成字典做文件反例。严禁调用capture/readonly或旧native/fixture main。
- 固定core `addons/account/views/account_portal_templates.xml`，只读Git对象，核已存在模板的字面/结构来源；不渲染/加载Odoo。

预定核验：所有整文件原字节先匹配冻结输入及旧manifest，再独立拒绝重复JSON键解析。唯一目标public.ir_ui_view/id929/key=account.portal_my_journal_mail_notifications，保留真实JSON pointer、physical OID。计算每个值类型、字符/UTF-8长度、完整SHA/hex、原JSON字符串token SHA/位置，独立定位原字节中的token并核解码；分列字符与字节偏移，核precommit↔异常RO↔tail和同一次保存副本的字段/整目标行全等。只重算已保存ir_ui_view表签名，不当作数据库测量；多个保存副本绝不当作多次独立测量。

字段公开门禁：仅在三份arch_prev除精确异常字符外与固定core模板的全部子结构、字面和属性相同、外层确认为loader的template→t转换且无实际患者/会话/口令/token时，才输出三份完整`.txt`及可复算JSON/UTF-8 hex。literal email变量和request.csrf_token()表达式不是实际值。全文、hex和附近片段均须先过该门禁；失败则只保留脱敏输入/失败说明，不上传整库、完整行或秘密。

检查capture→json.loads→对象比较→save/fsync→seal的实际源码顺序、静态fixture可变引用、替换/脱敏及独占写覆盖边界。预定11项纯文件正反例含相等/精确v→6、断言前保存/输入不变、后续相等不覆盖旧FAIL、独占x拒覆盖、重复物理键/顺序、中文字符与字节偏移、重复JSON成员拒绝、schema浅引用与行深拷贝，以及不同采集层机制生成同一保存对象的合成不可区分示例。示例不是P022原始返回的补造或根因证明。

拟输出仅docs/evidence/s10-p0-23中的输入原字节核验、字段观察/全文JSON/三txt、比较、公开门禁、静态fixture检查、纯文件反例、AST行号映射、结果和输出SHA清单，以及docs/s10-p0-23-*.md报告/保存链映射。原P022产品、脚本、索引、私有manifest和FAIL/tail一律不改。新私有文件仅.local/s10-p0-23（0700），用于GitHub流程证据和合成纯文件反例。

预算及实际要求：所有旧/新数据库连接、SELECT/CREATE/DML、Odoo加载、业务HTTP/RPC、浏览器、PDF、scope登录、文书、收退款、日结、安装升级、权限变更、产品/core修改、sudo/OS/PG/Docker/网络/硬件专项全部 **0**。GitHub API读取及本预检/最终回执评论是流程操作；Issue/Project状态0修改。仅新增授权P023路径，线性提交推送，不reset/clean/force-push、合并或部署。

本条REST GET正文逐字全等并保存后才执行：`PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python scripts/s10_p0_23_verify.py`。输入不符或字段无法证明则记录具体BLOCKED，不改旧证据/核验合同以放行，不重新采集。即使全部文件检查通过，结论也仅限已保存文件；若缺原始返回和服务器字段摘要，明确“离线证据止于采集后对象，数据库/驱动/内存/落盘分层无法由现存材料区分”。五组缺口和S10整体BLOCKED不变，不宣布数据库完好/根因修复或业务可恢复。正常交付和REST逐字读回后立即STOP，等待GPT独立复核，不自动续五组/P024/S11。
