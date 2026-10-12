# S08-A db20维护及固定测试恢复

依据[#32专项维护授权6125823343](https://github.com/Yredxin/YDental/issues/32#issuecomment-6125823343)及[#23持续开发环境授权6125774169](https://github.com/Yredxin/YDental/issues/23#issuecomment-6125774169)，完整读取#23/#32当前正文及3/9条有效评论，沿用原分支和诊断起点f9a8ff237da89838bac839a277e290008d74d56c。短时开发服务重启已经用户授权，无需再次申请。本批只维护db20及恢复S08-A验证，不启动B/C，不改业务要求。

## 已完成维护

[维护开工核对6125893718](https://github.com/Yredxin/YDental/issues/32#issuecomment-6125893718)逐字读回后实施。2026-10-12 14:06:16—14:06:20 UTC，唯一实际配置变化为现有Compose service db20增加`shm_size: 256m`；使用授权原命令`docker compose -f /home/redxin/code/odoo/odoo-sd/postgresql/docker-compose.yaml up -d --no-deps --pull never --force-recreate db20`，退出0。没有其它参数调优，没有pull/down/-v/删库/删卷/清理共享文件。

原Compose SHA256 `3d0baa673b19f2582f8dc2c6d22e94a87743c224b9359e52d5a51b28f9f48cf2`→`acebac7adac4b2e677715a953ef43b26fef80be496be86064f5ca918f8cb884a`；原文件600权限副本留本机受控目录，不上传凭据。Compose config退出0，规范化配置除db20 shm外深比较完全相等。首次校验误把返回的字节字符串当整数导致AssertionError，尚未执行重建；修正校验类型后通过，失败[原样保留](evidence/s08a-maintenance/maintenance-validation-failure.json)。

原本地镜像ID `sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`、原volume `postgresql_odoo20-db-data` RW→`/var/lib/postgresql`、cluster `7694897083368259627`、127.0.0.1:5432均不变。维护前后106个既存数据库OID/名称清单完全相同，原清单本机保留，仓库仅指纹；odoo12-db全部已选身份（容器/镜像/PID/启动时间/卷/端口等）深比较相同。

|实际服务端指标|维护前|维护后|
|---|---|---|
|共享内存总量|67,108,864|268,435,456字节|
|已用/空闲|63,995,904 / 3,112,960|64,004,096 / 204,431,360字节|
|inode已用/总|11 / 950,272|11 / 950,272|
|数据卷空闲|27,452,612,608|27,498,430,464字节|
|宿主RAM available|5,296,623,616|5,324,681,216字节|
|容器memory.current|967,360,512|528,465,920字节|
|OOM/oom_kill|0 / 0|0 / 0|

[前快照](evidence/s08a-maintenance/environment-before.json)、[后快照](evidence/s08a-maintenance/environment-after.json)、[命令/退出码/单字段变更](evidence/s08a-maintenance/maintenance-action.json)、[健康与日志hash](evidence/s08a-maintenance/health-after.json)、[维护摘要](evidence/s08a-maintenance/maintenance-summary.json)。资源为实际采样值，不是生产容量承诺。

执行前两次检查其它客户端活动事务数0，3个idle连接。短时重建使整个5432开发端点连接断开；日志显示14:06:16正常shutdown、14:06:20 ready，未出现SIGSEGV。既有Odoo PID42433/8069未停止，`/web/health?db_server_status=1`实际返回200及db_server_status=true，确认其数据库连接可恢复。首次pg_isready未指定-U，服务已就绪但产生角色postgres不存在的FATAL；随后明确-U odoo -d postgres退出0，保留并归因这一诊断噪声，不将其误称数据库崩溃。

回退方案：原Compose受控副本、原镜像和持久卷均保留；如确需回退，只还原该字段并重建同一db20，仍需短时开发停机，不删数据、不重放已提交业务。当前不执行回退。共享内存当前容量约束已解除；增长机制和原32MiB allocator仍未知，扩容不代表泄漏已根治或生产稳定性通过。

## 固定版本与合规环境

本轮最终全部适用PASS仅来自**固定test `a7b023d26812fd4d722b2d185dd6571bb6d27611`**、全新隔离合成库`ydental_s08a_test_20261012141720_8e252c8e`（OID1145535、端口18167）。产品仍为`a28b364691791214becf4909e9ecf1bc0be3555c`，产品树字节完全相同。Odoo核心固定`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`且tracked diff为空。最终证据提交SHA由#32交付评论固定；test→final只含AGENTS/报告/脱敏证据，不含产品或验证脚本。

原固定test e8b2247的并发探针无法保留失败内层frame/双方结果，已有明确验证缺口；依据本次D项授权，仅修`scripts/s08a_probe.py`补取证并复现旧PID判据，不改模型/前端/业务断言。中间`7d600af6fcfdfa7169a7245a44b942cceddd2a68`在另一全新合成库aa1ddac6安装30/升级28/probe16完成，但自然调度未触发末次PID复用。为核实机制，固定a7b后另建上述新库，**全部闸门从安装起重新执行**，未把7d或历史rework成功拼入最终结果。[中间运行及用途](evidence/s08a-maintenance/intermediate-history.json)、[新库身份](evidence/s08a-maintenance/new-database-identity.json)。两个新库及历史失败库均保留。

继续使用原runner的端点/cluster/OID/创建marker/configSHA/dbfilter/data_dir/独立端口/PID/外发guard。未接管旧库，不改guard。临时子进程PGOPTIONS仍是关闭query/maintenance parallel与maintenance_work_mem=16384KiB；probe和三次audit实际SHOW均为0/0/16384，未改PG全局设置，未再调大其它参数。

## 本轮最终实测

所有下表PASS为Codex自测，不代表GPT独立复核或用户验收。[最终结果索引](evidence/s08a-maintenance/final-tests.json)、[每次命令/退出码/原日志SHA256](evidence/s08a-maintenance/run-history.json)、[28方法逐项执行与源码定位](evidence/s08a-maintenance/test-methods.json)、[S08-T01—T16逐项矩阵](evidence/s08a-maintenance/tc-matrix.json)。A适用10项PASS，B/C所属6项继续NOT_RUN。

|闸门|本轮固定a7b / 同一新库实际结果|
|---|---|
|全新安装|退出0、30项；21模型+7真实HTTP/RPC，额外2项为原生资产初始化，不称完整JS套件|
|普通升级|退出0、28项；21模型+7真实HTTP/RPC|
|持久业务升级|真实Firefox/并发提交数据后再升级；退出0、28项；全部10组行签名完全相同|
|独立PG连接竞争|8类×2轮=16/16；每组初始backend不同、barrier真实重叠；14次serialization retry；deadlock0|
|Firefox|退出0、88项、10个真实响应屏障、21图逐张实际目视核验、pageerror0；默认sandbox|
|实际中文导出|退出0；151/151、缺词0、错误Python/JS metadata0、错误码前缀保留|
|guard|5项、退出0；隔离/创建marker/端点/config/PID/外发限制保留|
|权限与安全|当前公司/门店/能力撤权、旧连接/令牌、readonly/none、RPC伪造、CSRF、附件/export、共享历史目的性负向均实际执行；静态审查16产品文件未见新问题|
|SQL与审计|8类SQL错误全0；查看/保存/确认/更正/移交/交还审计有区分并保留作者版本|
|文书经济不变性|浏览器全流程前后6组事件/批次/stock move/move line/quant/价格快照签名完全相同|

安装、两次升级实际执行的28个方法均由原始日志中Starting记录逐项核对，并校验日志SHA；不是仅依退出码推断测试数。真实上游库存receive/issue测试仅在回滚合成夹具中执行，不代表B真实治疗执行。持久表升级前有17份文书、38个历史版本、19个执行段及26个task，升级后行JSON签名全部相等；库存原生demo行保留，文书操作没有经济事件。[三段audit与签名对比](evidence/s08a-maintenance/signature-comparison.json)。

D1交还后保持待完善，独立补记不占原椅，责任移交拒绝有效编辑者；释放后合法移交保留原作者及贡献版本。D2由另一合法医生/工位实际接诊并建独立文书，D1确认不误确认D2；D2交还唯一后继后还验证了D3真实新接诊。S06同事务保存/交还/唯一续诊、失败原子回滚、hold restore/verify、编辑释放及当前权限规则均由本轮模型/HTTP/并发/浏览器核对，不改产品规则。

审查依据odoo-security技能逐项覆盖ACL、sudo、SQL、路由/CSRF、HTML转义、私有方法和不可公开写字段、文件/反序列化、动态属性、返回原始值、事务/锁、终态浏览器核对出口及本轮probe改动；[审查结论](evidence/s08a-maintenance/security-review.json)、[新扫描取证](evidence/s08a-maintenance/security-sweep.json)。这是本轮Codex自审，仍须GPT独立复核。

## 原第八组AssertionError的定位与机制复现

历史1bec运行在第八组`continuation / round2`退出；原catch只记录异常类型，内层堆栈和双方结果已被丢弃，**历史确切失败行仍UNKNOWN**。原日志/hash/库未改，不能补造遗失frame。原末次PID判据（1bec脚本79行）是候选，不以候选替代历史结论。

本轮新增双方完整轨迹、初始PID/barrier、每次操作/serialization/游标释放、最终结果、失败case预先入档及异常frame。最终a7b在**同一第八组真实业务竞争**中，用有界20秒事件控制已提交胜方与失败重试方游标归池的顺序；初始两个请求仍在不同backend真实重叠，仅竞争结束后固定LIFO池归还顺序，未串行化初始业务操作、未改Odoo核心/连接池、未减少16组或放宽业务不变量。

实际初始backend **2369 / 2381**：2381提交成功version1；2369遭遇serialization failure并归还连接，随后合法复用2381重试，被产品以`editor_expired`拒绝。末次PID相同并不否定初始双连接竞争。单独重新执行旧`final PID != final PID`判据，**真实复现AssertionError**并保留当前frame：a7b `s08a_probe.py:132 race`→`:34 legacy_final_pid_assertion`。同时初始PID不同、一个成功一个拒绝、文书版本1、执行已交还、编辑释放、唯一后继1均通过。[完整16组原记录](evidence/s08a/probe-attempts/ydental_s08a_test_20261012141720_8e252c8e-20261012T142149695799.json)、[第八组双方完整轨迹及旧判据frame](evidence/s08a-maintenance/probe-diagnosis-final.json)。

这证实了**旧探针末次PID断言会被合法连接池复用误触发**的验证缺陷机制；复演对象是旧判据，未声称完整旧脚本重放或恢复历史遗失堆栈。最终独立性依据使用初始backend+真实barrier，并保留原全部业务断言。旧错误判据的诊断失败与业务测试PASS分开记录，不将失败吞成成功。

## Firefox终态与普通自动保存证据

[本轮88项/屏障时间/服务器核对/21图原记录](evidence/s08a/browser-attempts/20261012T142346031387/result.json)、[逐张实际目视核验与hash](evidence/s08a-maintenance/visual-review.json)、[浏览器固定提交及命令退出码](evidence/s08a-maintenance/browser-command.json)。前11图覆盖原真实接诊/FDI/自动保存/D1D2/移交/作者/更正/只读/断线。以下全部是本轮新库的新截图：

|场景|本轮效果证据|
|---|---|
|普通请求期间继续输入并追赶到服务端|[12自动保存最新文本与36/O](evidence/s08a/browser-attempts/20261012T142346031387/12-ordinary-inflight-autosave-catchup.png)|
|confirm延迟，文本/52牙/牙面/状态/0及动作冻结|[13确认冻结](evidence/s08a/browser-attempts/20261012T142346031387/13-confirm-all-inputs-locked.png)|
|correct延迟，同一保护及物理输入尝试|[14更正冻结](evidence/s08a/browser-attempts/20261012T142346031387/14-correct-all-inputs-locked.png)|
|更正时强制DOM输入，A已提交、B留原页|[15更正核对出口](evidence/s08a/browser-attempts/20261012T142346031387/15-correct-forced-input-retained.png)|
|handover延迟，所有输入冻结|[16交还冻结](evidence/s08a/browser-attempts/20261012T142346031387/16-handover-all-inputs-locked.png)|
|确认时强制DOM输入，保留未同步并合法补记|[17确认未同步保留](evidence/s08a/browser-attempts/20261012T142346031387/17-confirm-forced-input-retained.png)|
|已交还后无事件直接修改DOM，不假装可撤销|[18交还已提交不可本页撤销](evidence/s08a/browser-attempts/20261012T142346031387/18-handover-committed-unsent-retained.png)|
|服务器已提交但响应丢失|[19保留原页并核对](evidence/s08a/browser-attempts/20261012T142346031387/19-response-lost-reconcile.png)|
|请求未送出|[20保留原页并核对](evidence/s08a/browser-attempts/20261012T142346031387/20-request-not-sent-reconcile.png)|
|409旧版本|[21冲突核对出口](evidence/s08a/browser-attempts/20261012T142346031387/21-stale-version-reconcile.png)|

实际Firefox拦住真实POST响应，在释放前尝试文本及牙位交互；正常成功后的服务端完整内容与本次提交范围相等。强制input事件和不发事件DOM修改分别验证generation及完整内容比较；异常原页保留、本地文字可复制、新同源标签显示真实服务器状态，不自动重试、撤销或绕过更正规则。10个屏障包括save、confirm/correct/handover、三个强制输入以及response-lost/request-not-sent/409；每个具体延迟秒数和是否实际送出/丢弃响应均在原JSON。强制DOM用例的屏障只有约40—47毫秒，但实际注入与断言均发生在受控释放前；正常物理操作屏障0.679—0.891秒，save1.298秒，不冒称所有屏障均长时间人工延迟。

## 失败保留、环境结论和保护核对

本轮并未删除或改写旧失败：原32MiB共享内存安装失败、原第八组AssertionError、原竞态复现/中间Firefox调试全部保留于[历史rework报告](s08a-rework-report.md)和[环境诊断](s08a-environment-diagnosis.md)。本轮另保留：维护前Compose整数/字符串校验失败；一次误在升级尚未退出时启动audit被runner锁安全拒绝退出2，未执行数据库工作；只读环境快照helper沿用维护前“其它活动事务必须0”断言，恰遇本轮export而退出1，未进行环境修改，export完成后安静快照重读通过。[顺序事件](evidence/s08a-maintenance/verification-sequencing-events.json)。这些失败不删、不替换；最终audit/资源采样和所有适用测试各自有实际成功记录。

终场106个原库OID/名称仍全部保留，新增恰为本轮两个隔离库；总108。db20自本轮维护后未再重启，原卷/cluster/镜像/端口保留，odoo12身份不变。终场共享内存268,435,456总、64,004,096用、204,431,360余字节；数据卷余27,259,613,184字节，主机available5,405,097,984字节，容器memory.current409,022,464、OOM0。既有Odoo42433仍200/db_server_status=true。[终场资源](evidence/s08a-maintenance/environment-final.json)、[身份/健康/新运行全部日志hash](evidence/s08a-maintenance/final-preservation-health.json)。本轮新测试日志及维护后PG日志未见SIGSEGV/signal11/PANIC/OOM/DSM分配失败；不据此认定历史崩溃或共享内存增长根因已解决。

本轮专用预览只在核对精确PID1223854/config后SIGTERM，退出0；未停止其它Odoo客户端或odoo-12。原始配置/日志/凭据留本机受控目录，仓库仅合成截图、脱敏结果、原始hash。维护前旧PG容器的完整Docker日志未重新全量归档；既有诊断窗口和原Odoo失败日志/hash仍保留，不声称拥有完整旧容器日志。

[GitHub开工完整读取](evidence/s08a-maintenance/github-authorization-read.json)及[交付前再读](evidence/s08a-maintenance/github-before-delivery.json)：#23/#32正文及原评论完全未变，仅本轮开工/维护回执新增，逐字读回证据附上。[Project保护](evidence/s08a-maintenance/project-preservation.json)：21字段/15条目/6视图/7公开workflow全部分页读完，三次快照深比较无差异，mutation0；#32仍S08/进行中/Todo/OPEN，#31待用户验收，后续待启用。

## 复核入口与未做范围

复核可从final-tests→逐项TC/方法/运行日志hash→真实probe/audit/browser原JSON→21截图逐层核查。复跑必须用新的guard合成库，固定a7b源码与当前原核心，先install→upgrade→probe→preview→audit；serve期间运行Firefox，精确停止预览后audit→带业务upgrade→audit→export/translation。库存与费用不变只指A纯文书操作和原价格快照，不代表S10真实费用单；audit基线在preview夹具创建后、浏览器前，升级基线在全部浏览器提交后。

[原文书/牙位字典](s08a-data-dictionary.md)、[动作状态/权限契约](s08a-contracts.md)、[终态保护契约](s08a-rework-contracts.md)均不变。临床字段仍草稿，确认文字不等于实际治疗或正式签发。B真实治疗/药房/4+2及费用库存联动、正式转诊、C PDF打印、S09—S13、50会话性能/生产配置/部署均NOT_RUN；未合并/强推/关闭Issue。历史S07 SIGSEGV根因UNKNOWN，正式生产部署继续BLOCKED。完成#32交付申请逐字读回后停止等待GPT独立技术复核。
