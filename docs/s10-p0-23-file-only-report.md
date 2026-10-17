# YD-N1 R1 S10-P0-23：P022既存异常证据的纯文件核查

本批有限文件核查已完成。三份 `arch_prev` 的全文、UTF-8十六进制、长度、SHA256及保存副本均可独立复算，确认保存证据记录了 `v→6→v`。另确定一份既存scope-after文件含原始 `0x1F`，不是严格有效的JSON；该文件原字节与P022旧manifest相同。**异常来源仍UNKNOWN，S10_TECHNICAL_EXIT_BLOCKED及五组缺口不变。文件核对不是数据库完好、根因修复或业务可恢复的证据。**

唯一授权为 [6230563750 / FILE_ONLY](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230563750)，P022正式裁定 [6230526897](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230526897)保持，不重判/重跑P021财务原件、P020 A或历史窗口。父HEAD `42107b731775e239ef516e718f46347382147171`；原分支 `codex/s10-settlement-finance-r1-20261013`、origin `https://github.com/Yredxin/YDental.git`、工作目录 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`匹配。core只读固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。

实时#23/#34当前正文及全部3/264有效评论已API完整保存。#23正文/3评论、#34正文/旧260评论与既存存档相同；其后P022预检/交付与原正文文件逐字相同，仅再新增P022裁定及本授权。#35 OPEN/0。起始本地/远端HEAD匹配、工作树干净，无本批已有CODEX预检/交付、并行或归属冲突。只新增许可P023路径，旧产品、模板、脚本、报告、FAIL、尾审及manifest全部只读。

|预检与实际执行|固定事实|
|---|---|
|唯一初始预检 [6230625715](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230625715)|REST逐字全等于2026-10-17T06:21:09.194838+00:00保存；正文SHA `84b3b91b421ecca57a8cf26bb0fc294a102aaeba59e317c0cb14654399cf44f7`。|
|初始执行版本|`68530112b26b7314a155f3808c1246e950e5fdd0`；verify.py SHA `5c89930fff75dc972f83b355c4c4befb5855d4d9f92ff7fa8e24a63c6a5dfbce`。前一6543803是未执行准备稿，正常历史保留。|
|47项输入|`inputs.json` SHA `42f6033edb2a547db7980b0e47560266ec39fe56cbdabda93ce49c9d6122a3e4`，708669083字节；旧manifest和公开Git blob逐项列明。先核全文件原字节再解析。|
|初始严格核验|exit1，JSONDecodeError；原stdout/stderr/退出码保留，不用后续结果覆盖。尚未到合成反例或字段公开。|
|分层增量 [6230653895](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230653895)|REST逐字读回；951348cbf430db69f5e813d09ee34f3c178d55cf的diagnose.py SHA `e426c4c649669b8381a313c8b9734cf94172badf700ab9c3bbe87fda5c012c90`；system入口完成文件/字段输出后，合成helper命名空间漏ast，NameError/exit1。|
|更正及完成冻结 [6230673816](https://github.com/Yredxin/YDental/issues/34#issuecomment-6230673816)|REST逐字读回；7e571df0acd2daded1c1c57de8caa7f28f33487b的complete.py SHA `caa0a8f4626171955bac2d0c6704d8f6adba476e2173679c8b8ef972371d31e3`。只修本批新路径的纯文件helper依赖，旧两个执行文件/失败均不改，不重跑原路径。|
|剩余固定解释器入口|existing ../.venv/bin/python 3.12.15执行complete.py diagnostic-fixed，exit0；保留发现的一份严格JSON失败，11项纯文件反例通过。不是把所有输入有效性改判PASS。|

实际命令、stdout/stderr及SHA见 `process-results.json`。两次增量只是同批FILE_ONLY的冻结与更正，均先API逐字读回再执行；不是新增数据库授权。初始补充评论和initial-run-result把失败文件推断为intent-before，这是错误推断：循环此前两份严格解析已通过，失败在第三份after。原错误记录保留，由 `initial-run-correction.json`及6230673816明确更正。

输入仅限已存scope前后、precommit、独立RO及其persist before/after/full-diff、最终tail及两组离线比较副本、对应签名/索引/decision、旧manifest、七份冻结脚本、原static fixture及固定core模板。P022公开60项清单自身SHA `04ababfaf68a0e168fa6cb04a815ec3f4c0566041727cbe8562364fe9563bcca`，由父Git对象锚定；私有manifest由该公开清单及父Git对象锚定。没有重新生成旧索引，没有重算全部645表、其余私有manifest文件或旧filestore，也没有重新采集数据。

目标为旧文件中的 `public.ir_ui_view` / id929 / key `account.portal_my_journal_mail_notifications`，物理table OID **2122563**；schema记录列为SQL `text`，解析类型为Python `str`。physical schema来自固定capture的public SQL限定，table/OID来自保存行，不是本批数据库查询。12份snapshot目标JSON路径均为 `/tables/ir_ui_view/928/arch_prev`；full-diff目标路径为 `/0/before/0/arch_prev`和`/0/after/0/arch_prev`。每份目标数组都独立严格解析，id/key唯一；未使用strict=False、修改输入或跳过坏行重算签名。47项原字节在各次解析前后匹配旧manifest/冻结值。

|主要既存文件|原整文件SHA256|字段字符/字节|完整字段SHA256|
|---|---|---|---|
|A-owner-scope-precommit.json|`974a0bc8352c699bf1e2b3b4f493f02fcdc80b0b4d9f9be9bb224bfe4e13d07a`|2022 / 2022|`776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664`|
|A-owner-scope-committed-RO.json|`e81988d2da3ccb010c3e6fcb685b873beaf77cd33baaaa5a12de4af5df3e69b8`|2022 / 2022|`75cf739577c6a1977bdd25ddfc4df3a930255243916765abd79b248819248050`|
|final-tail-RO.json|`a5c86877e0dfcba311f1fd25758ef31190c2b5862f64da2947a223c1dd79abdd`|2022 / 2022|`776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664`|

precommit整文件58746920字节，RO/tail各58735553字节。原样文本保留末尾空行及4个空格，Git默认空白检查对两组共6份文本报exit2；仅排除这6份必须原样保存的文本后，其余文件格式检查exit0。没有strip或改变任何字段SHA，见format-check.json。三份原JSON字段token各2128字节，长度包括外层引号和转义，不能与解码后的2022字节混用。字段字符偏移1992与字段UTF-8字节偏移1992恰好相同；这不是通用规则，中文合成反例已验证二者可不同。实际 `v` U+0076 / 118 → `6` U+0036 / 54，附近为 `</div>`→`</di6>`；两者XOR为0x40。JSON token内差异位置则为零基字节2093：precommit原文件46530669，异常RO与tail原文件46519302。每个token的起点、长度、SHA、原字节匹配和反向差异详见 `diagnostic-fixed/field-observations.json`、`index-signature-token-checks.json`。

两组非空full-diff的before/after目标行已独立逐列复算，实际唯一变化列均为arch_prev；其余目标行列一致，见target-row-column-check.json。

三份完整字段原文本保存在 `diagnostic-fixed/arch_prev-precommit.txt`、`arch_prev-readback.txt`、`arch_prev-tail.txt`，不strip、不额外加换行；各文件SHA就是上表字段SHA。`field-values.json`逐值提供全文及完整UTF-8 hex，`comparisons.json`给字符与字节差异及附近片段。公开前独立核固定core `addons/account/views/account_portal_templates.xml:84–117`：loader外层template→t、XML声明与格式空白之外，precommit全部子结构/属性/字面与该原生模板相同；readback仅该一字符不同，tail完全相同。email/CSRF仅模板变量与request.csrf_token()字面表达式，没有实际患者、email、会话、口令或token。没有公开完整目标行、其他行、整库快照或配置；hex与附近片段也在公开门禁之后才保存。

12份快照及两份非空full-diff中的4个值，共16处目标值核验；4组同次采集重复保存的目标字段及整目标行全部一致。precommit、异常RO、tail各有原文件和persist复制/完整差异引用，不是多个独立数据库测量。另有scope前两保存副本、scope后单份；原生scope-after与precommit是两个不同capture，即使大部分字节相同也不将它们称同一次快照。全部成员及路径见输入清单的same_capture_groups和field-observations。公开RO/tail的ir_ui_view表签名从已保存数组独立重算匹配，四组完整差异去除before/after后的投影与旧公开index逐项相同；原FAIL/PASS标记均保留，不重评旧完整性合同或全库结论。

系统python3的7项已完成输出与固定解释器对应输出**逐字节相同**：file-diagnostics、field-observations、field-values、comparisons及三份txt。见 `cross-interpreter-comparison.json`。这只比较同一批文件的解析结果，不是两次数据库核验；system进程末尾NameError仍为exit1。

新发现的文件有效性问题：19份本次相关JSON输入中18份严格解析有效，唯独 `.local/s10-p0-22/r0-A-fresh-owner-scope-1-after.json` 含原始0x1F，字符偏移40931612、字节偏移41174581、行1321326/列25。两种解释器独立严格解析均在此拒绝。文件长度58746920字节、SHA `221683f576b84ae8903d099b7027ae48ab1d5022faa8d2ee12fc3c153a3624ec`均匹配原P022私有manifest。该坏字节位于目标view数组之外，目标数组本身严格有效，所以可以独立核目标字段，不能说整份文件有效。

将该scope-after与已存precommit按原字节比较，二者等长且全文件仅上述一字节不同：after为31/0x1F，precommit为95/0x5F（下划线），XOR也是0x40，见 `saved-file-byte-pair.json`。这是与v→6另一个位置的字节事实；**相同XOR不能定位为RAM、磁盘、PG、编码器或任何主体的问题**。没有做任何硬件、OS、PG或环境专项。最小合成反例 `{opaque: 0x1F字符串}`以JSON字节hex精确给出；严格json.loads拒绝，而正常json.dumps将chr(31)转为合法`\u001f`，回读可恢复字符。该序列化对照说明现存文件不符合正常JSON输出契约，不能证明真实异常在哪一层发生，也不能解释另一快照的v→6。没有修补或重新保存那份旧文件。

保存链的15个真实源码函数、行号及AST SHA见 `collection-save-chain.json`：

|路径|已确定的行为及边界|
|---|---|
|contract.py capture:98–117|固定public实际表SQL取得physical table/OID和to_jsonb(t)::text；直接json.loads(parse_float=Decimal)，加入physical键后返回新对象。SQL字面可见，但本次原始返回文本/字节未保留，没有同语句服务器字段SHA/hex或解析前后即时摘要。|
|runtime.py snapshot:24–36|flush→显示投影→flush→capture；display_projection另存，不能代替stored字段。|
|runtime.py observe:39–56|before保存intent→业务回调→after→persist；本批仅AST读取此旧路径，未调用任何回调。|
|runtime.py checkpoint:179–203|完整precommit先保存→commit intent/returned→独立readonly保存→persist→门禁成功后才marker。P022原FAIL发生在marker前；本批不重跑。|
|contract.py save:44–51 / persist:143–157|exclusive x，不覆盖；json.dump(ensure_ascii=False/default=str)→newline→flush→file fsync；before/after/full-diff/index先保存，再执行断言并写decision。没有directory fsync调用，不能把源码顺序当作服务端返回或端到端落盘的独立证明。|
|contract.py diff:120–140 / readonly:166–191|比较完整规范化对象，以physical table/id分组，保留重复键；完整diff中before/after引用原行而不做深复制，当前已保存副本没有目标值分叉。签名计算于已解析的表对象，非原始PG返回。|
|preflight.py main:17–143|schema等metadata存在浅引用；selected tables及after、修改反例是deepcopy，实际已保存fixture的8张表不含ir_ui_view。合成对照证明metadata别名，但未证明它能造成目标字段变化；旧fixture主程序没有执行。|
|seal_blocked.py save:24–27 / main:30–106|读已保存tail/baseline/完整性汇总，新增预算/退出表；此save只有关闭，没有显式fsync，不会改旧快照。integrity-stop是该seal的输入，不把汇总文件冒充原始返回。|

在这条收集/比较/保存路径，没有看到针对arch_prev作v/6替换、脱敏或覆写旧文件的源码操作。旧read_text/open未显式指定encoding；本批按原字节显式UTF-8严格解码，未重用旧读取函数。普通字符串不进入default=str转换；示例/时间字段的其他replace不等同目标模板替换。AST范围内未见能确定产生本次精确变化及回到原值的代码。保存顺序、缺失边界证据或一般别名风险不是根因诊断。

11项确定性纯文件反例覆盖：相等、精确v→6、先保存再拒绝且输入不变、后续相等不覆盖旧FAIL、exclusive x拒覆盖、重复physical key保留、行排序、中文字符/字节偏移、重复JSON成员拒绝、schema浅引用与表行深拷贝、解析前与解析后两种合成机制产生相同最终对象。另有0x1F严格拒绝/正常转义最小复现。只AST编译七个纯helper，在本批私有目录写合成文件，不导入旧模块、capture/readonly/native或fixture main；不是MODEL/RPC/HTTP业务测试。

**离线证据止于采集后对象，数据库/驱动/内存/落盘分层无法由现存材料区分。** 三份目标值及各副本一致记录该差异，能够排除“这次P023比对只看hash而未核字段原字节”的证据缺口；不能确定原PG持久值是否变化、何时在哪层发生变化/恢复、raw text与解析后对象是否已不同、编码器输出缓冲/写入/后续保存何时出现另一0x1F。现有SHA/manifest证明本次读取字节符合旧封存记录，不提供每个更早边界的独立见证。缺少证据不能补造，尾审同值也不是数据库自行修复的证明。

|本批运行/修改预算|实际|
|---|---:|
|旧/新数据库连接、SELECT、CREATE、DML|0|
|Odoo加载、业务HTTP/RPC、浏览器、PDF|0|
|scope登录、文书、收退款、日结|0|
|安装升级、授撤权、产品/core/模板修改|0|
|sudo、OS/PG/Docker/网络/硬件专项|0|
|旧脚本/证据重写、Issue/Project状态写|0|
|冻结的主核验器进程|3，退出码1/1/0，全部保留；另有编译/清单/报告封存等纯文件命令，不计为业务进程|
|GitHub流程操作|正文/评论/ref读取、1条初预检+2条增量说明及最终交付；非业务HTTP|

P022 A仍BLOCKED_BEFORE_DOCUMENT_ACTIONS，B/C/D/E仍NOT_RUN；P021已采子证据及原22行退出历史不改。没有本批文书、资金、网络附件、T05、升级或PDF视觉PASS。没有当前数据库身份或经济事实的新读回，更不能把本批0连接写成P022零写，P022那次scope commit事实仍按原裁定保留。

固定证据阅读入口：

1. inputs.json与input-byte-verification.json：核47文件旧SHA/Git对象。
2. process-results.json及initial-run-correction.json：核真实两次失败、一次完成和已更正的文件定位。
3. diagnostic-fixed/file-diagnostics.json：看整文件严格失败与目标数组严格有效的区别。
4. 三份arch_prev txt与field-values.json：完整UTF8、hex、SHA可复算，禁止用strip改变值。
5. field-observations、comparisons、index-signature-token-checks：核字段偏移1992、token偏移2093和绝对文件字节位置。
6. cross-interpreter-comparison及same_capture_groups：核共同输出相同及重复保存不是独立测量。
7. saved-file-byte-pair、control-byte-minimal-reproduction、pure-counterexamples：核新的单字节事实及合成边界。
8. collection-save-chain和本报告：核源码路径、未捕获环节及不能确定事项。

以上均为文件阅读入口，不是启动数据库/网页的操作步骤。无产品部署或数据库更改，无需业务回滚；如需停用新增工具，只能另行线性提交并保留旧证据，不reset/clean/force-push或清理副本。正常提交推送新增P023报告、核验器和脱敏证据后，#34正式交付及REST全文逐字读回私有保存后立即STOP。后续数据库或业务必须另有正式授权；不自动续五组/P024/S11，不改Issue/Project状态，不合并或部署。
