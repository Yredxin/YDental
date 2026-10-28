# R2-W3 药房负例与幂等

状态：**PARTIAL**。取得新合成处方的服务端无权、同 key 重放、库存不足竞争、超额及退药隔离证据；已完成事件的浏览器重复点击 NOT_RUN，独立末尾保护和最终账号／服务收尾待实际结果。W3 由新 A/B/C 分工，均在同一主机，不冒 OS 隔离。产品源码实际运行 `d0b79a9edfeb725a5a7706ef3f60232be725288c`，产品文件与 R1 候选 `dca4e1d2821b20df7b4b940d28d461270c310225` 一致。历史目标无模块升级。

## 新合成前置

初始 B 独立只读核旧账号停用、旧时段暂停、处置待处理及无 active lease，SHA `879b5d2f4f4aad0575af3cb96bac152315223f8d7143b51d1d9a9f28ffbdd66d`；为抽查而非全库保护。新药房 UID1559 正常表单登录，会员2546／员工1514及唯一 pharmacy/write 由 B 核；真实 capability562 已赋予。其对 stock.lot/move/picking/quant 的 read/create/write/unlink 在 Odoo MODEL ACL 检查均 false，SHA `82985b211e0c90fd8219c4d91b3f8f85ab54c04d8db1b841f1189b110a933d5f`；非 HTTP 权限负例。

新 SKU1141／lot283 真实入库3，inventory event763→native move760，supplier1297 −3、药房1293 +3，B `de141a797f552232fd087c484c0dfd33f06288ea14996a961477435ba701586e`。另新 lot284 入库3，event767→move763，B `ada853664a1e40ce84e36d0f5c3e2cc8ea358d0eacf2b3ad251f9b5005edd46a`。新目录721、合成价格354、mapping1277及link3独立确认；旧link2保持。R1 prescription31／lot278及其4＋2未重放。

医生对本轮新患者签发新处方35／line56 数量6、药房任务912；B `713e77879f7bf6f0d4b18730e5007485c15ecfafffbac4df4dbfc6f0d20962c2`。续接任务按真实状态保留；现有患者文书及未完成任务不能清除。

## 真实请求及独立读回

- 前台1554经正常独立 Context 登录，向新处方发真实 POST 返回 HTTP403 `access_denied: This business permission is required.`；该请求的 lease 参数为空，源码调用顺序与响应支持权限检查先于租约。B 核无新 receipt/event、费用或库存变化 `3076d62f1ce8bb26d4c00b736f8eb5602928c7c1f4b841b807694ebc9d3d823a`，请求日志 `58383ac74978a2cf3c6b23b46ba575046f662c31210a2e7e636e6832e9b08259`。不外推所有无权路径。
- 药房1559以合法受控入口实际发药1单位，event363／fee359=10／native move761，lot283药房3→2；B `ff2a14840c52bb7b7a82fe9484ef9ebf80470c569072342c295ac0c8d51d0c6c`。该岗位无上述库存模型 ACL，但业务入口成功派生库存和费用；层级按实际 ACL／HTTP 分列。
- 两个 HTTP 请求区间重叠竞争不足库存，一方409 `insufficient_balance`、另一方200 accepted。B 核成功方唯一event364/receipt417、move762/fee360数量2金额20，失败方无event/receipt，药房0／客户3，SHA `bfe14834ccedf7d2f56034289e0dd35dfe81522b3513924f46ffeec57690d24a` / `07b19dcee195e35357f96e759f1f09039da69068c7bc8bdac27ae9929dd59950`。客户端区间重叠不证明数据库锁等待。
- 首段正常 finish 后唯一续领914 pending，累计3/6，lease561 inactive，B `75b981b64043db70061015e06b135e07a2eb2fba62a1ea8b2f3e4fa670d42b5c`。新续领段发1后同 body/key 真实重发返回200 `already_accepted`；B 核 event/receipt/fee/move及lot284库存与首次快照一致 `cec83c1f97f744737db2a9ffee6c94170e1ae45218a3da1b7b4391c1b3616dbd`。再次 finish 后同body直接HTTP重发200 `already_accepted`，B 核event/费/move不变，正常finish receipt420新增 `d8dc7eee17552aef56c6330a9a78f1bcb0a207c7f33fb70f075826cfe9d8288f`。
- 完成事件366在真实浏览器可见，但页面无发药按钮、没有实际点击，日志 `609c6dc90b57bc69348aa819a98d3a864a6d2c5db3ea90a06713ecf60fdb6173`；因此**浏览器重复点击 NOT_RUN**，不能以直接HTTP重发替代。
- 新执行558对剩余2请求3，真实 HTTP409 `overdispense`；B 核无新发药event/receipt/费用/move，lot284余额2，SHA `09d40a64179c97554d97ae063bc772d1e59b4f231a871f5d15dac0094d5b47bd`。finish后task915 done、唯一余量916 pending、处方issued，lease563 holder_exit，B `3c241f54d4d583a3b6a076cb7fdb21e667a2fcde5704b25d5db3b8dee345da81`。
- 新退药由 inventory event764（treatment event363→consumption261／lot283）派生 return event769→native move765，客户1298→隔离1296一单位；lot283客户2／隔离1／药房0，续领915当时 pending，B `d3f088fc91a0765dbba18f5d30ac37310ba96995e5fee0050ebf6a5029dc258e`。done表示实物移入隔离，核查未完成，不自动恢复可领量。inventory event ID 与 native move ID 不混同。

