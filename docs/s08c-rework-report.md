# S08-C 原生崩溃诊断与 RX-2 分页返工工程报告

本报告依据 [#32 最新 GPT-REVIEW](https://github.com/Yredxin/YDental/issues/32#issuecomment-6138991636) 和已逐字读回的[第一阶段取证评论](https://github.com/Yredxin/YDental/issues/32#issuecomment-6139121593)。工作仅在 `codex/s08-c-pdf-print-r1-20261013` 线性向前进行；旧 final `1f5bae007d466f4f6dc932fde435a41f59a9b79f`、旧 test `87b2c8588ac3012abce7d9db5f26dc5682dc4e7d`、两座旧 C 库和旧失败证据均保留。本轮最新 product 为 `51b5b6df900b58ee925619ecea45c9cc9b826480`，固定 test 为 `141301e473e83c9429335b5127e76b7c0e4cc8a7`；本报告属于其后的 final 文档提交。`product→test` 仅修改测试/验证器；返工过程中更早的候选产品和测试提交也全部保留，不把候选结果拼成最终 PASS。

## 原生事故和有界恢复

旧 Odoo PID `1670701` 在 Python 3.12 的 `dict_dealloc` 指令附近收到 signal 11，原生退出 `-11`、外层 `245`，发生在 registry/post-tests CSS 资源生成之后、首个可见测试结果之前。[原始事故](evidence/s08c/native-crash.json)与[第一阶段脱敏取证](evidence/s08c-rework/native-diagnosis.json)分别保留原日志哈希、内核事件和运行边界。原事故进程 core limit 为 0，apport 因解释器不属于系统包而忽略；无 core/native stack。`dict_dealloc` 是崩溃指令所在函数，**根因仍 UNKNOWN**，不能据此归咎 QWeb、PDF、字体或某个扩展。S07 Python `_PyObject_Calloc` 与 B Firefox `libxul.so` 的事故证据不同，也未建立共同根因。当前内存/共享内存/FD/依赖只读检查不能替代事故时快照。

按先前在 #32 公布的上限，只在全新隔离库 `ydental_s08c_test_20261013054544_d143b812`（OID `1337165`、18179、同 cluster）运行两次带 `PYTHONFAULTHANDLER=1` 的 Odoo 子进程，私有原日志未覆盖。命令及实际退出：

| 命令 | PID | 退出 / tests | 结果 |
| --- | ---: | --- | --- |
| `PYTHONFAULTHANDLER=1 ../.venv/bin/python scripts/s08c.py install --db ydental_s08c_test_20261013054544_d143b812 --port 18179` | 1701874 | `1 / [1,0,103]` | 越过原 post-tests 边界；HTTP 故障注入测试预期 409 实得 200 |
| `PYTHONFAULTHANDLER=1 ../.venv/bin/python scripts/s08c.py upgrade --db ydental_s08c_test_20261013054544_d143b812 --port 18179 --print-only` | 1704123 | `1 / [1,0,23]` | 同一测试缺陷；无新增 SIGSEGV |

失败来自原测试补丁打在 addon 扩展类，而 HTTP 请求使用 registry 合成类。新 test 改为 patch 实际 `type(self.root['ir.actions.report'])`，正常渲染失败需返回 409 且不建 job/业务事件。两次诊断**没有证明 native 根因已修复**；后续只在全新 guard 库、固定 test、专用端口和精确 config/PID 控制下运行。发现新 SIGSEGV 必须立即停止重跑。本轮后续固定回归无新 SIGSEGV，但生产稳定性仍 BLOCKED。

## 分页原因、改动与可见验证

旧 RX-2 用不可分割的 `<tr>` 包多段长文，并全局设置 `tr/p page-break-inside:avoid`。wkhtmltopdf 对跨页表格行的分页约束是**有证据支持的版式原因候选**；未取得引擎内部堆栈，故不声称唯一根因。保留的旧 17 页候选及[旧人工 FAIL](evidence/s08c/candidate-page-visual-review.json)没有覆盖：重新核对哈希相同的原 PNG 时，旧记录所称第 7/9 页正文缺失与图像可见正文相矛盾，这一冲突如实保留。另一个首版候选发生处方行标题跨页重复/裁切，也已保留。

本次仅将处方**每行**的长字段从表格单元格改为可分页的 `article/div/p`，保留所有源行、SKU、规格、用法、频次、疗程、数量、状态与真实发药表；行标题和首字段作为不可拆的开头，字段正文允许跨页。没有缩小字号、截断医疗文本或减少药行。补充四个中文标签翻译。原 A 病历、未签署同意书及受控服务端导出契约继续适用：[字段字典](s08c-data-dictionary.md)、[模板/来源版本](s08c-contracts.md)、[权限与审计](s08c-security-review.md)。QWeb 仍用 `t-out` 输出源字段；没有新增公开 RPC、附件 URL、外链或脚本。

固定 test 在新库生成**16 份真实合成 PDF、共 57 页**，其中 RX-2 16 行、三 SKU、长中文及无空格英文占 13 页。验证器逐源行核对 ID 顺序、SKU/药名/两类规格、用法/频次/疗程、开立/实际已发/未领、单位、状态/原因与字段末标记所在页；A4、Noto CJK 嵌入、中文、边界、重叠候选、稀疏/空白主体像素均有自动检查。自动产物明确标记 `AUTOMATED_PASS_VISUAL_PENDING`，**不代替人工**。Codex 已打开 57 张实际 PNG，通过 15 张接触表逐页再核：没有页脚孤页、正文丢失、乱码、明显裁切或重叠；第 12 页的一个字段标签在页尾、正文续至第 13 页，可读但仍是分页美观上的剩余改进点。见[逐页验收清单](evidence/s08c-rework/visual-acceptance.json)、[PDF/PNG/源行矩阵](evidence/s08c/probe-attempts/20261013T064304331872/rendered-pages.json)及[全部样张目录](evidence/s08c/probe-attempts/20261013T064304331872)。这是 Codex 自测，不是 GPT/用户独立验收。

## 同一固定 test 的完整新库回归

固定 test `141301e473e83c9429335b5127e76b7c0e4cc8a7`，唯一最终库 `ydental_s08c_test_20261013063042_4e7a1d2c`，OID `1386445`、端口 `18182`、PG cluster `7694897083368259627`、config SHA256 `68daefb740a580efca59e734df5007a7eaf78d86ad2e0eb98516196de1211cea`。真实总命令：

```bash
PYTHONFAULTHANDLER=1 ../.venv/bin/python scripts/s08c_validate.py --db ydental_s08c_test_20261013063042_4e7a1d2c --port 18182
```

外层退出 `0`、[27 条命令逐项记录](evidence/s08c/validation-ydental_s08c_test_20261013063042_4e7a1d2c.json)全为 `0`；安装 `[0,0,103]`、空升级 `[0,0,101]`、已提交业务再次升级 `[0,0,101]`（安装比升级多 2 项原生资产初始化）。

| 适用项 | 固定 test 实际结果 |
| --- | --- |
| C-T01—C-T03：病历/处方/未签同意书、版本/字段/6→4→2/三 SKU、二进制下载 | PASS；16 PDF / 57 页、源字段矩阵和样张上链；演示/未审/无签章醒目标记，费用来源未冒充付款 |
| C-T04：版式/字体/长页 | PASS；57/57 实际逐页目视，最长 Rx 13 页，中文/英文连续字段与三 SKU；机器结论和人工结论分开保留 |
| C-T05：Firefox 预览/下载/原生打印请求/断网/重试 | PASS；C 43 项/14 图、pageerror 0，三类 PDF 原生对话框已打开目视；`physical_paper=UNKNOWN` |
| C-T06：角色、跨店、撤权、RPC/附件负向与审计 | PASS；真实 HTTP 模型测试、C5 独立后端竞争、C Firefox 负向；打印 job 无普通 ACL，二进制 `attachment=False`；生成/下载/打印请求审计 |
| C-T07：失败注入、并发版本与纯导出经济不变性 | PASS；runtime registry renderer fault-injection、源并发 C5、失败/断线/重复；C 阶段前后 26 张来源/经济/库存/队列签名相等，允许的仅 print job/audit 增长 |
| C-T08：隔离安装/升级/业务再升级/翻译/安全 | PASS；三次实际 Odoo 子进程均退出 0、中文导出 `176/176`、guard 退出 0，升级前后所有 27 张签名/容量总量相同 |
| S08-T11/T12/T16 及 A/B 必要回归 | PASS；A16+B25+C5=46 组真实独立 PG backend/barrier、deadlock 0；A Firefox 88/21 图、B 24/13 图、B 返工 23/14 图，均 pageerror 0；原 A/B 模型/HTTP 随安装及升级运行 |
| 实际纸张、生产稳定性、生产部署及 S09/S10/S12 | `UNKNOWN/BLOCKED/NOT_RUN`；不可用浏览器打印请求替代出纸证明 |

共 `88+24+23+43=178` 项 Firefox 检查，`21+13+14+14=62` 张截图；62 张均在接触表查看，三类原生对话框另以原分辨率复看。[Firefox 目视记录](evidence/s08c-rework/firefox-visual-acceptance.json)与[原 C 截图/结果](evidence/s08c/print-browser-attempts/20261013T065003754217/result.json)可逐图追溯。四个专属预览 PID/config 精确匹配后各正常退出 `0`；现有服务和其他 PID 未停。`xvfb_exit=-15` 是本批专属 Xvfb 受控终止，不是 Odoo SIGSEGV。末次 SQL 审计 41 类不变量错误 0；对读写副作用、原生库存、费用、治疗、患者队列、文书版本和容量均做前后核对。A Firefox 合法开始接诊会更新 `ydental_supply_claim` 状态/版本，新 test 明确将该表从 A 的**行字节不变**断言中排除，但仍断言 claim 数量与容量总量不变；C 纯 PDF 操作仍要求 claim 签名完全不变。

## 失败链、环境与回滚

本轮保留四座新增隔离 C 库及其私有日志：`d143b812` 的两次故障注入测试失败；`9cb7482e` 的首个可分页候选仍出现标题跨页重复/裁切，验证器判 FAIL；`2f19ad4b` 的 57 页已可读，A Firefox 返回 0，但旧 SQL 审计把合法 intake claim 状态变化错当 PDF 经济副作用，整体验证 FAIL；最终 `4e7a1d2c` 在修正测试判据后独立完整重放 PASS。前两次候选及旧 RX-1/RX-2 PDF、PNG、日志/哈希、原始错误描述均未覆盖；不将异 SHA 的 PASS 拼入最终结果。S07 与 B 浏览器历史崩溃、B 原生序列化重试耗尽仍是独立风险。

新库均使用原 guard 命名、独立 data_dir/dbfilter/端口、PG endpoint/cluster/OID/marker/configSHA 验证。结束时只读比较 PG `pg_database` 的原 117 个 OID/名称对与旧冻结目录，117 对全部存在；当前 123 库，增加的恰为六座 C 合成库（旧 2、新 4），cluster 未变，见[数据库保全核对](evidence/s08c-rework/database-preservation.json)。Odoo20 core、odoo-12、历史库/卷、db20 `shm_size=256 MiB`、现有服务及系统依赖未在本轮修改；私有 libpq 会话参数仅关闭并行、维护内存 16 MiB。回滚产品只需在测试/开发环境切回旧 final `1f5bae0` 或禁用本批 `ydental_print` 改动；**旧版长处方分页及原 SIGSEGV 风险将随之恢复**。既有数据库、临时 PDF/截图和日志必须保全，不能通过删除证据“回滚”。生产回滚/部署未实测。

## 期限、二进制保留及剩余风险

`ydental.print.job.ydental_expires_at` 在生成后 15 分钟，服务端 `_deliver` 拒绝过期读取；然而 `ydental_pdf` 是 `attachment=False` 的数据库二进制，当前 `write/unlink` 被模型拒绝，**到期不会自动物理清除**。普通附件直链没有该 PDF，当前 ACL 与 `NO_ACCESS` 阻止普通读；数据库备份仍可能长期保留演示医疗内容。建议单独授权并设计“到期清空二进制、保留 job 元数据/哈希/审计”的限界清理操作，先评估不可变模型、备份保留、法务/隐私、失败恢复和旧证据冻结的影响；本轮**没有删除旧文件或建立 S12 正式归档**。

本批技术回归自测通过只证明固定库与受控运行窗口；PID 1670701 原生根因没有定位，原 S07 SIGSEGV、B Firefox 崩溃和重试稳定性未解，生产发布继续 **BLOCKED**。Project #4 本轮只读双快照的 21 字段/15 条目/6 视图及字段/7 workflow 与旧 final 深比较完全相同，[快照](evidence/s08c-rework/project/project-after.json)和[第二次快照](evidence/s08c-rework/project/project-second-check.json)可查；#32 仍 `S08／进行中／Todo／OPEN`，本批 Project mutation `0`。等待 GPT 独立技术复核，不启用 S09/S10/S12、不合并主分支、不关闭 Issue、不生产部署。
