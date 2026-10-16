[CODEX] S10-P0-11 W5原责任人pending文书一次确认与费库款零变正式预检

执行依据：唯一正式授权 https://github.com/Yredxin/YDental/issues/34#issuecomment-6209310360 ，上批独立裁定6209255943。已用GitHub REST API完整获取#23正文/3评论、#34正文/213评论、#35 OPEN/0评论，逐条保留完整响应与正文SHA；当前末尾为6209310360，没有其后新授权或既存P0-11预检/交付。固定commit API核对；origin=https://github.com/Yredxin/YDental.git，唯一分支codex/s10-settlement-finance-r1-20261013，本地/远端HEAD=0c972e1949191d62d84536f987a40f26dba57e03；工作树仅本批许可新增。Odoo20 core=f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb、tracked工作树干净。

永久只读源W5：ydental_s10_test_20261015073500_e50f4a71 / OID2100310 / cluster7694897083368259627。静态config SHA=867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7，marker SHA=1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa；父W4 OID2100301及父marker/config对应封存，152份filestore W manifest=bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283。P0-10 read-only-sql.json固定SHA=3bbc7130ed4fa3575a1f4ee8e5ca527781c366bbddcaf6de0eb3d8853e0f65ea，不能代替本批现场SQL核验。

冻结脚本 scripts/s10_p0_11_readonly.py SHA256=4d5d0d678ea7c02f48ec2812393779325785de15292180e1f27cd361d19220a6；docs/evidence/s10-p0-11/preflight.json SHA256=5ba443a2fe838f2cc8e1b12c4be562f679dfec71a0d367e90ed713c8c51c9cf6。许可新增仅 scripts/s10_p0_11_*.py、docs/s10-p0-11-*.md、docs/evidence/s10-p0-11/*；私密原件仅受限.local/s10-p0-11-6209310360/。没有修改旧源码/证据、addon、ACL、core或Issue/Project字段。

API逐字相等GET读回本评论并存ID/URL/字符数/UTF-8字节数/正文SHA、脚本SHA和预检SHA之前，历史SQL/CREATE/HTTP/Firefox/POST均0。读回后本阶段只准一次W5只读连接，首个查询前set_session(readonly=True,isolation_level=REPEATABLE READ)，所有SQL仅SELECT/SHOW，finally rollback/close；禁止锁/写/临时函数。冻结SQL：SHOW transaction_read_only/isolation；SELECT实际库名/OID/cluster/CURRENT_TIMESTAMP；SELECT本库其他连接；catalog列发现；逐public base table SELECT to_jsonb(t)::text、按id或全行文本排序。全行只在私密目录，公开各表行数/SHA与后续严格字段白名单。所有SQL字面值已列入preflight.json。

本阶段CREATE尚不放行。SQL必须匹配W5固定31稳定表、P0-10 W5全部封存表与RO1-R1资金投影、164附件指针/152实文件；invoice1 posted740/residual0，4费源600+80+40+20，既存500/240和partial1/2及审计、模块安装态/QWeb必须无漂移。随后离线从同一事务原始快照核doc1=patient1/store1/company1/pending/version2/responsible7，旧version1/2、真实非空完整TEXT_FIELDS+teeth及各hash、原/当前execution患者/门店、状态/lease、当前user7 active/company1/store1 active membership/employee、medical write、capability、资格、有效编辑器互斥、患者有效关系、本人内部账号及合法scope条件。任何不足立即BLOCKED_PREFLIGHT，CREATE0/浏览器0/业务POST0，不补权限、排期、工位、原文或业务。

只有全门禁成立，才准备唯一新克隆和Web脚本；新增执行脚本、精确逐表/逐事件白名单及可CREATE结论将冻结在补充checkpoint并再次API逐字读回，绝不暗变本冻结只读脚本。原生端点本人user7 /web/login POST最多1、必要时store1合法switch最多1、/ydental/clinical?document_id=1 GET最多2、/ydental/clinical/action POST依次acquire/confirm/release各1。只用同一真实Firefox原生会话/同源Origin/cookie和DOM原生CSRF、有效scope revision、固定32—128字母数字connection、新唯一action key、expected_version=2和既存完整内容原样。三POST逐步成功且响应/审计/只读SQL核副作用才继续，任何失败/未知/并行编辑即停，不重试、不换key、不自动重发。

总最高预算CREATE1、Odoo HTTP1、Firefox1、本人登录POST1、必要合法切店POST<=1、临床GET<=2、临床action POST=3、heartbeat0；资金/库存/其他业务POST/PDF/原版重印0、Odoo shell/upgrade/install/init/test/直接业务ORM/sudo0。静态资源与原生登录跳转GET只限必要登录/页面依赖，不能借跳转额外访问业务页。后续事务仅身份login/session/device/合法scope、clinical.view至多2、doc1编辑字段、pending2→confirmed3、新增kind=confirm version1、edit_acquire/confirm/edit_release各1及公共fence受控revision；若有旧编辑器元数据需先精确冻结editor_invalidated，不能宽放审计。费库款及PDF/来源指针全部逐行零变，W5所有表零变。无安全执行配额/租期则停，不增heartbeat。

本预检非技术PASS。S10整阶段技术/生产BLOCKED、T12 BLOCKED、W5 browser exit1/final_audit NOT_RUN、Native SIGSEGV历史UNKNOWN、W4 STOP均保留；#34 OPEN，#35 S11 NOT_STARTED。不重放退款14/13、日结9或W5收500/240，不转PDF备选、不启P0-12/S11、不合并部署。
