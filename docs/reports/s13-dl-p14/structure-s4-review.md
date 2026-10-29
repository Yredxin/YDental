# P14 结构调整 S4：独立最终审查

2026-10-29，复核者未实施产品、未连接数据库。固定候选 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8`，与 `39038bd8b84ef00fe46dc37973e05a0e46d12796` 比较；结论 **PARTIAL，T09 FAIL**。不得把表外表单局部改善冒充整个键盘验收通过。

## 发现

- **[阻断验收] 新增的账单办理锚点仍被表格滚动框裁切。** `ydental_settlement/views/ydental_settlement_templates.xml:129`：真实 Chromium、普通写岗位、已提交合成账单、JS on 的真实 Tab 测试中，320×800 原生 200% 时锚点轮廓 x9.13–151.14、横滚框 x24–136；320 root 200% 和 768×1024 正常缩放也裁切，合计所测 3/9。768 正常时轮廓 x637.14–779.16、框 x24–744。用户不能以转移焦点后横滚代替 Tab 一次到达时可见。独立读取 `.local/p14-structure/s3-b/real-focus.json`，对应候选和真实岗位 HTTP 合成账单层级；属具体产品候选在限定条件下的可访问性失败（judgement），不是脚本异常。按本计划停止叠加试验；是否保留或回退候选由用户/GPT依据证据决定。

## 合同及证据边界

`git diff --check 39038bd 34f7681` exit 0；该候选相对产品基线的产品文件仅结算模板和局部 SCSS。重新执行 `../.venv/bin/python .local/p14-structure/s1-b/check.py > /tmp/structure-s4-contract.json` exit 0，结果 SHA256 `74dfeae3fead6949d339184166f4002328e07aa1dafa2c36995af02169c28e05`，其检查原 form、cancel、五列、PDF 条件、分页与限定区域之外的 XML；仅源码结论。原表单移至同一 `invoices` 集合新循环，链接 target、summary id 和 invoice_id 由相同记录 id 派生；没有复制表单。跨账单 Tab 次序已改变，应按新布局判断，不声称原 DOM 顺序不变。

实际候选 worktree HEAD 经本人独立 `git -C .local/p14-structure/s3-a/source rev-parse HEAD` 核为 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8` 且工作树 clean。读取已加载 QWeb 内存两账单结果 SHA256 `1fdab3a76abc05f1a1152db0e57ba42274fdf5ef715bbb36cd5126378fb27bab`，记录了两账单行锚点、对应 summary 和 invoice_id、权限布尔组合与空态；此为只读事务合成，不代表真实多账单权限。真实 HTTP 仅一笔合成账单，正常 write/read 两岗位 GET 200，write 唯一表单、read 无表单，实际 CSS 200、FormData 内存顺序及绑定有记录。真实 write 岗位无 export，PDF 真实链接未测；完整真实页面双引擎、JS off、五视口矩阵尚未完成。S2 双引擎的30组合使用旧 QWeb 片段静态变换和简化外壳，不能冒候选真实页面。

S3 B 的升级后独立只读连接与 A 保存的升级前34表全行摘要一致；A 未等待 B 升级前独立采像，不能补签。HTTP 后 `ir_attachment` 哈希改变、109行数不变，逐行前像缺失，具体变化 UNKNOWN；审计记录有正常访问新增，历史库、未覆盖表和附件文件不能外推无变化。UID6/7 状态及岗位授权来自 S3 B 的升级后只读记录，不由本角色数据库独核；既有 invoice1/event1/fee1 已提交且不可重放。

本人只读执行 `docker inspect --format '{{.State.Running}} {{.State.ExitCode}} {{.HostConfig.NetworkMode}}' 2007f4e0c139739dcf56f18403d177683b85319d7ee08f3d332155d14e4956f4` 得 `false 0 none`，`ss -ltn '( sport = :18631 )'` 仅表头，端口无监听。本人未审计其他进程、旧 session 或外部系统。S3 记录未发送经济 POST；无 POST 不能证明全库零变化。

Guidelines read: Odoo reviewing process、views/actions/data records、web SCSS and CSS。未改产品文件或启动服务。
