# P11 来源详情有界验证

只适用于用户启用的 YD-S13-DL-P11 / 1.0。产品、报告和运行调度由 root
统一管理；浏览器工具不创建业务数据、不下载原件、不CSV、不启动服务。

`browser_checks.py` 保存实际 executed 脚本、候选、原参数、原PNG和实际
Node退出。原失败保留，不自动重试；超时保留未知child并等待核实。
`.cjs` 复用既有正常浏览器依赖与真实native zoom机制；每次先核当前
P11 owned服务，凭据仅由正常私有provider读取，认证/正常选店技术POST
之外仅GET。禁止业务写入的预拦截不算产品权限拒绝。

模式 `layout` 采真实普通角色原main href钻取、五view、完整投影、两return
实际点击和main/error隔离；`zoom` 分别原生200%和独立root32；`nojs`
在同禁JScontext正常认证后验证原生details/返回；`permissions` 真实授权
和后端无源/非法scope拒绝；`components` 明确loaded QWeb内存长值/多分摊/
跨店/多卡片分支及用户文本间距、缺CSS/SVG故障，不冒真实授权或持久数据。

`browser_source.cjs` 完整保留title/scope/cards/事实/分摊4列/trace和所有href。
只在语义比较中将原生scope第三段query_at_utc值单独分类；原值保留。
`source_contracts.py` 仅SOURCE/PURE，不冒实际loaded/browser。
`viewing_package.py` 从显式清单复制原PNG逐bytes构造私有0400 ZIP，内含
完整manifest/SHA；不包括凭据、Cookie、profile、原请求、DB、原件、CSV、
字体或程序。未实现者须逐源/成员/隐私独立核验，构造成功不算验收。

`keyboard` 是真实普通岗位 source 原导航相邻两控件的可信 Tab / Shift+Tab
补层，保 active、原 href、完整焦点和原 PNG。`diagnostic` 只测单个明确
loaded QWeb 组件首视口的原字体 Range；首尾全文端点先保存原状态，再以
真实 window/原 auto-scroll 容器正常滚动补读并保存前后几何，不改 CSS、
字体、文字或判定阈值，也不滚动 hidden/clip 容器冒用户可达。
`focus-diagnostic` 保留有分摊组件横读后视口切换的原顺序；保存原生 Tab
即时、两帧加250ms后、正常 scrollIntoView 后的实际 scrollLeft / box /
ring / clip 和三张未编辑现场图，用于区分原生滚动与收集器影响。
先前实际私有小测试的 exact executed 源与退出独立保留；最终公开函数整合
不反签此前失败、不同候选或未运行模式。
