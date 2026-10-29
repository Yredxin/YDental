# P14 最终独立复核

2026-10-29，复核者未参与产品实现。结论 **PARTIAL，不签完整技术通过**。最终候选 `39038bd8b84ef00fe46dc37973e05a0e46d12796` 撤回了不可靠的焦点修复；`git diff --exit-code d70793d 39038bd -- ydental_settlement` 退出 0，故下列 `d70793d` 实测对应的结算产品文件与最终候选逐字节一致，不能因此称提交哈希相同。其相对 `c663557` 的产品差异仅结算模板、manifest 一项资产和独立 SCSS；`git diff --check c663557 39038bd` 退出 0。独立运行 `python3 .local/dl-p14/b-contract/check.py` 退出 0；此前完整 XML C14N 检查和字段细节见 [W3 审查](w3-review.md)。这属于 SOURCE，不能替代真实授权或持久业务验证。

新独立 scratch 以 `d70793d` 首次安装退出 0，在只读事务中以实际加载的 QWeb 渲染 normal、long、readonly、empty 四个合成分支并回滚；读取 `.local/dl-p14/w3-final/result.json` 与 `intent.json` 确认候选、cluster `7701958915498270749`、库 OID `16384` 和运行记录。资产列表解析包含新 SCSS；完整 bundle 编译及 HTTP 加载未验证。内存布尔值、token 与账单为合成数据，不是普通岗位权限或财务实证。渲染日志的测试 lambda 警告见 [W4 记录](w4-independent.md)。

Chromium 与 WebKit 使用加载 QWeb 的合成 HTML、候选本地编译 SCSS 和简化外壳，分别记录五视口、三种缩放与 JS 开关共 30 个组合；基础断言涉及表头、原生展开、键盘、300 字及内存 `FormData(form, submitter)`。空态和只读为合成分支，不能代表真实岗位 GET。Chromium 首轮把 Home/End 用作横滚键导致工具断言失败，修正后结果及原失败均保留；WebKit 另存焦点数据。检查 `.local/dl-p14/w4-b/focus-results.json` 可复现 768×1024 正常缩放下金额和原因输入右侧 767px、滚动框右侧 744px，Tab 聚焦时裁切 23px。结果中的 `pass` 不包含焦点几何，不可视为焦点通过。320/390 两种 200% 在 Chromium 也有控件被裁，横滚两端可达须先转移焦点。真实完整页面、真实权限、真实取消导航及完整焦点可见均未通过或未测。局部 CSS 的后续尝试 `7f2c455` 在 WebKit 仍裁切且极窄输入过窄，已撤回；不把该尝试的 Chromium 成功结果混签最终候选。

查看包 `.local/dl-p14/viewing/P14-static-view-only.zip` 的 SHA256 为 `7f6e132355cf34a15f3bd43632163cdd7037ec2713bfdb9666d8dbfe2435f1e2`，`unzip -t` 退出 0。包说明明确为静态合成 WebKit 截图，基线和候选单号不同，不能作像素级对照、真实 QWeb 或权限证据；候选截图对应与最终产品树相同的 `d70793d`。

独立 `docker inspect` 对三个本次 scratch 容器 `fd07286b097c`、`62925da9886d`、`83f8bf8d8f31` 均返回 `Running=false`、`ExitCode=0`、`Network=none`，命令退出 0。本次复核未启动或停止资源。浏览器角色报告 context 和浏览器已关闭；此处没有审计主机所有进程。历史库没有本轮独立前后读回，经济、库存、原件、附件、文书、审计和待办全库保护结果为 UNKNOWN；不能以无经济 POST 声称全库无变化。P12、R1/R2/R3 的历史 PARTIAL 和 E2E-BUG-002 不由本次改变。
