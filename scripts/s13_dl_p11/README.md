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
