# S10-UI1-R1：CREATE 后测试控制器异常，Web 恢复 BLOCKED

**本批结论：BLOCKED。** R1 离线夹具合同通过，但唯一新库 CREATE 后控制脚本自身抛出 Python `TypeError`。按[#34 R1授权](https://github.com/Yredxin/YDental/issues/34#issuecomment-6182095943)及本批[强制预检](https://github.com/Yredxin/YDental/issues/34#issuecomment-6182178103)的命令异常 STOP 条件，未修脚本后继续运行。Odoo/Firefox 进程0，业务 COMMIT0，产品文件0改。UI1 的真实 HTML→JSON 疑点仍 `NOT_RUN`，不是 `NOT_REPRODUCED`。

## 先行核验与三项离线修正

- API GET #23/#29/#31/#34 当前正文与全部3/7/8/113条评论、#35 OPEN/0；R1 是最新授权，未见同批并行交付。原分支 local/remote 起点 `759ee62cec0b7e7563abc2ec3fbeb8c0264395f7`、工作树干净；core、历史S10 product/test、S10服务blob和S07服务SHA均匹配授权。
- 上批`s10_ui1_{control,prepare,browser}.py`及失败库OID2100227、私有marker/log原样保留。新增R1脚本副本：marker生成器从实际core HEAD和新库真实OID生成完整字段；控制器/准备shell完整校验，准备shell在业务动作前显式执行固定适配器保护；CLI以`serve-before/serve-after`与预检一致；浏览器baseline先按实际Content-Type/Location/页面分类，只有JSON类才解码JSON。
- 无Odoo/无数据库的离线合同测试 exit0、**34项 `SIMULATED_PASS`**。它执行实际marker生成器及未改`ydental_settlement_test.pre_init_hook`的AST：完整marker通过，缺/错core、错database/OID/cluster/config hash、落盘config变化均被原适配器和控制器拒绝；auth/脚本哈希错误拒绝；实际CLI入口及JSON/HTML/303分类检查通过。5份R1脚本编译通过，仅标SIMULATED。预检评论6182178103在新CREATE/Odoo/Firefox/产品修改前发布，API逐字读回一致，SHA256 `0d628aa8e4173025b7014f735ee410e5b4a0685a6af4d8f1e47af26303938759`。

## 实际 CREATE、根因与保全

`scripts/s10_ui1_r1_control.py create`仅调用一次，**数据库实际已创建**：`ydental_s10_test_20261015012000_b43e9a71` / OID2100239 / 原cluster `7694897083368259627`，独立私有目录、配置、124个复制并核对哈希的模板filestore、marker已落盘。但命令 exit1，最终没有执行随后串接的 `verify-target` CLI，也没有启动 Odoo。

可精确定位的测试控制器缺陷：`create()` 的filestore复制循环在第131行把局部变量命名为`target`，第161行又调用同名`target()`函数；Python局部变量遮蔽函数，抛 `TypeError: 'PosixPath' object is not callable`。先前34项离线合同测试覆盖了生成器与固定适配器，但没有模拟`create()`整个有副作用控制流，故没有捕获此错误。**这不是S10产品或固定适配器失败。**

STOP后仅独立只读取证：真实OID2100239与落盘marker的database/oid/cluster/core及config SHA一致；新marker完整字段校验PASS，未改固定适配器AST判据PASS。这个读回是事故后的只读核对，**不冒充未执行的`verify-target`命令或真实Odoo运行**。新库 store/patient/fee、settlement payment/refund/close/receipt、account.move/account.payment、S01 audit、mail.mail 均0；模块92、附件70、`bus.bus=6`与`mail.message=851`均同纯模板，没有其它新库活动连接。历史事故2056451、模板2100080、C1 2100125/2100126/2100176、FC1 2100197、FC2 2100212、上批失败2100227仍存在。原失败库和所有旧filestore/marker/log/core/volume/备份及本批新库保留，不清理重建。

## 真实验收状态与用量

|项目|本批实耗/状态|
|---|---|
|新库 CREATE|1/1；OID2100239；命令随后exit1|
|Odoo顺序进程|0/4，NOT_RUN|
|Firefox/Playwright|0/1，NOT_RUN|
|业务 COMMIT|0/12，NOT_RUN|
|新库模块升级|0/1，NOT_RUN|
|原版 HTML 普通表单点击与JSON导航判定|NOT_RUN|
|修后出账/部分收款/申请审批实退/日结解锁|NOT_RUN；产品0改|
|JSON兼容、权限、CSRF/revision、跨店、幂等|NOT_RUN|
|大于50条HTTP分页|NOT_RUN|
|bill/receipt/refund PDF下载、中文视觉与无权直链|NOT_RUN|

没有本批原生 posted 凭证、资金或S01业务审计增量；旧FC2的有限PASS不能替代UI1 Web验收。没有真实新SIGSEGV，旧Native根因仍UNKNOWN。S10全阶段技术与生产继续BLOCKED，S11未启动。下一步需GPT独立裁定是否再给一个单批预算；本批不改脚本后重试，不叠加剩余配额。不使用sudo，不开展基础设施安全专项，不改Project/Issue状态、不合并/生产部署。

本提交保留**实际失败时的R1脚本字节**供审查，并附[脱敏机器证据](evidence/s10-ui1-r1-blocked/verification.json)。脚本不可在本批重复执行；后续若获授权，需先消除`target`遮蔽并增加覆盖`create`尾部调用的离线控制流测试，再分配新的唯一库及预算。
