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

## 固定测试恢复

维护后安全身份核查通过，下一步以产品a28b364691791214becf4909e9ecf1bc0be3555c不变、最小必要验证取证修正后的固定test，在全新guard合成库完成全部适用闸门。最终实测、失败链、固定SHA及截图将补充本报告，不沿用旧版PASS。当前维护结果不代表S08-A技术PASS。

Project不改、#32继续S08/进行中/Todo/OPEN。S08-B/C、S09—S13、合并与生产均未执行；历史S07 SIGSEGV根因未知、生产BLOCKED继续。
