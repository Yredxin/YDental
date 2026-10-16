# S10-P0-15 GAP-03 增量索引

仅申请 `S10_P0_15_GAP03_DELTA_AND_NEXT_ACTION_STATIC_TECH_ACCEPTED`，由 GPT 独立复核决定。本批是 Codex 对固定源码及公开脱敏证据的离线审计，没有新增业务 PASS。S10 整阶段技术、生产及 T12 继续 BLOCKED；原生 SIGSEGV 根因 UNKNOWN。

唯一授权 [6213938772](https://github.com/Yredxin/YDental/issues/34#issuecomment-6213938772)，P0-14 限定技术裁定 [6213877494](https://github.com/Yredxin/YDental/issues/34#issuecomment-6213877494)直接作为已生效事实引用，不重新裁定。原分支 `codex/s10-settlement-finance-r1-20261013`，唯一父 HEAD `a66c9dfd4b65573a27ff3e45733a87103f17bf32`；core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`。子提交由正式交付评论固定，避免文档自引用 SHA。

开工 GitHub API 完整读取 #23 正文/3 条评论、#34 正文/228 条有效评论、#35 OPEN/0；本地、origin 与 REST 远端 ref 匹配。正文及逐条评论 SHA 见 [github-start.json](evidence/s10-p0-15/github-start.json)。[静态预检6214014587](https://github.com/Yredxin/YDental/issues/34#issuecomment-6214014587)先于交付生成发布，REST GET body 逐字相等：2840 字符、5004 UTF-8 字节，SHA256 `a76f6ba21f1ee1ca60d190f1a25cfe25ce2c3b675786d387f957d163adf63e93`；[原文](s10-p0-15-preflight.md)/[读回记录](evidence/s10-p0-15/preflight-api-readback.json)。GitHub API 与正常 Git 推送是本批允许的外部操作；所有数据库、Odoo、浏览器及业务操作预算和实际次数为 0。

## 旧 GAP 保留及新增来源

原 GAP-02 固定提交 `0c972e1949191d62d84536f987a40f26dba57e03` 的 [coverage.json](https://github.com/Yredxin/YDental/blob/0c972e1949191d62d84536f987a40f26dba57e03/docs/evidence/s10-p0-10/coverage.json) 和旧报告原字节不改。[gap03-delta.json](evidence/s10-p0-15/gap03-delta.json) 每行保存完整 `gap02_original_row`，涵盖旧断言、旧失败、旧来源提交/库/有效评论、旧缺口，逐字段比较相同并固定 canonical SHA。新增来源列不覆盖原行结论：**7 SCOPED_ACCEPTED、14 PARTIAL、T12 BLOCKED，FULL_PASS=0**。

| 新来源 | 固定提交 | Codex / GPT 评论 | 可采范围及实际停止 |
|---|---|---|---|
| P0-11 | `0b64b1b143ca99dac0404d202d410a782d08421f` | 6209987413 / 6210167613 | W5 一次严格只读、643 表及25资格检查保全；补充执行检查点未发布，BLOCKED_PREFLIGHT，CREATE/Web/确认均 NOT_RUN。 |
| P0-12 | `cf6692c27d48ebabf1b7d4f3ab1ef99ef4cfef74` | 6210910862 / 6211057301 | 离线源连接与执行后证明合同冲突；BLOCKED_PREFLIGHT，数据库与原生操作全0。 |
| P0-13 | `6c64403f9c015c669e50e750aff6e0e7a2eab3c0` | 6211754121 / 6211928330 | 双源只读/单克隆/本人登录及临床首次GET保全；DOM和登录/source.view白名单合同 STOP，acquire/confirm/release 全0，未新增v3。 |
| P0-14 | `a66c9dfd4b65573a27ff3e45733a87103f17bf32` | 6212629752 / 6213877494 | 唯一新克隆 user7 本人原生原文确认 pending2→confirmed3；acquire1/confirm1/release1；源前后643表及克隆禁写627表全等、原钱货不变。仅 SCOPED_TECH_PASS。 |

以上固定提交的 `docs/evidence/s10-p0-N/verification.json` 路径、全文件 SHA 与原始完整机器结论均纳入新索引 `new_sources`。P0-11/12/13 是历史 BLOCKED，不因 P0-14 成功而改写。每行新增 P011/P012/P013 保全与 STOP 列；P014 列只在 F4/T08 标新增确认子断言 SCOPED_TECH_PASS。T12 虽引用同一子证据，整行仍 BLOCKED；其它行的新业务覆盖 NOT_RUN。生产配置/外部到账等受影响行另列 POLICY_PENDING。

| 行 | 原GAP-02状态（保留） | P0-14新增覆盖 | 原剩余缺口（逐字保留） |
|---|---|---|---|
| F1 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | W5 browser exit1、final_audit NOT_RUN；23步不在同一Firefox完成；外部现金到账未证 |
| F2 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 原F2全序列没有同一次真实Web和外部资金确认；响应丢失HTTP重放、更多审批同退款组合不足 |
| F3 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 合法错日期绕锁、不同业务日/渠道组合与实物退药同链、完整Web更正交互不足 |
| F4 | PARTIAL | SCOPED_TECH_PASS：P0-14只补结清后既存原文确认v2→v3及费库款零变；文字correct/数量/退药/原版/同Firefox全链均未补。 | 同一完整临床链补旧文书与原版重印、S08/S09必要HTTP回归及全链签名未齐；不合并跨库为单次PASS |
| F5 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 当前UI Web没有同一组合完整选择/付款证据；生产科目及币种映射待审核 |
| F6 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 跨店原生RPC/附件/完整票据直链及患者合并组合不足；角色矩阵未穷尽 |
| T01 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | W3只单次Web出账，未在该库并发；不同批次限制需保留 |
| T02 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | W5完成marker和final_audit未运行；真实现金到账及跨故障HTTP响应丢失不在本条已验范围 |
| T03 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 0元Web操作与所有折扣权限/审计组合尚非完整现场；原R3固定双连接未完成 |
| T04 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 不同请求key及响应丢失场景、外部付款核验未齐；锁对象种类未独立证明 |
| T05 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 真实HTTP响应丢失后同key重放与外部支付状态真实性未测；unknown与实际出款并发不足 |
| T06 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 适用合成模型路径；生产税额和财务映射未批准 |
| T07 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 合法业务日跨日绕锁、不同渠道/收费员组合仍不足；更正Web全入口未覆盖 |
| T08 | PARTIAL | SCOPED_TECH_PASS：新增仅原责任人原文确认及同源钱货不变；R3数量更正/退药分别是不同patient/store，不能拼W5全链。 | 同患者同接诊并结合W3费库款/报告重印后的逐行签名与Web动作不足 |
| T09 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 异币种、效期/配置失败、同source双事务订单及原生posted失败原子性未获匹配证据 |
| T10 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 跨法人医疗全文、附件/原生RPC、患者合并后的旧身份访问矩阵证据不足 |
| T11 | PARTIAL | NOT_RUN：P0-11至14没有PDF；P0-14 confirmed3不是票据或历史原版；W5当前paid740/0首份账单仍NOT_RUN。 | 批准在途、unknown/rejected/done、零额/多账组合的实际PDF逐页和法人店边界未全覆盖；GPT未亲见私有图 |
| T12 | BLOCKED | BLOCKED：只接受P0-14一个确认子动作；W4 metadata STOP/W5 exit1 final_audit NOT_RUN/R3 SIGSEGV UNKNOWN永久保留。 | W4元数据越界STOP；W5 browser exit1/final_audit NOT_RUN；同Firefox23步与完整上游HTTP回归未通过 |
| T13 | SCOPED_ACCEPTED | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 此特定多账组合真实浏览器未见；不同库结果不并成同次Web PASS |
| T14 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 全岗位、跨法人患者合并及原生RPC/附件拒绝未穷尽 |
| T15 | PARTIAL | NOT_RUN：P0-14未调价620、未重印；W5 price600旧快照和原版缺失不因新文书v3改变。 | 同一旧费源调价后原版重印与更正后的签名、驳回PDF/审计全字段组合不足 |
| T16 | PARTIAL | NOT_RUN：本行无新增业务；P0-11/12/13的保全及STOP不替代旧缺口。 | 合法时点而错业务日绕锁、跨日补录与同收费员全渠道组合、审计原生删除/RPC广度不足 |

## 来源及版本位置

[source-lineage.json](evidence/s10-p0-15/source-lineage.json)完整引用旧固定血缘及逐字段链，并新增 W5→P0-14 边；身份由数据库名、OID、cluster、marker/config SHA、克隆签名共同确定，禁止仅按数值 ID 拼链。

| 来源边/家族 | 固定事实 | 本批读取层级 |
|---|---|---|
| W3 OID2100285 → W4 OID2100301 | 旧38表签名/parent marker匹配；W3 `71a554667157cdd917c0062db5e4ddf1693f6410` → W4 `79417da9043478501ffae586f93eebc1e5d7105d` | 固定公开证据，只读文件 |
| W4 → W5 OID2100310 | 旧38表签名/parent marker匹配；W5 `287881a824e9a18dd637522c570f74df139078f9`；后续只读核账固定 `5876740dabf342372b0970682947e6be8356fa8c` | 固定公开证据，只读文件 |
| W5 → P0-14 OID2100326 | `clone.json` source_oid2100310、initial643全等、config/marker SHA；源前后独立643全等；新库 `ydental_s10_test_20261016_p014_7c42a9e1`；cluster7694897083368259627 | 只引用 P0-14 固定证据/GPT裁定；没有连接或打开克隆 |
| R3/P0-09 独立家族 | R3 OID2056451、`f24b0302569aefaa394391da6b696d915e3f0616`；不是 W 家族父边 | 禁止拼接患者、费源、发票、PDF为同源业务 |

永久 W5 的固定源事实仍是 doc1/patient1/store1/company1/responsible7、pending/version2，原文 SHA `678e527db07b38518de9522b056d45c9a4f5f5da775d07e112c5360f0ced21aa`。confirmed/version3 只在 P0-14 新克隆成立，新增版本 kind=confirm/author7/previous2；不是文字 correct，也没有永久修改 W5。该克隆、文书及其原始私有材料本批不使用，未来也不得作为业务模板。

W 家族四费源映射保持：source1→fee4/20，source2→fee3/40，source3→fee2/80，source4→fee1/600；invoice1 posted740、付款500/240、两条原生partial、residual0。治疗event1使用snapshot1、inventory3/move3/lot2；检查event2使用snapshot2且无假库存；两次发药event3/4分别qty4/2，snapshot3/4、inventory4/5、lot1。这里只复用旧公开同源事实；本批没有重收、重出账或重做发药。

R3数量更正event13→14/fee13→14/source13→14/invoice78→credit79在 **patient4/store7**；R3退药inventory4→19/lot1/move19/line26在 **patient1/store1**。这两个R3子例本身也不能拼成同患者同接诊，且都不能移植为W5的已做动作。旧退药位置投影24→22可引用；隔离库配置字段当时没有独立投影，本批只从固定 `_return` 源码证明应进入 quarantine，不把静态规则伪称旧SQL已独立证明的配置。

## 仍阻断的实际业务与原件

纯文字 correct 需要独立合法已确认父文书、原责任人、可审核的纯合成非医疗更正文案。现有唯一新增v3在禁止复用的P0-14克隆；旧W5仍v2。结论 **NOT_AUTHORIZABLE_PENDING_SOURCE**：不能重复确认W5 doc1以准备更正，也不能仅为了v4伪造原文/诊断。完整源码合同及未来准备差异见 [下一工作合同](s10-p0-15-next-executable-contract.md)。

`ydental_print_job` 的历史五来源计数0、P0-14源签名计数0，仅限定这类临床/处方/consent短期任务不存在。S10结算 `_pdf` 每次当前渲染并且 `report_pdf_no_attachment=True`，不经过该job模型；所以job0不等于整个系统从未有PDF。旧索引保有R3八份外部PDF的字节/hash事实，本批没有打开原私有PDF、没有新渲染/视觉核验，不能把R3样张当W5历史原件。

W5目前公开索引没有同源可用原始PDF字节及可追溯原版票据对象；**原版重印 NOT_AUTHORIZABLE_PENDING_SOURCE**。新生成当前paid740/0账单只能叫“首份当前内部账单PDF”。它既不证明600→620后历史原版重印，也不代表S12正式税务原件。生产科目/税/币种和银行/渠道实际到账政策、S13最终统一用户验收仍待批准/完成。

T12历史23步依次为：reserve、arrive、report_care、care_start、document、treatment、exam_order、prescription、care_handover、report_exam、exam_start、examination、report_pharmacy、pharmacy_start、dispense_four、finish_first、report_remainder、pharmacy_restart、dispense_two、finish_final、bill、pay_five_hundred、pay_two_forty。列表来自固定 `scripts/s10_e2e_w3_browser.py:28` 的AST常量提取，没有执行该脚本。完整同Firefox23步仍未通过，不建议重放旧收款以补表。

W4元数据682行write_date及依赖加载越界STOP、W5 browser exit1/browser-complete缺失/final_audit NOT_RUN、R3 registry后的Native SIGSEGV exit-11/另守卫-2和根因UNKNOWN永久保留。完整S08/S09真实HTTP回归、同源更正/钱货/票据联动也尚未闭环。P0-14单条确认及引擎exit0无法抵销这些失败，P0-14原诊断UNKNOWN也照原裁定保留，不另启OS/PG/Docker/网络专项。

## 离线验证及交付边界

新增 [分析器](../scripts/s10_p0_15_static_audit.py)只解析固定Git源码AST/文本和本批新增GitHub读回记录，不导入addon、不执行旧入口或SQL字面量；提取每方法真实路径、起止行、源码SHA、固定Git链接及直接调用集。[static-action-contract.json](evidence/s10-p0-15/static-action-contract.json)保留实际方法文本，读者可独立判断静态结论的边界。断言覆盖CAS/confirmed guard/作者与parent version、原价继承、quantity kind限制、return上限/quarantine、render无attachment和短期job原字节交付约束。它不证明动态资格、原生PDF依赖或业务执行成功。

运行 `python3 scripts/s10_p0_15_static_audit.py --verify`，核对22旧行逐字段相等、固定源字节/AST、所有原有tracked文件及core未改；产出 [verification.json](evidence/s10-p0-15/verification.json)及[全新增文件SHA索引](evidence/s10-p0-15/sha256-index.json)。索引不递归哈希自身，其SHA及最终父子提交由正式交付评论固定。分析器开发时曾发现一个路径名和两个源码符号假设错误，均在纯离线阶段修正；没有据此执行任何数据库/原生操作，记录于新增离线检查日志。

数据库连接/CREATE/Odoo HTTP/Firefox/全部业务GET和POST/Odoo CLI或ORM/资金库存附件PDF写/sudo全0；旧产品addon/ACL/core/AGENTS/报告/历史证据、Issue正文和状态、Project均零修改。本批没有下一业务READY结论：先补哪个最小源门禁、唯一候选的精确按钮和断言均在下一工作合同列明。正常线性提交/推送及正式回执REST逐字读回后立即STOP，等待GPT，不自行授权P0-16、S11或整个S10通过。
