# S08-A 环境阻断诊断与授权申请

**结论：BLOCKED，不申请技术PASS。** 已确认实际 PostgreSQL 容器的 POSIX 共享内存上限为64 MiB，当前可用仅3,112,960字节，无法满足历史日志中的32 MiB分配。宿主磁盘、宿主共享内存和inode均不是本次已观察到的容量瓶颈。没有验证出不修改既有服务的无特权会话恢复办法；本轮没有创建数据库或重试安装。

唯一边界为[#32 GPT-REVIEW6125132411](https://github.com/Yredxin/YDental/issues/32#issuecomment-6125132411)。完整读取#23/#32当前正文及全部2/6条有效评论；[读取指纹](evidence/s08a-environment/github-read.json)。以下均为Codex只读自查，不是GPT亲测或用户验收。

|固定节点|SHA|
|---|---|
|诊断起点/此前交付|`e1f0c98bd74caf414377e44cd10b182fba0a899c`|
|product，保持不变|`a28b364691791214becf4909e9ecf1bc0be3555c`|
|test，保持不变，最终全量尚未通过|`e8b2247609e51d7fbe268b94082e8fd3259db9d3`|
|Odoo20核心，tracked diff为空|`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`|
|分支|`codex/s08-a-clinical-doc-r1-20261012`|

本次只新增诊断文档/脱敏证据并更新执行入口；新的诊断提交完整SHA固定于#32本次评论。没有产品或验证脚本改动，不另立已通过的test。

## 服务端实况与容量证据

诊断窗口2026-10-12 13:25—13:34 UTC。端点`127.0.0.1:5432`实际映射至Docker `odoo20-db`，服务器地址`172.18.0.2:5432`，cluster `7694897083368259627`。服务端PostgreSQL18.6，宿主master PID27070、容器PID1，启动时间`2026-10-10T04:52:29.066705Z`，未发生本轮重启。

宿主namespace为mount `4026531832`、IPC `4026531839`；服务器及同UID诊断进程为mount `4026532352`、IPC `4026532354`。直接从宿主读取服务器namespace句柄退出1，保留这一限制；使用现有Docker访问权、明确`--user 999:999`，从与postgres相同UID的容器进程读取成功。没有sudo、nsenter、root exec或权限提升。

|服务端来源|实际值及判断|
|---|---|
|Docker HostConfig|ShmSize=67,108,864；IpcMode=private；mountinfo `/dev/shm` tmpfs size=65536k|
|容器`df -B1 /dev/shm`|总67,108,864；已用63,995,904；可用3,112,960字节；96%|
|容器`df -i /dev/shm`|950,272 inode；已用11；可用950,261，inode充足|
|容器数据卷`df -B1 /var/lib/postgresql`|可用27,454,361,600字节，使用57%，不是物理磁盘满|
|宿主`/dev/shm`|约3.7 GiB空闲，属于不同mount，不能代表容器|
|内存/进程限额|Docker Memory=0，cgroup memory.max=max；当前约965MB；OOM/oom_kill均0；pids.max6219/current14|
|宿主内存|约5.3GB available；没有发现本轮OOM证据|
|共享内存文件|10个PostgreSQL文件、尺寸约1—16MiB；全部仍映射于存活的容器PID34，部分同时映射其他服务器进程|

[逐命令argv/时间/退出码/输出](evidence/s08a-environment/readonly-commands.json)共16条：15条退出0，宿主直接namespace读取退出1；[结论结构化数据](evidence/s08a-environment/environment-conclusion.json)、[Docker管理身份](evidence/s08a-environment/container-managed-identity.json)。文件仍被服务端使用，不能当作异常残留删除。SysV shmmax/shmall巨大不改变POSIX tmpfs容量限制；`pg_shmem_allocations`只反映主共享内存，不能据此排除DSM占用。

SQL只读连接显示3个idle client和本次1个active诊断client，后台为launcher/checkpointer/background writer/walwriter/io worker等；快照没有parallel worker、autovacuum worker或S08-A连接。宿主精确argv扫描只有既有Odoo PID42433，没有本轮S08-A runner/probe/browser/audit或预览；未终止任何进程。[只读会话结果](evidence/s08a-environment/sql-read.json)、[精确进程扫描](evidence/s08a-environment/processes-exact.json)。现存102个ydental库全部保留。以上是快照，不能证明过去每时刻都无资源竞争。

## PGOPTIONS生效程度及根因边界

使用现有venv/libpq，三个顺序小连接均显式只读，依次读取无PGOPTIONS、原runner相同PGOPTIONS、关闭后再次无PGOPTIONS的实际`pg_settings`：

|配置|基线默认|原profile实测|连接关闭后的新基线|
|---|---|---|---|
|maintenance_work_mem|65536kB/default|16384kB/client/user|65536kB/default|
|max_parallel_maintenance_workers|2/default|0/client/user|2/default|
|max_parallel_workers_per_gather|2/default|0/client/user|2/default|

[完整三连接证据](evidence/s08a-environment/pgoptions-check.json)。证明该profile**现在**有效且非持久化；过去失败后端已退出、当时没有SHOW记录，其实际设置仍为UNKNOWN，不能追认过去已验证。

这些参数限制查询并行和维护内存，不扩大`/dev/shm`，不限制全部服务端共享分配。实际`dynamic_shared_memory_type=posix`；`dynamic_shared_memory_type`及`min_dynamic_shared_memory`均为postmaster级。`track_counts`为superuser上下文，未尝试关闭或用特权参数规避。[PostgreSQL18资源参数文档](https://www.postgresql.org/docs/18/runtime-config-resource.html)。

历史服务器日志独立确认12:54:17 backend265687、12:59:23 backend266585的32 MiB ENOSPC；12:59:14 backend266568还有两条相同FATAL，此连接来源未确认。FATAL并非SIGSEGV证据。[脱敏错误及原日志hash](evidence/s08a-environment/server-log-summary.json)，原日志SHA256 `c95106e380ff55a02b952c8cf86f0bfe168be00b4247df3005c76e3b718e8071`，仅本机受控保留。

已确认的是实际命名空间容量约束及与历史错误一致的分配失败条件。**过去每次失败瞬间的精确余量、32 MiB由哪个分配子系统请求、累计文件是否由共享统计DSA增长或泄漏导致，均未确认。** PG18.6源码显示共享统计DSA可扩展，与查询parallel worker不是同一限制；这只是可能机制，不能作为本次运行栈证明：[对应版本pgstat_shmem.c](https://raw.githubusercontent.com/postgres/postgres/REL_18_6/src/backend/utils/activity/pgstat_shmem.c)。未通过清理、删库或重启来验证猜测。

## 原并发AssertionError：可定位范围与缺失证据

失败库`ydental_s08a_test_20261012124648_038d989e`，OID1103407，commit `1bec52a970f497a1c01d5be98f1e4919bcd907d1`；原probe退出1。原[七组完整成功轨迹](evidence/s08a/probe-attempts/ydental_s08a_test_20261012124648_038d989e-20261012T124939174051.json)依次为versions×2、editors×2、handover_save×2、continuation×1。按原循环，第八组是continuation第2轮。

旧source的裸断言候选为line79末次backend PID不同、line90后继≤1、line91版本条数一致、line93续诊后继/交还/编辑释放；line80有详细错误消息，与原空detail不符。原catch line103仅保存type/detail，未保留内层traceback；外层line108只报告总体失败。因此**不能恢复准确触发行或第八组双方完整竞争轨迹**。

原日志SHA256 `32e2e8d6d250ae3b7d08402d1b0273c3e73dc7bc2a228ec5c1e8ca0b4d758d37`。服务器记录backend264980八次SerializationFailure，最后12:49:39.142，与失败时间相邻；只能证明重试发生，不能证明最终PID断言必然失败。[原source指纹/候选位置/时间序列](evidence/s08a-environment/probe-failure-trace.json)。

对旧库仅用受端点/cluster/OID校验的SQL只读事务读取doc57—64，不加载Odoo registry、不重跑夹具、不写历史库。doc64/execution68目前version1/version_count1、handover、编辑空、唯一后继1，满足续诊最终不变量；这是最终持久状态快照，不能证明原断言时刻的状态。[只读行证据](evidence/s08a-environment/probe-readonly-diagnosis.json)。

“序列化重试后连接池复用胜方backend，导致末次PID误判”仍是候选解释。固定e8b2247已有初始PID+真实barrier、重试PID轨迹及异常frame记录，但没有最终16组通过证据，且失败前双方outcomes仍需在必要时补齐。资源恢复后须保留原16组和原不变量，用完整失败轨迹定位、初始真实不同backend并发重验，不能降断言、删组或顺序执行冒充竞争。本次没有修改测试脚本或宣布根因修复。

## 申请单独授权的最小调整（尚未执行）

现有无特权会话配置不能提供需要的空间；调整既有容器容量会影响同端点其他数据库，超出当前只读授权。依据最新GPT-REVIEW第5.2条及本次用户“具有副作用的环境调整必须报告并停止”的明确要求，**申请单独授权：仅给既有Compose `db20`增加`shm_size: 256m`，在维护窗口使用原有本地镜像重建`odoo20-db`，保留数据卷及全部数据库。**

实际Compose路径`/home/redxin/code/odoo/odoo-sd/postgresql/docker-compose.yaml`；db20当前没有shm_size，使用Docker默认64MiB。[仅供审批的单字段diff](evidence/s08a-environment/proposed-adjustment.diff)、[原文件SHA及未应用证明](evidence/s08a-environment/compose-proposal.json)。没有修改该文件。

拟执行命令，**待另行授权，当前未执行**：

```sh
docker compose -f /home/redxin/code/odoo/odoo-sd/postgresql/docker-compose.yaml up -d --no-deps --pull never --force-recreate db20
```

执行前须再次核对本地镜像仍为`sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`及数据卷`postgresql_odoo20-db-data`仍挂载`/var/lib/postgresql`，确认维护窗口。只修改db20容量，保持现有image/volume/端口/PG配置；不pull、不down/-v、不删库、不改db12/MySQL/Odoo服务、系统配置或依赖。若身份变化即停止，不扩大变更。

影响与风险：重建会重启该PostgreSQL集群，断开5432上的**全部**客户端，不仅S08-A；可能中断既有业务和未提交事务，必须另行同意维护窗口。256MiB只是建议的tmpfs上限，不预分配全部内存，但后续实际增长会增加宿主内存压力；不是正式生产容量批准，也不保证消除未知增长原因。无卷删除计划；容量回退也会再次重启，不能当成无代价自动回滚。重建后应先只读验证cluster/OID/卷及256MiB实际容量、余量，再按原guard进行一次全新S08-A合成库完整回归，失败即停止留证。当前不执行该方案，也不继续创建候选库。

## 当前验证状态与保护

[本次逐项状态](evidence/s08a-environment/current-results.json)：本轮新库0、安装尝试0、服务变更0。只读命名空间/容量诊断完成，三连接PGOPTIONS核验通过；这些不是产品回归PASS。

|必须完成的固定test验证|本轮结果|
|---|---|
|全新安装、升级，21模型+7HTTP/RPC|NOT_RUN / 环境BLOCKED|
|16组真实双连接及原失败场景|NOT_RUN / 环境BLOCKED|
|Firefox终态延迟、普通自动保存、D1/D2流程|NOT_RUN / 环境BLOCKED|
|实际中文151/metadata、guard5、权限/附件/导出负向、安全运行时|NOT_RUN / 环境BLOCKED|
|8类SQL审计、带业务升级10组签名、经济6组签名|NOT_RUN / 环境BLOCKED|

不沿用任何此前版本PASS冒充本轮最终回归，不把诊断读旧库当成并发或审计验收。全部历史失败库、原始日志、代码及截图保留；仓库只新增脱敏诊断及hash，不上传配置密码、原始SQL日志或患者数据。

Project零mutation，完整两次读取21字段/15条目/6视图及其字段/7公开workflow，与此前交付深比较一致；[保存证明](evidence/s08a-environment/project-preservation.json)。#32保持S08/进行中/Todo/OPEN，#31待用户验收、后续待启用。未改历史库、Odoo核心、odoo-12、既有服务、系统依赖或workflows。

S08-B/C、S09—S13、合并、生产部署均未执行。S07历史SIGSEGV根因仍未知，生产部署BLOCKED继续。发布`[CODEX] S08-A环境阻断诊断与授权申请`逐字读回后停止，等待用户对上述最小调整单独授权及GPT独立复核。
