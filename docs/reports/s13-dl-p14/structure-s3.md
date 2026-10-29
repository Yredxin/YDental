# P14 结构调整：S3 真实加载与保护记录

2026-10-29。S3 C 未参与产品实现，不负责启动或停止资源。固定候选 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8`；证据按实际层级记录。本报告的阶段事实随执行与独立复核完成而补充，不以脚本成功或某个快照代替全面验收。

## 目标身份与受控升级

S3 A 在本次复用前通过现场数据库连接核得 cluster `7701965376565411870`、库 OID `16384`，原合成 invoice1 为 posted/out_invoice、原金额和余额各100.00，UID6/7 active；身份前像 `.local/p14-structure/s3-a/evidence/identity-before.json` SHA256 `89934d225e8278868804e681a53df31b811a946359d58354406a88505a8371f7`。核对 candidate 独立工作树 `git -C .local/p14-structure/s3-a/source rev-parse HEAD` 为 `34f7681797f4ad4aec0b3aa7201b9bf9d02761d8`，工作树 clean。该目标是先前独立 scratch，不是受保护历史业务库；原合成 event1/fee1/invoice1 已提交，不得重放。

A 采 34 张受检表的升级前后全行摘要并报告仅在该目标对候选执行模块升级，进程 exit 0；两份证据 `before-upgrade.json`、`after-upgrade.json` 字节一致，SHA256 均 `176da7a581e4fb3c05b30dfd92e8feab69f464a4550317f00330e56a3d81584d`，身份前后 JSON 一致。A 在 B 尚未独立连接采前像时已开始升级，这是实际调度遗漏；不能称该前像由 B 独立读回。B 随后独立新只读连接再次核对 cluster/OID、账单 posted/原金额/余额及 UID6/7 状态，34 表摘要与 A 留存的前像字节一致；独立证据 `.local/p14-structure/s3-b/`。被比较表范围及 snapshot 工具见原始文件，不覆盖全部数据库、所有技术资产、日志、附件文件内容或历史库；正常模块升级本身会产生技术变更，不能据此声称数据库无变化。

## 实际加载 QWeb 合成分支

在已升级目标中，A 按实际 loaded combined arch 在只读事务内执行两条内存账单及 write/read、export/noexport、empty 五分支并 rollback，结果 `.local/p14-structure/s3-a/evidence/loaded-qweb.json` SHA256 `1fdab3a76abc05f1a1152db0e57ba42274fdf5ef715bbb36cd5126378fb27bab`，arch SHA256 `4fbc2d2765e592520369472af122f97094a7cc064529b59c02b06545a7cd0a12`。账单和权限布尔为内存合成，不等于真实岗位权限或实际多账单。渲染工具、日志及结果保留在 `.local/p14-structure/s2-c/`、`s3-a/evidence/`。


A 记录升级命令为项目 venv 的 `odoo-bin -c <本次私有配置> -d ydental_finance_test_20261029055915_fc94147d -u ydental_settlement --stop-after-init --without-demo=all`，候选独立工作树与隔离网络环境，exit 0；`odoo-bin shell` 使用同配置和库、`--no-http` 运行上述只读渲染脚本，exit 0。渲染日志包含测试 lambda 的 `Unsafe function access` 警告，原日志保留；这些命令不等于真实岗位浏览器通过。

B 的升级后新只读事务另核 source1 → fee1、store1、patient2、invoice1，UID6 为本店 settlement write，UID7 为 settlement read，原始 `.local/p14-structure/s3-b/verify-after.json`。该容器内数据库角色实际具有超级用户等属性；本次 B 事务显式只读，不能将其描述为受限数据库角色。

## 真实岗位 HTTP 与资产

A 的 `.local/p14-structure/s3-a/evidence/http-result.json` 记录新候选在同一 scratch 的正常岗位页面：write 和 read 均经正常登录、切店后 GET 200；账单1五列，write 存在唯一表单，read 无表单且显示“仅供查阅”。write 行内片段锚点跳到 `#waive-invoice-1` 并使该 `SUMMARY` 成为 activeElement；内存 `FormData(form, submitter)` 顺序为 `csrf_token, revision, key, output, operation, invoice_id, amount, reason`，合成金额12.34、reason长度300，operation=waive、invoice_id=1。角色 GET 使用一笔已提交合成账单；真实多账单不在该结果覆盖范围。结果记录禁止经济 POST 及外部请求均为零；这是测试客户端拦截与观测，不冒服务端拒绝验证。

实际 frontend CSS 经 HTTP 200 加载，包含 P14 scope 的 CSS SHA256 `037f6a23747676ebcb99494ae52f6d6c8e0bcbf3994c3eb66ca21334da295f6e`；截图和原始结果同目录。A 报告 HTTP 后 `ir_attachment` 内容摘要变化而计数不变，正在分类；不能将升级前后 34 表一致外推至 HTTP 之后，也不能将 bundle 技术数据变化误记为业务变化。

B 以真实 Chromium、真实 write 岗位、JS on 对 320/390/768 三视口 × 正常/native200/root200 共9例进行真实 Tab 焦点复测。新增行内锚点在3例出现焦点轮廓裁切：320 native200 轮廓 x9.13–151.14、滚动框 x24–136；768 normal x637.14–779.16、框 x24–744；两个真实测试脚本均因几何失败 exit 2。表外免单表单四控件9例横向轮廓在视口内、无横向裁切祖先。角色没有 export，因此真实 PDF 链接未出现；真实 GET 的 JS off 及其余两视口未测。截图、逐控件几何、脚本与退出事实在 `.local/p14-structure/s3-b/real-focus*.json`、`real-controls*.png`。这些证据支持真实页面限定 FAIL，不能把9例扩写为完整双引擎矩阵。

B 独立对 A 的升级后与 HTTP 后 34 表摘要核对，仅 `ir_attachment` hash 改变、109行数不变；当前九个 web/assets 附件，但逐行前像缺失，具体变化不能认定，保持 UNKNOWN，见 `assets-after.json`。B 独立只读核访问审计由旧终态73行/max id102变为105行/max id134，新32条均为 accepted 的 login、login.scope、store.switch 或 settlement.invoice_view，包含 B 两次登录及18次 GET，逐行保存在 `audit-after.json`。这些读回不等于全库保护或审计完全无变。

## 本次资源及截图

A 报告 Odoo Ctrl-C exit 0、Docker stop exit 0、浏览器 context 均关闭。C 再执行 `docker inspect --format '{{.State.Running}} {{.State.ExitCode}} {{.HostConfig.NetworkMode}}' 2007f4e0c139739dcf56f18403d177683b85319d7ee08f3d332155d14e4956f4` 得 `false 0 none`，`ss -ltn '( sport = :18631 )'` 无监听；该独立检查仅涵盖该容器与端口，未审计主机其他资源。最终 S4 应独立复核收尾。

同目录 `real-before-bf60346.png` SHA256 `0badaa3c061eb6d8c4eb0587fe2d018b84a698b4d48b6bc9d7d62280de7cdca9`、`real-write.png` SHA256 `91afdf896987eaedc609975705c1d11b7fecc241bfad6e26517b6e9fdd6409c1` 是实际普通岗位合成账单页面截图；两图来源版本、视口不同，不能作为相同条件像素级对照。没有经济 POST；原账单保留且不重放。
