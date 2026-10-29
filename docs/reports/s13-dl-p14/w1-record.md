# P14 W0/W1 独立记录（SOURCE/PURE）

2026-10-29，W1 C 独立检查当时工作树；产品基线 `f9c4778e584e0513bcaf46cee3a76fd6883b76af` 是报告起点 `c663557eeb30b9bb43f07f3ff8130c8cd3bc4382` 的祖先。W0 B 报告两者结算模板 SHA256 相同（`ee8e31d2246f1835f66a00f9ba5834de2e44c3b43706ea4587ba9167805cf558`）；W0 A/C 报告历史合成库受保护，不得升级或重放经济、库存、原件和历史待办。此处是 W0 角色发现的记录，不是本角色对数据库的独立读回。

当时产品修改为结算模板局部 class/data 属性、独立 `settlement_unpaid.scss` 和 manifest 中一项前端资产；`CURRENT_TASK.md` 为主控状态记录。`git diff --name-only` 不包含未跟踪的 SCSS，`git status --short` 单独确认该文件。模板内原五列表格、分页调用、可见条件、waive 字段、动态链接和表单结构在人工差异阅读中未见改变；业务合同的机械独立核查由 B 另记。共享 mixin 和其他产品文件未见本轮修改。SCSS 以新 section 的 class 与 `data-dl-scope` 为根，内含 48rem 表最小宽和末列 18rem 最小宽；窄屏横向滚动、焦点及两种放大必须用真实浏览器验证，源码不能证明可达。

独立执行：在仓库根目录用 `../.venv/bin/python` 的 libsass 将 `ydental_access/static/src/scss/_actions.scss` 与新 SCSS 拼接编译；同进程用标准库解析模板 XML 和 manifest，确认 `web.assets_frontend` 包含新文件。退出码 0；产物 16355 字节、SHA256 `cd859df1be07e24aea2b4f589785da89d5db0637a6b61f373ee704181f80f7dd`。`git diff --check` 退出码 0。该编译仅验证独立组合，不代表 Odoo 完整资产管线已加载。

当时文件 SHA256：模板 `27611570b440fd0741fb70e647a78fcf4b1ae213f9817b1d54fb0aec22f32d31`；manifest `20f1bed3a8045af622203d35a6481d7ea8f68bac6cc7217a31e9f9a01b890c98`；SCSS `16797f18b4909b8636d258530cce06c344db2fae6df20c03adc16107077c178a`。如后续改动则这些仅是该时点证据。

D 报告首次以系统 Python 导入 lxml 失败，后改标准库解析成功；此为 D 的工具环境失败，非产品 BUG。C 自己未运行浏览器、Odoo、数据库或 POST，不能声称权限、实际 QWeb 渲染、历史保护或最终技术验收通过。待核的原生 details 联动、真实 FormData、各视口/放大/JS 状态、长内容、实际普通岗位 GET 与合成组件均须分层记录。
