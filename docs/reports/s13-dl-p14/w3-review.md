# P14 W3 独立源码及证据复核

复核者没有实施产品代码。本次以 `c663557eeb30b9bb43f07f3ff8130c8cd3bc4382` 为比较基线、`d70793d98c7cedbe7836900a811e517c8b9a47c8` 为固定候选；这是源码及现有证据复核，不是最终完整验收。

## 源码事实

`git diff --name-status c663557 d70793d` 和 `git diff --check c663557 d70793d` 退出 0。产品只改变三个文件：结算 QWeb、该 addon 的 manifest 和新建的局部 SCSS。manifest 除 `web.assets_frontend` 新增本 SCSS 外没有改变；没有修改 JS、后端或其他 addon。新 SCSS 从未付清 section 的 class 和 `data-dl-scope` 开始约束，动作样式复用原共享 mixin，不改共享 mixin。第三、四列金额 `white-space: nowrap`，依赖原表格滚动容器而不隐藏列。

独立执行 `../.venv/bin/python .local/dl-p14/w3-b/review.py > .local/dl-p14/w3-b/result.json`，退出 0：逐节点核对原有 class 未删除，去掉新增 class/data 装饰后完整 QWeb 的 C14N 与基线一致，文件清单与 manifest 匹配。最终 XML SHA256 `27611570b440fd0741fb70e647a78fcf4b1ae213f9817b1d54fb0aec22f32d31`，SCSS SHA256 `b83900056086ff90be02e57410381e1d4360fc94001241a7a0da5eadf19ffd30`。这证明源码结构和表达式未改：五列顺序、金额/余额取值、分页调用、can_write/can_export/invoices 条件、PDF href、details name、form method/action、token 调用、waive/invoice_id/amount/reason 属性、submit 和动态取消 href 仍然保留；不证明实际部署、真实权限或运行时提交。

## 浏览器证据的边界

- `.local/dl-p14/w2-a/` 使用真实 Chromium 运行源码衍生静态夹具，30 条包含五视口、三放大条件和 JS 开关，全部脚本运行无异常；此批采于金额列修复前候选。脚本对许多字段顺序和几何仅记录，不自动断言；不能以 30 条无异常冒称所有合同和可达项通过。320/390 两种 200% 下横滚两端分别可达，但记录中控件焦点轮廓不能同时完整显示；滚轮尝试无滚动，原因未确定。
- `.local/dl-p14/w2-b-fix/` 以最终候选衍生的静态夹具运行 WebKit，30 条基础断言及窄屏键盘横滚定向检查通过；长单号下金额列宽从约 40/40px 提升至约 73/88px，金额单行。夹具非完整 Odoo 前端、非真实岗位 GET 或授权数据，不证明真实权限。旧的首轮外壳溢出是缺少 Bootstrap `border-box` 的夹具错误，原结果保留。
- 两套静态夹具的令牌、账单是合成值；`new FormData(form)` 的次序不证明真实 QWeb 动态 token 值、原生请求或持久财务状态。Chromium 未测 submitter/空态/真实取消链接；用户要求的最终候选双引擎真实页面全矩阵和独立历史保护读回不能由本审查代签。

复核时未启动服务或数据库、未发送业务请求，也未修改产品文件。历史经济、库存、原件、附件、文书、审计和待办的当前数据库状态不在本复核范围内；不能由无 POST 推断全库无变化。其他团队在独立 scratch 所取得的真实加载结果须按各自证据和实际代码版本另记。

Guidelines read: Odoo views/actions/data records、manifest、module structure and file naming、web SCSS and CSS；本变更未修改 controller、ACL、sudo 或 RPC 方法。
