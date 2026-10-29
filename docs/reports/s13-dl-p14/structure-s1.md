# P14 结构性布局 S1：独立风险与证据记录

2026-10-29，S1 C 未参与产品实现。此记录先标明已有证据与验证边界，最终候选须另由 B 和后续全新团队独立验收。

## 原失败保留

此前 T09 在实际引擎、已加载 QWeb 合成片段及简化外壳上，Chromium 8/30、WebKit 18/30 场景发生焦点轮廓水平裁切；WebKit 768 normal 中轮廓右缘773px，滚动框右缘744px。不是完整真实 Odoo 页面结果。前述 sticky 末列方案在极窄屏遮挡余额；RTL 方案在横滚后仍裁切且改变滚动方向，均未采纳。历史报告 [T09 续办](t09-addendum.md) 和 [独立复核](t09-independent.md) 原样保留，不因新布局改判。

## 本次待核风险

新布局须逐账单只有一个有效免单表单，并能从表格行定位正确的 summary 和原 invoice_id。多条合成账单才有能力暴露错配；只读、空态、PDF 无权和分页范围必须单独验证。通过 fragments 导航至 summary 不等于其展开或焦点自动可见；新行内锚点和 PDF 链接仍在横滚容器内，可能被裁切，不能仅检查移到外面的表单。共用 `details[name="settlement-operation"]` 的原生互斥行为、Tab/Shift+Tab 顺序、Enter/Space、取消动态 href、所有表单字段的语义与 FormData 必须检查。新布局仍须验证超长单号、余额与 reason 文本、两个200%缩放、双引擎和真正 JS off；超高内容按正常纵滚可达处理，不通过转移焦点代替直接 Tab 可见。

## 既有工具与 scratch 边界

`.local/dl-p14-t09/f2-a/`、`f2-b/` 有真实引擎几何采集和截图，但绑定旧 QWeb DOM、旧固定候选与简化外壳；若只替换 HTML 或复用结果将不能证明新结构。WebKit 几何脚本的 exit 2 是断言失败，垂直瞬间越界要单独分析。新工具应记录候选、实际载入模板/资产、每控件轮廓和裁切祖先、滚动和网络事实，保留前后原件。

`.local/p14-t09/real-get-base-01/` 是原隔离 scratch；此前正常合成来源提交 event1、fee1、posted invoice1，禁止重放。原 `http-invoice.cjs` 和 `http-formdata.cjs` 将 form 定位为 `#invoice-1` 的后代；外移后该测试假设失效，需新 scope 测试实际行→锚点→唯一外部面板→invoice_id，不能把旧断言直接失败认作产品 BUG。脚本允许正常登录和切店 POST 并阻断其他非 GET，该客户端阻断不能冒服务器拒绝或证明全库无变化。旧 before/after 摘要仅34张表、没有审计和附件实际文件；升级模板时前后独立读回应另设范围并分类正常访问审计及技术资产变化，历史缺失前像不能补造。凭据只在私有 provider，不进入 Git、报告或截图。本角色未启动服务、连接数据库或修改产品。

## S1 候选源码核查

D 完成后本角色在当前工作树只读查看 `git diff -- ydental_settlement/views/ydental_settlement_templates.xml ydental_settlement/static/src/scss/settlement_unpaid.scss`。相对于起始 HEAD `054701a5c091b50991fdc7981e1ed241549a132e`，差异仅这两个产品文件：原五列表格仍在原位置，每条账单的第5列在 `can_write` 条件下新增 `#waive-invoice-{invoice.id}` 片段链接；原 `details/form` 从滚动框移到框外同一 `invoices` 集合的新循环内，summary 标示单号和应收余额并带对应 id，原 `can_write`、name、表单字段和动态取消表达式可见保持。移出后表格末列不再承载表单，删除其原18rem最小宽度。原表单、token、分页与权限细节的完整机械检查以 B 实际报告为准；本角色人工审阅不能证明一一映射或实际 FormData。

独立执行项目 venv Python 标准库 XML 解析、libsass 将原共享 actions mixin 和修改 SCSS 拼接编译，exit 0，编译 CSS 16714 字节；`git diff --check` exit 0。候选 XML SHA256 `25ad51cea2e895ac5b1a2c14fef29f20544c22ee4e1bb9eb5a407b7cdc00487c`，SCSS SHA256 `0a48144164a0261e669e826a84f273a6aedea3739e10f4af89a887967b70e60f`。这些是此时工作树文件而非固定提交，后续变更需重验；独立编译不证明 Odoo 完整 bundle 或 HTTP 加载。

风险仍包括行内链接在横滚框中的焦点裁切、片段链接对原生 summary 的焦点行为、两个账单的正确映射与字段身份、旧/新页面混用与真实权限；这些必须实测。Guidelines read: Odoo views/actions/data records、web SCSS and CSS。没有对历史库、Odoo 服务或浏览器作任何操作，也没有执行经济业务。
