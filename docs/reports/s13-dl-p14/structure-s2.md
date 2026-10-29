# P14 结构调整：S2 独立证据记录

2026-10-29，S2 C 未参与实现。固定候选 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8`。本阶段 A/B 的浏览器测试均将旧已加载 QWeb 片段手工变换为新结构，再加载候选 SCSS 和简化外壳；它们使用真实 Chromium/WebKit 引擎，但**不是候选实际已加载 QWeb、完整 Odoo 资产或真实岗位页面**。所有数据为内存合成，未发送经济 POST。

## Chromium

独立读取 `.local/p14-structure/s2-a/results.json`：五视口 × 正常/native200/root200 × JS on/off 共30组合，0脚本异常。14组合存在至少一个表内焦点轮廓水平裁切：12组合包含新免单锚点，14组合包含既有 PDF 链接；数字分别独立计数，不相加。320 native200 新锚点轮廓 x4.32–146.33、滚动框 x24–136；320 root200 新锚点 x9.14–291.16、滚动框 x24–296。该测量记录了真实 Tab 后几何，不能用转移焦点再横滚代替；只在简化夹具范围内判定，尚未归因完整产品页面。面板内各字段位于滚动框外。原始 `results.json` SHA256 `534e962fb766697b9d80c42a46ecb58501d3aab27683de32c0c0fc75c7d9a970`，测试源码、截图、运行结果及详情见该目录 `report.md`。

首轮工具在页面保留片段地址时执行 Chromium 缩放扩展导致28例异常；原结果和日志以 `initial-*` 保留，修正每例先导航到 about:blank 后重跑。最终 exit 2 对应几何裁切，不是脚本异常。A 报告每例在双账单合成中测试唯一 row→fragment→summary→隐藏 invoice_id 对应，真实 Enter 落对应 summary 后 Space 展开、内存 FormData 与输入次序；截图、执行命令及真实网络计数保留。焦点几何与可访问性仍须实际候选 QWeb/真实页面验证。

## WebKit

B 首轮工具在 reason 获焦后以 locator.fill 修改 amount 导致焦点被转移并反复访问 reason；这属于测试驱动错误，已保留 `initial/` 并用页内设置值保持焦点后重跑。独立读取修正后 `.local/p14-structure/s2-b/results.json`：30组合、0脚本异常、每例两个合成账单的表单序列均记录，所有记录字段顺序为 csrf_token、revision、key、output、operation、invoice_id、amount、reason；本夹具未记录水平焦点轮廓裁切。结果 SHA256 `834b74064a220e0c53093ac906f08d7399852e715ba05e309aad73433780c9cc`；不以脚本 exit 0 反签实际加载页或真实权限。320 native200 的超长账单 summary 高约1234 CSS px，物理视口无法完整同屏，须另按正常纵向滚动可达评估；不把垂直瞬时越界混成横向裁切，也不凭此声明完整焦点体验通过。

## 已加载 QWeb 多账单准备

S2 C 新建私有 `.local/p14-structure/s2-c/render_loaded.py`，`../.venv/bin/python -m py_compile` exit 0，脚本 SHA256 `1468b5eb805d133583a99609aaec6b780449892b2e02fcbfb8b14b753acf2fc9`。拟在经现场身份核验且确已加载固定候选的独立 scratch 的 Odoo shell 中运行，强制确认 DB/OID/cluster、只读事务，读取实际 combined arch，渲染两条内存账单及可写/只读、导出/无导出、空态共五分支；逐笔核五列、片段锚点、唯一 summary、显示单号及余额、唯一表单 invoice_id 和字段顺序，结束 rollback。脚本尚未在 Odoo 或数据库中执行，语法通过不是 QWeb 通过；其数据和权限均为合成，不冒真实岗位或财务数据。原 scratch 和旧证据本角色未启动、连接、改写。