## 失败、UNKNOWN 与资源

首药房脚本正常登录后遗漏切店，enter前 Error store、exit2；B 独立复现并分类 AGENT_OPERATION_ERROR，主控亲自正常登录／切店只读定向复验 GET200，B 核未形成lease，日志 `0addc438e6cfd81b8248a822c3008ced008e4d3857863e8501a127bee5676210`。原失败保留。

首次 duplicate 实际 HTTP400，工具解析 SyntaxError 未保留正文，首因 UNKNOWN；B 新Context以安全无权payload复现错误body编码，主控定向修正编码并取得403，无费库变化。后续新来源正常重发成功不补写原400正文。为避免错误编码的 replayafter，旧runner执行 stop 触guard exit2，Context正常关闭；不是产品拒绝。相同字节的工具摘要日志不可用于区分不同批次实体，实体按B来源读回。

本轮新患者的 doc515–519、CBCT908、continuation913及药房余量916等按实际状态保留；账号UID1559及其他R2账号的最终处置和专用服务停止由主控在计划收尾核验，Session失效未验。保护对比及资源最终状态待追加；私有原始证据在 `.local/s13-e2e-r2/`，凭据、Session及完整日志不公开。P14和生产、正式政策、真实资金、外部通知均未授权。

W3 末 B 独立只读对比158表全部行的非敏感字段及529个文件（缺失0），快照 SHA `ec1ca44657afb303803ee008aa5c66e8efd6c662ea1332da8a063b0b182b9d54`：相对W2末旧行零删除，变化仅5条技术mutex revision、R2 task911状态／版本、R2 floor281和queue scope1200版本／write_date；W2末519个附件引用的大小和哈希保持，新增10。首次比较工具误用文件键 `id` 退出1，改为 `attachment_id` 后成功，失败保留。该保护结论限纳入表与非敏感字段，不补历史缺失前像。

独立末态 SHA `2529f6df82e1db1478d3c1e3ddc689de8d7c44620b37b466bbc6af00e27da765`：旧11账号 inactive、旧10时段 suspended、11处置 pending；本轮7账号 active、无active lease或患者位置，task908/913/916 pending、line56已发4、旧mail exception13保持。PID2416485仍监听18554，最终资源与账号收尾在计划后续执行，不冒称已停止。
