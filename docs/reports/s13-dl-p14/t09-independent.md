# P14-T09 F2 C 独立证据复核（过程时点）

2026-10-29，复核者未参与产品实现或测试夹具生成。此记录是现场证据复核，不签 T09 通过；数据准备团队仍在运行，最终读回与停机以其后实际证据为准。

## 产品与 F0/F1

`git diff --exit-code 39038bd bf60346 -- ydental_settlement`、`git diff --check 39038bd HEAD` 均 exit 0；当前 HEAD `bf60346604a54a442eb39ddf2af63d9626961be5`，工作树未见产品文件修改。该对比证明续办时产品文件与固定 P14 产品一致；不是对运行数据库或历史数据的全量检查。scratch 安装工作树 `rev-parse HEAD` 为 `bf60346`，故实际 HTTP 使用的产品树对应原产品；提交本身不同。

F0 A 的 Chromium 定向对照、F0 B 的 WebKit 768 记录和 F1 D 两种方案证据在 `.local/dl-p14-t09/{f0-a,f0-b,f1-d}/`；二者均为同合成内容、简化外壳，不是同一历史数据库的真实岗位页面。WebKit 对照记录基线控件和轮廓在框内、P14 候选金额和原因输入 x=529–767 而框右侧744，轮廓右缘773。此夹具支持 P14 样式引入768焦点裁切的限定判断。Chromium 320 native200 中基线输入164px而滚动框112px，候选输入更宽；320/390 root200 候选比基线明显恶化。保持焦点的鼠标横滚不代替 Tab 自动可见；宽于框的控件不能通过横滚同时露出两端。

F0 A 随后以 `build-baseline.py` 从 `f9c4778` 源模板提取基线、复制同合成值并重建 `baseline.html`；但其 `results.json` 顶层 `layer` 仍误写为“剥离装饰”的旧标签。保留这个工具元数据错误，实际来源须结合该构建脚本、构建日志与 HTML 判断；两者均不是真实基线岗位 GET。F0 B 初构建缺少 cssselect 失败，改 XPath 后成功；不能把操作失败列为产品 BUG。

F1 两个 CSS 探针没有修改产品：sticky 末列在 320 native200 聚焦期间遮挡整个可见滚动框；RTL 滚动方案在用户横滚后再次 Tab 仍裁切并改变初始滚动方向。均不满足本计划，未采纳。连续失败后停止该方向，原 7f2c455 撤回证据仍保留。

## F2 浏览器与真实加载

F2 A Chromium 使用已加载 QWeb 的合成片段和本地 CSS，5视口、三缩放、JS on/off 共30场景；基础脚本 exit 0 只表示基础断言，逐控件几何显示其中 8 个场景的四个焦点轮廓横向裁切。F2 B WebKit 同类层级共30场景：独立解析 `focus-results.json` 得 18 场景至少一个轮廓水平超出滚动框；`focus.cjs` exit 2 反映几何断言失败。其共20严格失败包含垂直瞬时越界；页面允许纵向滚动，不将这20个全部认定为不可达。两个测试均非完整 Odoo 外壳，也未覆盖 P12/P13/pay/refund/close 浏览器回归。T09 仍 FAIL。

本角色只读 `.local/p14-t09/real-get-base-01/http-{read,invoice,formdata}-result.json`：该团队记录正常收费岗位登录与切店、空态和合成已过账账单 GET 各 HTTP 200；未付清表为五列、waive 一个、原字段及带 submitter 的内存 FormData 顺序存在，reason 300字、金额12.34。前端 CSS HTTP 200、582669 bytes、SHA256 `8a43f4804fa994023f8262f56a8d74b6d724ddd0b5d44c4962bdeb94fe5c1fe1`，含 P14 scope。请求记录包括正常认证和切店 POST，`forbidden` 和 `external` 为空；并非无任何 POST，也不能从客户端记录单独证明数据库全局无经济操作。结果所用数据是新 scratch 合成账单及一个收费岗位，不等于真实患者、资金或所有岗位权限。独立持久读回和只读岗位 GET 以团队后续实际证据为准。

## 资源及保护范围

本角色执行只读 `docker inspect`，在复核时刻容器 `2007f4e0c139...` 为 Running=true、network none；`ss` 显示 `127.0.0.1:18631` 正在监听。安装器早先的 stop 回执仅为安装时点，不能作为此次最终停机证明。未停止或干扰正在运行的资源。

没有本轮受保护历史库的独立前后物理快照；不推断全库零变化。新 scratch 来源、经济对象与待办的实际前后读取须依据后续证据，既往缺失前像不补造。本角色未访问凭据、连接数据库、提交业务或修改产品。

## 追加：最终只读证据和资源核对

准备团队完成后，本角色不重启资源，以已保存结果作独立只读核对。`http-reader-result.json` 记录普通只读岗位对同一合成 patient2 的 GET 200、五列、仅供查阅、无 waive；不代表其他岗位或真实患者。`bill-receipt.json` 记录新 scratch 的 event1、fee1、patient2、invoice1、store1、posted 100/余额100；团队的私有 `.local/p14-t09/real-get-base-01/f2-result.md` 记有另连接核对来源和 0 payment/refund/close，本角色未自行连接数据库，不把读取该回执写作自己独立数据库读回。

`cmp` 确认 `before-reader-get.json` 和 `after-reader-get.json` 字节一致，二者 SHA256 均 `176da7a581e4fb3c05b30dfd92e8feab69f464a4550317f00330e56a3d81584d`；各覆盖34张列明的账务、结算、库存、临床、治疗与附件表。该比较只包围只读岗位 GET，不覆盖此前建账和写岗位读取，且不包含所有审计表、历史库或文件系统内容。它不证明全库零变化，也不补历史前像。

最终只读 `docker inspect` 对相同本次容器返回 Running=false、ExitCode=0、network=none；`ss` 显示本次端口18631无监听。浏览器关闭以测试运行记录为据，本角色未独立核实所有浏览器进程。结论仍为 PARTIAL，T09 FAIL；不得以本次真实加载、权限或限定保护证据覆盖失败。

## 再次重启后的相邻区域限定复核

准备团队为真实相邻区域 GET 重新启动同一 scratch 后已报告收尾；本角色再次只读 `docker inspect` 确认容器 Running=false、ExitCode=0、network=none，端口18631无监听。`http-adjacent-result.json` 记录普通写岗位 GET 200：P12 查询和三费用区存在；pay 展开后的字段顺序和打开 close 时 pay 的原生收起行为已观测。合成测试数据没有未出账费用，P13 bill 面板按条件不存在；没有付款/退款对象，退款办理分支未测。这是有限 HTTP DOM 检查，不代 P12 A04 或完整 P13 回归。

本角色对 `before-adjacent-get.json` 和 `after-adjacent-get.json` 执行 `cmp`，两份 34 表汇总字节相同、SHA256 均 `176da7a581e4fb3c05b30dfd92e8feab69f464a4550317f00330e56a3d81584d`。该范围只包围此 GET；认证和访问审计不在34表。准备团队报告本次审计69→73并分类四条新增正常访问事件，本角色仅阅读其报告，未独立查询数据库或取得独立审计原始快照。首次容器启动后 socket 未就绪导致快照命令失败，待就绪后成功，为工具时序错误。历史库、其他表、附件实际文件以及更早时点仍不能由此比较推断为无变化。
