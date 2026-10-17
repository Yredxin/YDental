# S10-P0-20 功能收尾交付：A已完成，B经济不变量取证不足触发STOP

结论 **BLOCKED_B_TEXT_ECONOMIC_SIGNATURE_MISMATCH_NO_PREASSERT_FULL_DIFF**。当前不能申请S10阶段技术通过。可以提交A“真实已结清账单入口/当前内部PDF”的限定子证据独立复核；B三组业务收尾及阶段退出条件未齐。不是把检查器PASS当功能交付，也不把瞬时回滚中的金额/动作输出当已提交全链。

依据唯一授权[#34/6228862519](https://github.com/Yredxin/YDental/issues/34#issuecomment-6228862519)。P019裁定6228828303永久保留；没有重跑其窗口。父/固定产品`a2fa26e37d350910668742869764c9ed102641ca`，原分支`codex/s10-settlement-finance-r1-20261013`，origin为Yredxin/YDental。Odoo core固定`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。本批产品文件零变化，不创建新的产品提交；最后证据提交由正式回执固定。

## 预检与有限修复记录

完整读取#23正文/3评论、#34正文/248评论，旧244评论与P019保存正文逐字一致；#35—37 OPEN且未启动。起始工作树干净，远端HEAD匹配，未见同批并行进程/已有预检或交付。逐评论SHA在[开工索引](evidence/s10-p0-20/github-start-index.json)，完整响应私有保留。

[正式预检6229023871](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229023871)于03:26:25 UTC发布、03:26:35.479924 UTC REST GET逐字相同。正文11458字符/20041字节，SHA `ff1360ba80761105cd7f256c7f0fb724df21dd3cb52d0a73fb20b8d436c2bfd3`，初始执行冻结SHA `91c02df09041a053cd8c4e3d27f29da045a523f2d880113d50f78a7cefeb84ca`。读回前运行0。33项比较器/共享事务纯文件检查和3项工程检查exit0；原生预算与fake cursor/fixture严格分开。

B首轮新仓库配置失败后，[R1定向修复增量6229073507](https://github.com/Yredxin/YDental/issues/34#issuecomment-6229073507)于03:31:52.742277 UTC REST逐字读回。正文SHA `b1112a56a19c4cb6c004d13c1a0de0113e44510ff0aa583a231153ece8867f50`，增量冻结SHA `db385577f75934834fa64162c0ff8f7c88c35ef8103f6a4dbf2d7d23cd489264`。用掉1/2定向修复；原轮脚本及冻结完整保存在round0，不覆盖旧版本。剩余一轮未用于突破未知经济结果STOP。

## A：真实页面和当前PDF已完成

新副本`ydental_s10_p020_20261017040000_20a0cafe` / **OID2100333** / port18320 / cluster7694897083368259627。新建前W5只读连接已关闭，maintenance/CREATE各1，filestore copy2真实复制。独立前审643表和完整继承族与源相同。唯一官方XML同步/metadata commit各1；先保存完整before/after/full-diff和脱敏索引再门禁，提交前、独立提交后均PASS。沿用P019物理(schema,table,id)、child/shared-parent/ONLY条件，无整表豁免。

user5本人原生Firefox登录GET1/POST1，默认store1。redirect工作台1 + patient1真实筛选GET1。既有invoice1显示posted/out_invoice/paid，总740、余额0，在“已结清本店账单”只读区且不在未清账单勾选。真实页面链接“下载当前内部账单 PDF”点击/GET/render/download各1；未直接访问地址、注入按钮或修改余额。A原生HTTP/Firefox均正常exit0。

[真实患者筛选页面](evidence/s10-p0-20/A-patient-page.png)、[默认页面](evidence/s10-p0-20/A-default-page.png)、[PDF字节](evidence/s10-p0-20/A-current-internal-bill.pdf)、[实际单页图](evidence/s10-p0-20/A-pdf-page-1.png)。中文逐页实际目视PASS，无重叠/裁切；20+40+80+600、实收核销740/余额0、法人/店铺/合成患者编号对应。PDF文件SHA=响应X-YDental-PDF-SHA256=唯一report_download审计SHA。**原合成币种实际为USD**，没有改为生产CNY、税务发票或支付平台证明；本报告不以“740元”掩盖实际币种。

请求intent/request/dispatch/response/failure/cancel/close同步持久化；browser/server完整计数与状态相同，redirect GET计入2。静态GET7/translations1。原生累计backend metadata1/Web12、Web观测池占用最大5≤8；不再使用累计≤池容量4错误阈值。原生DSN观测postgres+新副本，逐PID精确归属UNKNOWN，未根据线程猜测。

A独立尾审PASS：Web实际只改变res_device_log/res_users_log/ydental_access_session/ydental_access_audit四表，新增6条S01审计；身份技术写和新资产附件实际均0。许可metadata导入的差异另核；所有原经济、临床、权限、旧附件事实及152旧文件不变。不是声称登录/页面数据库绝对零写。execution-result的zero_budget仅是A控制器范围，不能当B新业务尝试0；其source-after0为延后最终核对，最终source-final-decision已补齐。pdf-result的visual PENDING是下载时状态，后续实际图像目视结果在A-pdf-visual-review单独记录，不回改旧执行输出。详见economic-web-verification、metadata独立diff/decision、http-reconciliation和request-events。

## B：失败、修复与未知差异

新B库名称/新OID/端口见[B-created](evidence/s10-p0-20/B-created.json)，独立template0原生正常安装`l10n_cn,ydental_settlement_test`及既有真实依赖，**install exit0**。不来自W5，不复用任何保护失败副本。新B首次f1在 `_setup`前因多仓库/库位设置未开启UserError/exit1；没有进入库存、费用、收款。首次RO尾审错误猜测`ydental_patient_patient`表名导致UndefinedTable，连接rollback/close，无完整快照，不记PASS。

R1先以实际catalog逐表完整RO/RR快照证明12类来源/经济表全0，确认首轮fixture事务回滚。新B配置管理员仅通过固定native `_apply_group`启用多仓库、多库位、价目3既存功能组，记录精确base.group_user→feature边；未改任何ACL文件、record rule或业务鉴权，不使用sudo。配置是本批全新仓库/演示价目的真实前置，A/W5不变。[最终配置差异核验](evidence/s10-p0-20/B-native-configuration-final-verification.json)证明仅3边、base group技术日期、4类native cache信号各1，其他表全等。

R1首个场景实际运行了新的治疗600、检查80、药房4+2/库存、调价620后旧源仍600、posted740、350后欠390、补390结清、原生partial2。原责任人结清后acquire/confirm/纯文字correct/release均调用。随后`s10_p0_20_b_f1_740.py:99`的 `signature()==before_text` 失败，exit1；B PDF和业务commit均未到达。

**验证器缺陷和证据限制：** signature使用全部ORM `search([]).read()`的表示做哈希，未在断言前保存两侧完整字段值、逐行全差异或是哪张表不同。不能区分实际经济字段变化、计算字段或读取表示差异。根因 **UNKNOWN**，不能事后添通用忽略字段、重跑以伪补本次瞬时证据，也不宣称已证明产品损坏。该门禁失败触发未知经济结果STOP，所有新业务入口关闭；没有用剩余修复轮次继续付款、文书、PDF或下个场景。

[完整实际失败片段/中间输出](evidence/s10-p0-20/B-runtime-failures-redacted.txt)保留首轮与R1；其中350+390和posted等为**回滚事务中的中间事实，不是提交PASS**。B-current PDF0、普通前台Web0、其它11场景0、升级0。两次失败fixture及所有旧资料原样封存，未另换库绕过。

最终独立新B RO/RR完整快照在裁决前落盘；患者/店/库存event/move/治疗event/fee/source/payment/refund/doc/version/native account.move/payment/S01 audit均0。场景经济/临床提交0，首轮和R1都已回滚；仅允许的原生初始chart/feature配置保留。尾审能证明保全，**不能倒推瞬时哈希差异的字段或原因**，不抵消原失败。

## 数据保全、预算与测试范围

W5最终唯一后验在B停止以后执行，严格RO/RR并rollback/close。前后643表/schema/继承投影全部相等，config/marker及152文件封存全等。源2连接、A审计3、显式maintenance2、B独立RO3（首个失败），显式共10；native A13+B7=20，累计物理连接共30。B安装原生还观察postgres目录读取，按授权明示，不当旧库业务连接。池A实测最高5/B最高2、配置8；每PID数据库归属UNKNOWN。详见[实际预算](evidence/s10-p0-20/actual-budget.json)与A/B-native-connections。

CREATE2/2，Ametadata导入/commit1、A登录1/PDF1；B安装1、首场景2次尝试、定向修复1/2，经济业务commit0。B独立RO一次失败+R1前审+最终=3；新数据身份均按新OID/原cluster绑定。所有源、A/B显式审计连接关闭；自有A HTTP/Firefox已退出，B HTTP/Firefox未启动。无Native SIGSEGV新标记，原历史根因继续UNKNOWN，不能据此称稳定性已修复。

受保护OID2100325/2100326/2100327/2100330和所有旧失败库0连接/复用/修改/清理。旧500+240、refund14、close9/权限负向、refund13分页及旧文书0重放。产品/core/S01—S09/旧报告证据/AGENTS不改，Issue/Project状态0、sudo和OS/PG/Docker/网络专项0，未合并部署或启动S11。没有运行完整原生模块测试套件，不能把36个离线检查和A成功说成其通过。

## 阶段退出和最低补齐动作

[最终22行退出表](s10-p0-20-exit-table-final.md)及[全历史/版本来源JSON](evidence/s10-p0-20/exit-table-final.json)逐行保留旧GAP-03/GAP-02，纳入P016资格/P017静态/P018失败/P019元数据和本次A子证据。没有删除旧失败或扩大适用范围。S10仍阻断，当前不申请阶段技术通过：

1. **F4/T08/T12**：先用实际持久字段合同和真实源码制定稳定比较器；事务内每个动作前/后完整snapshot/diff必须在断言前保存，所有变化逐字段解释，不通用忽略。当前瞬时差异不可追补。GPT对STOP另行裁定/授权后，在新的合法来源完成文书与费库款不变量及三组必要联调，保留新旧失败；不重放W5或本次未知场景。
2. **F2/F3/F5/F6与T03—T10/T13/T14/T16必要缺证**：本批原三组脚本尚未执行，需在修好取证门禁后按最小新来源验证财务状态、选中核销、跨日/渠道/收费员更正、权限/导出/附件/审计与实际跨法人链。兼容历史证据可复用，不能以“相同方法”扩大到原未测组合。HTTP结果丢失/重放和附件原生矩阵仍按实际缺证列出，不要求生产平台真实到账来证明合成技术。
3. **T12升级**：B正常安装exit0只有安装子断言；还缺带已提交同源业务的S10限定升级及前后完整保全。
4. **F4/T12/T15原版**：W5无同源历史原件，当前PDF不冒充历史原版。新合法同源链应先保留可追溯原始PDF再验证调价后原样取回。S12完整正式来源/模板快照体系和此S10显式TC承接关系需GPT裁定，Codex不自行免测或补造旧件。

S12正式模板/税务原件与完整快照、S13统一美化/50活动会话/持续备份/最后统一用户效果验收、生产科目/税/币种/渠道审批分别列后续待办；不是阻止所有后续开发的混合硬门槛，也没有把S10缺失职责全部推给后续阶段。

## 当前已可观察的用户效果（合成范围6步）

1. 合法user5原生登录，页面显示当前store1。
2. 打开结算工作台，看未清账单与已结清账单分别展示。
3. 在本店已结清区看到invoice1总740、余额0，没有付款勾选。
4. 使用患者筛选表单筛选patient1，仍看到同账单与真实链接。
5. 点击一次“下载当前内部账单 PDF”，得到一页中文当前内部账单。
6. 核对PDF的四费源、740已收/0余额、法人店铺和内部演示声明；这不是税务开票/平台到账/历史原版或S10全阶段验收。

## 固定材料与回滚

最终提交、全部逐文件SHA256和索引自身SHA由#34正式回执固定。实际执行源码原/增量哈希、HTTP实时账本、SQL/metadata白名单、正反例、失败片段、A页面/PDF/视觉核验、前后/尾审签名、完整脱敏差异索引和22行退出表均随证据提交。原始私有大快照、密码、cookie、CSRF、SID及未脱敏HTML不上传。

无产品改动可回滚；不用逆向SQL删除A合法metadata或B原生配置。A/B和日志/marker/filestore封存保留、不DROP/重置；将来代码回滚只能正常revert具体新产品提交且另经授权，不能从本批报告推导部署授权。正式BLOCKED回执REST GET逐字读回保存后立即STOP，等待GPT独立技术复核，不启动下一批/S11。
