# S07 安全自审

审查范围：本阶段 `ydental_inventory`、受隔离guard保护的 `ydental_inventory_test` 及 `scripts/s07*`；固定版本见 [报告](s07-report.md)。采用 odoo-guidelines、odoo-security；本批没有 static/ JavaScript。此为 Codex 自审及自测，不代表 GPT 独立复核、用户验收或生产安全认证。

## 权限和 sudo

`ydental.inventory.service._access` 先验证 S01 server-bound session、revision、当前门店、实时员工/membership及业务等级；所有普通库存动作要求 warehouse-write。集团主数据只检查集团管理授权和有效当前门店/允许公司，不能从该权限推导库存读取或 price-write。临床私有hook另检查 medical/pharmacy，不要求通用stock管理组。

`_native()` 的 sudo 仅用于固定模型名及经过服务端校验的对象，带 Python `object()` 身份token；客户端JSON/context不能构造此token。`_model()` 只接收代码固定的config/batch/event/operation后缀；对象读取必须 `_get` 当前店或 `_lot` 当前batch+法人验证。批次/产品/单位ID先验证正整数、存在、类别、法人及配置，库位由服务器类别映射，不接受客户端company/location/domain/model。同法人调拨再次验证目标店 warehouse-write。

受管native warehouse/location/lot/move/move.line/quant有 create/write/unlink guard、访问domain、`check_access` 和 `fetch` 检查；YDental用户即使同时有stock manager也不能直通原生库存。受管product的原生读取封闭，防止qty_available等计算字段越店；主数据/工作台只返回必要投影。非YDental原生用户对受管对象的普通修改同样受关联库位/产品和token检查。单位及祖先换算在已被受管产品引用后拒绝普通变更，包括原生系统管理员直接写存储factor/parent_path。没有新增管理员抢占或远程强制释放。

source模型继承S01读取/导出契约，法人使用无group的restriction、门店使用动态domain；普通CRUD/import/unlink均封闭。所有历史不可普通删除。S01 export-write与原对象读取同时成立才允许导出，不通过隐藏按钮代替服务端检查。

## RPC、HTTP 和信息最小化

业务服务全部私有方法，RPC不能调用 `_operate/_source_action/_authorize_source`；公有CRUD和native方法仍在ORM层检查。DataSet继承链移除客户端ydental_binding，再用服务器登录session绑定；沿用S04患者及S05/S06边界，不修改既有内核。

库存POST为auth=user、默认CSRF；action体最大32768字节；操作白名单+固定参数签名，整数/有限数量/单位换算/短文本/显式bool均验证。GET只读工作台并审计。错误页使用QWeb转义`t-out`，无Markup、safe_eval、动态getattr/setattr、pickle、用户模板或用户SQL。持久事件/审计与native移动同事务savepoint；HTTP业务拒绝403/409，网络失败不报告成功。扫码POST仍需可信session与warehouse-read，只返回unsupported_source/received=false。

工作台不返回patient_id、完整病历、文书、签名、附件或任意来源记录。必要summary由可信来源hook生成；本批只含显著合成摘要。inventory源及原生lot/move/quant附件加入S04 blocked-source清单，public标志也不能绕过。每个角色通过真实HTTP/RPC验证只读、无权、stock manager旁路、跨店、旧revision、实时撤权、患者读取和原生导出拒绝；模型还验证public附件拒绝。

## 并发、SQL 和审计

仅固定 advisory lock(31007) 和参数化mutex UPDATE原生SQL，无用户拼接。mutex更新迫使REPEATABLE READ竞争者重试新快照；每次锁后重新核权。source和request两组数据库unique约束同时保证来源/请求幂等。补货/退回/核验/调拨/盘点/recover受同一fence控制，最后一份、累计退回/核验、缺料恢复均用两个不同PostgreSQL backend实测。业务无commit，无删除已完成原生流水。探针仅在明确新库自有cursor提交合成夹具，受进程guard限制。

真实 `_action_done` 完成后注入异常验证quant/move/event/audit全回滚。最终只读SQL检查负数、重复来源、半事件、event与move数量去向不符、movement审计数量不符、quant与已完成move.line不守恒、quant归属不符均为0。盘点相符只留observed事件，不能走pending执行恢复；HTTP及模型都验证拒绝。

临床产品hook默认AccessError。测试适配器要求精确frozen Python类型、当前actor/store、S07新库模式与专属进程目录；客户字典、context开关、错误actor不能激活。价格来自原合成快照或真实S05不可变演示snapshot；真实S05调价后恢复仍保持原版本/金额，不调用新取价。S08/S10并未安装，费用引用不是实际收费凭证。

## 运行隔离和残余边界

runner每次验证端点、cluster、创建记录/OID、config哈希、精确dbfilter、独立data_dir和日志、核心SHA、干净产品/测试文件、专属端口和flock；serve PID必须与专属config匹配。没有drop/adopt/reset历史库操作。运行进程网络guard仅允许本机5432及本次HTTP端口，阻止外部解析和其他loopback服务。Firefox限本次origin，不关闭浏览器安全sandbox。所有凭据/config/access文件只在.local且0600，不入GitHub；日志仅发布脱敏摘要及hash，不发布原始日志。

剩余未验证项如实列在报告：真实S08临床/发药、S09、S10费库款、S11加工来源、生产阈值、50会话性能/锁粒度及生产部署均NOT_RUN。单一库存fence以正确性为先，不能据此声称并发吞吐达标。其他未启用模块的任意新入口未来仍须回归；本自审不是对未来代码的保证。
