# S08-C 工程交付与阻断复核报告

**结论：BLOCKED，不能申请技术 PASS。** 首版三类中文演示 PDF 和受控入口代码已提交，候选运行生成真实 PDF、完成部分权限/并发和 Firefox 原生打印验证。但固定 test 在原生 Odoo post-tests 阶段发生新的 SIGSEGV；已停止全部 Odoo/浏览器/测试重跑。之后对既有候选文件的逐页核对还发现 RX-2 长处方空白页与正文严重缺失，必须修正并重新验证。本批不是用户验收、正式医学/法律签发或生产通过。

## 1. 需求完成情况与固定边界

唯一授权 [GPT-ACTIVATE6137113212](https://github.com/Yredxin/YDental/issues/32#issuecomment-6137113212)。完整读取 #23/#32 正文及初始 3/20 条评论，交付重读 3/21 条；原正文与原评论字节不变，仅新增本批[开工检查6137191852](https://github.com/Yredxin/YDental/issues/32#issuecomment-6137191852)，已逐字读回。#36 仅核对未来 S12 边界。

|固定点|SHA / 状态|
|---|---|
|B baseline|e95b77d1ebd2ff55331e777adedf32efe81fdfbc|
|C product|8794f1c6d6d7f4a8e76c64edddfb0c49c85e3fe2|
|C test|87b2c8588ac3012abce7d9db5f26dc5682dc4e7d|
|C final|本报告所在 final commit，完整 SHA 固定在 #32 阻断交付评论；不自引用 SHA|
|分支|codex/s08-c-pdf-print-r1-20261013|

新增 ydental_print 的只读来源适配、QWeb 报告、临时 job、受控 HTTP/界面、中文翻译与审计。没有修改 S01—S08-B 产品字节；ydental_treatment_test 仅增 C 隔离库 guard 适配。product→test 仅四个验证文件；test→final 仅 AGENTS/文档/脱敏证据。没有部署到原有服务。

原生核心为 f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，复用 Odoo20 ir.actions.report、base_report_wkhtmltox、qweb-pdf-wkhtmltopdf、既有 patched Qt wkhtmltopdf 0.12.6.1 和 Noto Sans CJK SC。没有 OCA、第二病历/药房/库存/财务账本。

病历明确选择独立文书/不可变文字版本，显示 D1/D2 原作者、责任人、原/当前段、7 字段、FDI/牙面和保存/确认状态；处方取真实药品 SKU/规格/单位/用法/频次/疗程和真实事件逐行实发量；同意书八栏保持空白、待审核/未签署。每份附来源版本集合、模板号、来源 SHA、生成者/UTC，均非完整正式病历或收款凭据。详见[字典](s08c-data-dictionary.md)、[契约](s08c-contracts.md)、[安全复核](s08c-security-review.md)。长处方分页未达交付标准。

## 2. 已真实执行的流程回放

以下全部是本批新合成库中的候选回放，固定 test 的最终全量链没有完成。逐份来源/版本/事件、生成前后 17 表签名见[候选结果](evidence/s08c/probe-attempts/20261013T043822532357/result.json)。

|流程|真实来源与实际结果|范围限制|
|---|---|---|
|C-F1 独立文书|同患者313：D1 document316 多次保存、交还 pending v4；D2 document317 独立文字确认 v1。两位作者分别为合成医师甲 D1/乙 D2，未由 D2 覆盖 D1。D1 草稿/待完善各7页，D2独立确认2页|独立来源样张，不汇总成正式完整病历|
|C-F2 6→4+2|order84 line141：issued6/已发0/余6→event73发4/余2→event74再发2/余0。实际 pharmacy/fee/stock 由 B 服务产生，打印前后不追加事件|不是纸张回执或资金实收|
|C-F2 多SKU|order86：取消旧行158；有效159/160/161分别真实SKU503/506/508，真实价源10/27/43；事件75/76/77分别实发4/2/1，159余2；次日事件78再发2，done|次日通过测试进程本地 Datetime patch，不修改系统钟、不冒称真实日期临床操作|
|C-F3 同意书|真实同患者/文书来源版本的2页样张，医学内容/签署/监护授权八栏空白；显著待审核/未签署|无法定审核、无签名/电子签章|
|C-F4 历史更正|D2旧确认v1和更正v2分别生成，旧文字仍来自immutable version；原作者/原因/前序清晰；处方草稿旧取消行保留|不是永久原件库或原版重印|
|C-F5 权限/并发|候选5组真实不同初始PG backend/barrier；包含源写入在实际渲染中提交，PDF保留旧快照；重复key、撤权、交还和重复打印有断言|最后候选5组PASS/deadlock0，未运行固定test的A16+B25+C5整套46组|

Firefox候选 fa8377b 为真实 headed Firefox：43项/14图/pageerror0，3类实际 PDF 查看、下载、Ctrl+P 原生对话框，均取消。响应屏障、丢响应、离线/恢复及只有read无export拒绝有截图。14图已逐张实际查看；此轮处方仍为 RX-1，不能证明固定 RX-2。见[结果](evidence/s08c/print-browser-attempts/20261013T043328099034/result.json)和[人工核对](evidence/s08c/candidate-firefox-visual-review.json)。

最后候选 a94e68e 原生生成16 PDF/61页，已全部逐页查看。普通短处方、三SKU、D1/D2和同意书可读；**最大长度16行处方 RX-2 第7页仅页脚，第9/10/12/13/15/16页正文严重缺失**。原自动文本/字体/重叠检查漏检，不能将其 PASS 用作验收。早期 RX-1 第3页也有文字重叠。见[人工 FAIL](evidence/s08c/candidate-page-visual-review.json)，所有原始自动结果与失败截图保留，未在崩溃后修改产品。

## 3. 逐项测试、失败与固定执行结果

状态有两个维度：候选单项结果按各自 SHA 保存；**固定 test 最终验证全部 BLOCKED/NOT_RUN**，不能跨提交拼成 PASS。[最终状态](evidence/s08c/final-tests.json)、[C与S08逐项矩阵](evidence/s08c/tc-matrix.json)、[测试方法索引](evidence/s08c/test-methods.json)、[真实尝试/命令/退出码/日志hash](evidence/s08c/attempt-history.json)。

|关口|候选已执行|最终裁定|
|---|---|---|
|C-T01 三类二进制/中文/多页/下载|16份真实二进制；Firefox3份实际下载；61页人工查看|FAIL：最大长度处方空白/缺正文；固定链BLOCKED|
|C-T02 D1/D2/历史文字|独立源、责任人、确认与更正样张/模型断言|候选单项PASS；固定BLOCKED|
|C-T03 处方各状态/4+2/多SKU|真实事件/价源/跨日、取消和不完整草稿|来源数量候选PASS；长处方版式FAIL；固定BLOCKED|
|C-T04 未签同意书|2页真实样张/8空栏、模型/Firefox|候选PASS；固定BLOCKED；正式签署NOT_RUN|
|C-T05 权限/审计|候选15模型+7HTTP覆盖源+导出/药房/跨店用途/撤权/RPC/附件/原生报告/CSRF/旧revision/公司|候选22项升级PASS；固定BLOCKED，新增第8 HTTP故障用例未运行|
|C-T06 竞争与失败|候选5组真实PG屏障PASS、重复/源改版；字体缺失/引擎超时故障注入；Firefox响应丢失/离线|BLOCKED：新原生SIGSEGV、最新corrupt PDF/QWeb故障包装未验证|
|C-T07 安装/升级/持久业务/A/B|新库安装确实执行但整次FAIL；多个print-only候选升级PASS22；候选打印17表签名相等|BLOCKED：无同一固定test新库完整链、无带业务升级签名验证、A/B双连接/Firefox均NOT_RUN|
|C-T08 POT/中文/隐私/恶意输入/视觉|真实export退出0，候选POT176项/手工PO映射176项；代码审查和负向候选断言|FAIL：版式；完整翻译CLI NOT_RUN，固定运行BLOCKED|
|S08-T11/T12/T16|对应上表；打印经济签名候选及崩溃后只读证据|T11 FAIL；T12/T16固定BLOCKED；不援引旧A/B PASS|
|隔离guard|候选运行5项；真实端点/OID/marker/config/PID/外发guard|候选PASS，固定完整guard NOT_RUN|
|生产/设备/正式签发|未运行|BLOCKED/NOT_RUN|

固定失败命令（真实执行，非建议命令）：

```text
../.venv/bin/python scripts/s08c.py upgrade --db ydental_s08c_test_20261013031800_b81ae5c3 --port 18178 --print-only
```

PID1670701，原生退出 -11/signal11，外层shell245，tests=null；日志 upgrade-20261013T044559893521.log，SHA256 07e23e987e415a50255789fbe9721b1d10e8931977d77fe4761ec7b1819f6909。最后日志为 registry重载、QWeb原生资产预生成至04:46:06.955，04:46:08.090退出，无本次test方法/总结。configSHA3b3d578bb0c8539d5865b07929ab0c0abe6278ccd1236076b351f5b7e606f182；OID1319789，cluster7694897083368259627。没有匹配core或可恢复原生调用栈，coredumpctl未安装；apport pipe/var_crash/journal只读核查未获得本次堆栈。**根因UNKNOWN**，不以PG OOM=false、shm37%或原服务健康证明任何原因。见[崩溃证据](evidence/s08c/native-crash.json)和[脱敏日志尾段](evidence/s08c/native-crash-log-excerpt.txt)。

原候选失败链全部保留：初始翻译provenance元数据导致install255/testsnull；第二库install1/[6,8,99]（旧A/B78方法未失败，新增C失败，安装另2原生资产初始化，不能称全JS）；之后C参数/ACL/报告scope/字体UTF8、价fixture导入、RR重复key唯一冲突、FOR UPDATE与用户外键阻塞、兼容汉字抽取NFKC、空页/重叠、Firefox工具缺失/旧iframe定位器超时、离线前提等逐步诊断与修正。原日志、原SHA、原错误和不同候选库不删不覆盖；诊断脚本PASS只表示相应诊断完成。最新fault handler未完成验证。脱敏证据整理脚本曾选错两库列表末条日志exit1，定位后按精确PID取记录exit0；这是文件整理错误，不是Odoo测试重跑。

离线证据完整性检查首次误用未安装的pypdf导入exit1；改用本地既有pymupdf后exit0，无安装/环境调整。23份原日志hash、最后候选16PDF/61PNG hash、83份PDF元数据和报告相对链接核查通过，见[完整性记录](evidence/s08c/artifact-integrity-check.json)。这些是文件保全检查，不是重新运行PDF渲染或产品测试。暂存全量空白检查报告9处原生PDF抽取文本尾空格，包装脚本exit1；证据原样保留，随后仅排除原始抽取文本的文档检查exit0。首次文档提交d420d861仍保留，未改写历史；完整记录见publication-checks.json。

尚未执行的固定全量入口 scripts/s08c_validate.py：拟新库install103、upgrade101（原A/B78+C23，安装另2原生资产初始化），带业务再升级101、46组真实竞争、A88+B24+返工23+C43 Firefox、翻译/guard/签名。这些是脚本断言目标，**实际均NOT_RUN**；最终新库未创建。

## 4. 字段、动作、配置与审计

字段逐项见字典。模板CLINICAL-1/RX-2/CONSENT-1，A4/zh_CN/全部未审核；初版临时演示副本，不建立正式签名账本。preview/generate/pdf_view/download/print_request都校验真实 S01 Binding/session/revision、当前店/公司/患者关系、源读取与export-write；临床走A接口，药房仅本店真实issued/done+药房task窄投影。

原生report/RPC/伪JSONcontext/附件直链不能替代受控入口。数据库BinaryBytes attachment=False、NO_ACCESS、无普通ACL；Python冻结RenderScope固定服务器来源，静态QWeb t-out转义，无任意模型/字段/domain。输出no-store/private、固定无患者名下载名，交付期限15分钟；已合法获得本地副本不能远程收回。

记录生成/重复生成/查看/下载/print_requested独立S01审计，失败denied及failure_kind，纸张unknown。无paper_printed。400KB来源、100行/500事件、10MB/80页、字体5秒/引擎30秒上限；浏览器45秒超时、断网清除资格，恢复需人工核对，响应丢失不自动重放。最新corrupt binary/原生异常脱敏处理代码已提交但测试未完成。

## 5. 用户效果核对步骤（阻断解除后才可执行）

当前不提供重启/实测指示，以下为复核后的验收步骤，**本次用户NOT_RUN**：

1. 用新隔离合成库医生选择当前门店，进入受控演示PDF入口。
2. 分别选择D1待完善与D2独立确认版本，核对原作者/责任人/牙位/内容与明显状态。
3. 生成并下载病历真实PDF，逐页核对中文、长文、来源版本与页码。
4. 选择处方在6未发、4余2、再发2三个时点生成，核对每个SKU/规格/实际药师/时间。
5. 核对取消行与最大长度16行长处方，无空页、缺正文、裁切或重叠；这是现有FAIL必修项。
6. 生成同意书，确认八栏未预填医学结论、患者决定、签名或日期，始终待审核/未签署。
7. 请求浏览器打印，核对原生PDF对话框并取消；界面和审计不能写设备已出纸。
8. 撤权/切店/改版本后用旧标签尝试下载和打印，确认服务端拒绝；核对审计与经济签名不变。

## 6. 数据保全、环境调整与回滚

仅新增两个C合成库并全部保留：a31e9b72（OID1304322/18177，安装失败）和b81ae5c3（OID1319789/18178，候选+SIGSEGV）。原117库OID/名称全保留，总119，未重置/删除/修改历史库。Docker db20镜像/卷/启动身份/shm256MiB、odoo12身份不变；核心tracked不变，原Odoo42433健康HTTP200。没有全局服务/参数/依赖修改。只在本批libpq会话关闭并行/维护16MiB。

为了真实headed Firefox原生对话框，7个Ubuntu包下载解包到.local/s08c-tools（哈希/版本见[清单](evidence/s08c/local-tools-manifest.json)）；独立Xvfb:107及bwrap私有mount补xkbcomp，无系统安装/默认sandbox禁用。首次工具包装留下自有Xvfb子进程，按完整路径/:107核验精确PID1638740后SIGTERM，后续改进自有进程组清理；不泛称全程exit0。Odoo预览仅按configSHA/PID精确停止，正常退出0；最终失败进程为signal11。崩溃后无重启，无本批存活预览或display。见[环境保全](evidence/s08c/environment-preservation.json)。

崩溃后只读psycopg2连接核验端点/cluster/OID/marker/config，41类SQL不变量全0；27表签名保存，17张业务/来源表与崩溃前最后候选样张签名相等。account未安装，不以不存在的会计表证明款项联调。这是保全证据，不是升级或全回归PASS。见[只读审计](evidence/s08c/post-crash-readonly-audit.json)。候选每次纯PDF操作17表签名相等，真实治疗/药房动作在回放阶段另行发生。

Project完整21字段/15条目/6视图及各视图字段/7公开workflow开工双读、交付双读深比较一致，0mutation。#32保持S08/进行中/Todo/OPEN，#31待用户验收，#33—37待启用。见[完整快照与比较](evidence/s08c/authority-and-project-final.json)。

回滚：现有服务未部署C，无需回退历史业务。冻结本分支与失败库供复核；若后续授权停止C，在新的独立工作树选B baseline，仅停止精确匹配C config/PID的进程，不对C数据库运行降级/uninstall/drop，不把B旧模型直接挂到已升级C库。正式数据库回滚/全树迁移、生产恢复演练NOT_RUN。原始日志/配置/凭据/失败材料本机受控保留；仓库仅合成PDF/PNG、脱敏摘要、日志hash/来源hash，[脱敏说明](evidence/s08c/publication-redaction.json)。

## 7. 独立复核申请

请求GPT核对固定product/test/final、源权限/字段/审计契约、实际候选证据，以及两项阻断：新的原生SIGSEGV和RX-2长处方可视FAIL。不得裁定当前C技术PASS。请给出后续诊断/修正与同一固定test新隔离库完整验证边界。本批未将C失败归罪于已通过A/B业务，也未以旧A/B结果替代新回归。

正常push并核验远端SHA/产品tree；#32发布“[CODEX] S08-C BLOCKED与技术复核申请”，逐字读回后立即停止。没有关闭Issue、改Project、合并/强推、启用S09或生产部署。

## 8. 未做与剩余风险

新SIGSEGV根因/堆栈缺失、RX-2空页/正文缺失机制、旧S07 SIGSEGV、B浏览器崩溃和原生serialization重试耗尽均未闭环。新fault wrapper未完成测试；自动PDF验证存在漏检，必须结合逐页人工核对，不能拿文本抽取证明全部可见。完整A/B模型/HTTP/Firefox/双连接与安装升级/持久业务/翻译固定链NOT_RUN或BLOCKED。

正式医学字段/模板/用药/同意书法定审核、专用print资格政策、可靠签章与监护身份、正式永久原件/原样重印、设备出纸回执、S09真实结果、S10收退款、S12报告、50会话/生产性能、完整历史源码树迁移与生产回滚均未完成或未授权。**生产继续BLOCKED**；本交付严格为Codex工程自测和阻断技术复核申请。
