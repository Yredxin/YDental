# P14-T09 / 1.0 定向续办结果：PARTIAL

2026-10-29。T09 仍为 **FAIL**；没有满足约束的可靠修复，本轮没有修改产品代码。固定产品 `39038bd8b84ef00fe46dc37973e05a0e46d12796`；真实运行的报告 HEAD `bf60346604a54a442eb39ddf2af63d9626961be5` 的结算产品树与其一致。原 P14 PARTIAL、原报告及已撤回 `7f2c455` 证据保留；#37 OPEN，不启 P15、不合并、不部署。

## F0：同内容定位

Chromium 和 WebKit 以相同合成内容、共同简化外壳比较 P14 前模板和 P14 已加载 QWeb 片段，非历史库真实页面。WebKit 768×1024 正常缩放，基线输入轮廓在框内，候选 amount/reason 右边 767px、滚动框右边744px，轮廓超出29px；此夹具显示 P14 引入裁切。Chromium 320 原生200% 基线和候选输入均宽于滚动框，属于基线已有物理约束；320/390 root200 候选相较基线加重。鼠标横向滚轮可保持 activeElement，但控件宽于可视区域时不能完整同时显示，不能替代键盘 Tab 可见。JS on/off 相同。原数据、祖先、scrollLeft、outline 和截图分别在 `.local/dl-p14-t09/f0-a/` 与 `f0-b/`；F0 A 结果元数据保留旧 stripped 标签，实际基线由 `f9c4778` XML 源脚本构造，详见[独立复核](t09-independent.md)。

## F1：定向修复探针

- 在焦点期间固定末列并适配面板宽度可改善聚焦几何，但 320 原生200% 下末列遮住整个可见滚动框，无法同时阅读应收余额，不采纳。
- 滚动框 RTL、表格 LTR 可改善初始位置，但滚动后再 Tab 在 WebKit 768 仍裁切，且改变初始位置及横滚方向，不采纳。

两方向分别有具体假设、真实浏览器几何、截图和结果，均未写产品；连续失败后停止，不添加盲目补丁。证据 `.local/dl-p14-t09/f1-d/`。

## F2：回归及真实加载

- 最终产品树的 loaded QWeb 合成组件、简化外壳在 Chromium 与 WebKit 各执行 5视口 × 3缩放 × JS on/off。Chromium 8/30 场景焦点轮廓水平裁切；WebKit 18/30 场景至少一控件水平裁切。WebKit 另有视口垂直瞬时越界，按正常纵滚可达原则单列，不全部视作失败。实际键盘、字段、FormData 和长文本记录见 `.local/dl-p14-t09/f2-a/`、`f2-b/`；简化外壳不能冒真实页面全矩阵。
- 新隔离 scratch 首次安装，network none、Unix socket；正常来源产生并单次提交合成治疗 event1、fee1 和原生已过账账单1（100、余额100），来源、患者和门店由新只读连接核实。该新对象不得重放。真实 write 岗位正常登录切店 GET 200，五列和 waive 表单可见；真实 read 岗位 GET 200、只读文字可见、waive 表单不存在。真实 frontend CSS HTTP 200，SHA256 `8a43f4804fa994023f8262f56a8d74b6d724ddd0b5d44c4962bdeb94fe5c1fe1`。真实页浏览器内 FormData 含原 token 字段、operation、invoice_id、amount、reason，未发出经济 POST；拦截限制不冒服务器权限拒绝。
- 实际岗位 GET 有限相邻回归：P12 查询和三个费用区存在，当前均空；pay 与 close 展开及同名 details 折叠通过。P13 带未出账费用、退款办理等分支未测，P12 A04 历史失败未改写。
- 只读岗位及相邻 GET 各自前后，独立只读事务核对34张业务及附件表全行摘要不变（SHA `176da7a581e4fb3c05b30dfd92e8feab69f464a4550317f00330e56a3d81584d`）。相邻 GET 访问审计 69→73，新增正常登录、scope、切店及账单查看各1。此保护范围不覆盖初始化、全部表或历史库；过去缺失的 P14 历史前像仍 UNKNOWN。无 waive/pay/refund/close POST，不推断全库零变化。
- 合成账单首次准备缺 heartbeat 失败，独立核无该事务提交后补齐配置重试；首次快照因关联表无 id、首次启动快照因 socket 未就绪、系统 Python 缺 psycopg2 均为工具或环境错误，修正与原日志保留。真实新账单提交后独立读回，不重放。

本次 Odoo、浏览器及独立数据库容器已停止；未实现者再次核容器停止和端口释放。完整命令、退出码、数据库身份和限制见 `.local/p14-t09/real-get-base-01/f2-result.md` 与[独立复核](t09-independent.md)。真实岗位页面的五视口、两引擎全矩阵仍未执行，P13 有数据和退款分支、历史保护仍 UNKNOWN/NOT_RUN。由于 T09 明确 FAIL，P14 不能升级为限定技术完成。
