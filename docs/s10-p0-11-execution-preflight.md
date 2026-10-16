[CODEX] S10-P0-11 正式预检补充／W5现场资格通过与唯一克隆Web脚本冻结

承接唯一授权6209310360及预检6209454407（API逐字已读回）。原HEAD 0c972e1949191d62d84536f987a40f26dba57e03、core f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb及原分支不变。本补充不扩大授权；以下机器checkpoint/脚本冻结API逐字读回之后，才允许一次CREATE及原授权Web路径。

已在2026-10-16T06:22:53.312733+00:00对W5/OID2100310/cluster7694897083368259627执行一只读连接，READ ONLY / REPEATABLE READ、rollback/close均真：643张公共表全行签名建立，P0-10全部47封存表及31稳定表匹配；152filestore/164指针/manifest匹配；原生posted740/residual0及500/240/partial1/2保全。25项资格/文书/安装态门禁成立：doc1 patient1/store1/company1 pending2/responsible7，旧version1/2非空完整内容hash同为678e527db07b38518de9522b056d45c9a4f5f5da775d07e112c5360f0ced21aa；execution原/当前1 handover，旧lease1 inactive、station9能力1；user7 active/company1/member5/employee3 active/medical write/active caps1,2,3,4，snapshot qualification空且catalog一致；无有效或残留doc editor，无本人serving/verify；原patient-store关系、内部账号/group均匹配。安装92模块元数据hash封存匹配，clinical view1582 en_US结构与现行源码完全匹配且zh_CN完整。

如实保留离线校验器首版失败：错误额外假设source.id==fee.id；实际同一冻结快照外键1→4、2→3、3→2、4→1及金额/原生line完全合法。首版脚本与输出保存eligibility-initial-script.py、eligibility-initial.json和eligibility.json；只离线按真实外键关系纠错，未重连SQL/改历史/放宽授权。corrected资格25/25通过；16项离线正反门禁检查通过，SQL/HTTP/Firefox/真实或模拟业务POST均未用于该离线检查。

唯一目标新库 ydental_s10_test_20261016_p011_a730c9e4，HTTP127.0.0.1:18311；原W5永久只读；CREATE前再次只读比全643表、查目标名/连接及静态seal，冲突立即STOP。独立filestore复制152文件并SHA全等。maintenance postgres连接仅单次CREATE DATABASE新库WITH TEMPLATE W5，autocommit/IDLE；不修改源、不重试、不新建第二库。克隆全643表与源完全同签名才启动一次Odoo HTTP，workers0/max_cron_threads0，无CLI业务/shell/upgrade/install/init/test。Odoo和Firefox仅使用既有私有依赖及进程内网络guard，不调整OS/PG/Docker/网络安全配置。

完整冻结机器计划 docs/evidence/s10-p0-11/execution-preflight.json SHA256=73e0b1094877960bfac783547decfe2972c237348db9c44316139d11eaf9f6ec；其中逐SQL、所有脚本SHA、静态来源SHA、HTTP/Firefox真实argv、白名单和预算完整记录。脚本SHA：
- scripts/s10_p0_11_browser.py: 088dbc063eec16f6c22192975e4232c350d0862e368ccc0bb9ee4a037374ae67
- scripts/s10_p0_11_control.py: 1f8b62d4de5a6264f5060e9d945ecaf497f1b7ace1a2406cd9d4cf62eae796ec
- scripts/s10_p0_11_eligibility.py: 919a57a4ecb5c3f149d21639468ad658750e5c731184ebfe38ba8b2b84fd366b
- scripts/s10_p0_11_offline.py: 7036c0144b26f025fc2d3a279410363421a454725f56a4301c7add200bd2e911
- scripts/s10_p0_11_readonly.py: 4d5d0d678ea7c02f48ec2812393779325785de15292180e1f27cd361d19220a6

本人user7复用既有合成医生凭据（离线只验现有hash，不公开、不修改），原生Firefox一个context，登录redirect直接/ydental/clinical?document_id=1，所以身份页额外GET0，原生登录POST1、自动scope店1/revision1，显式switch0（若默认不符即STOP）。只允许已存在5项web.assets、临床原生JS/CSS及正常web.login/website.translations必要GET；临床GET1初始、GET2原生confirm完成自动返回，至多2。CSRF、Origin/cookie、本人scope、固定原生生成32—128字母数字connection、expected_version2和完整原文在真实路由放行前严格核。只点击既有Open与Confirm按钮；原生Confirm自己触发release，绝不再点击release重发。每个响应原样校验/保私密HTTP，下一真实POST转发前核前一步全643表、副作用及截图。任何失败/未知/403/409/真实浏览器错误、额外POST或heartbeat均停止，不重试或换key。

逐表最大白名单已冻结：本人login/session/device各新增1；本人res_users7/partner8/employee3/hr_version3/resource3仅write元数据（hr_version另last_modified），timezone不变；S01新增最多8且逐事件仅login1/login.scope1/store.switch1/clinical.view2/edit_acquire1/confirm1/edit_release1，目标/source/category/before-after强绑定，无editor_invalidated。doc1仅editor字段/write元数据、state/version/saved_at，完整内容原样；只新增confirm version3/author7/previous2/new key，旧version1/2逐行不变；patient/supply/intake/queue四公共mutex各每action revision+1、总+3且其他字段不变；仅原生orm_signaling_default最多3条id/date append并保旧行。其他所有表，包括附件/filestore/mail、event/fee/price/snapshot/source/account/payment/partial/refund/close/stock/inventory，逐行零变；不宽放“审计可变”。

源heartbeat2秒/timeout600秒不改。acquire响应后立刻原生Confirm；原生saving=true期间在Confirm/自动Release路由之前做全表门禁，无产品JS修改/计时器屏蔽，heartbeat0。若任何heartbeat出现，转发前硬停并报告；不得扩大配额。真实Firefox引擎PID/退出码由Playwright原始launch/exit日志保留，Odoo精确自有Popen PID正常停止并保exit；原始医疗原文、截图、HTTP/cookie/connection/editor/key全部只在700私有目录，GitHub只ID/状态/金额/哈希及白名单结果。

最高CREATE1/HTTP1/Firefox1/loginPOST1/显式switch0/clinicalGET2/clinicalPOST3(acquire-confirm-release)/heartbeat0，其他业务POST/PDF/款物写/CLI业务/sudo0。不重放退款14/13、close9、W5收500/240；原版PDF备选不授权。S10整阶段技术/生产与T12持续BLOCKED，W5旧browser exit1/final_audit NOT_RUN、W4 STOP、Native SIGSEGV UNKNOWN保留，#34 OPEN/#35 S11 NOT_STARTED；正常提交推送后交付API逐字读回立即STOP，不启下一批。
