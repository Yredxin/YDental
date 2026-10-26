# DL-P10 有界实现与验证工具

只适用用户启用的 YD-S13-DL-P10 / 1.0。完整范围见
[实施计划](../../docs/execution/S13_DL_P10_IMPLEMENTATION_PLAN.md)，实际结果、
候选、命令/退出、原始证据和局限见 `docs/reports/s13-dl-p10/`。
工具不授予生产、经济/库存、文书/PDF/打印或其它业务操作权限。

- `runtime_config.py` 在获准私有 provider 基础上创建当前阶段的运行元数据；
  `rebind` 保留原有效期和历史字节。旧 scope/STOP/guard 不修改。
- `admission_probe.py` 核现场目标、角色、资源和代码；未实现者对当前原始结果
  独立 review 后，`bind_admission.py` 才能绑定。名称不证明 OS 隔离。
- `protected_snapshot.py`、`runtime_files.py` 读取完整既有业务/技术投影及现场
  所有附件引用、共享物理路径和实际 bytes/size/SHA；`runtime_classify.py` 只列
  离线差异事实，不自动验收。原生依赖由 `runtime_dependency_snapshot.py` 单列。
- `run_checks.py` 只在明确 clean 候选、独立当前准入、冻结与即时完整 pre 满足时
  执行限定 `ydental_reporting -u`；必须实际退出再完整 post 分类。不为 CSS、工具
  或报告重复升级。未知 native 结果保留 child 并停止受影响动作，不自动重试。
- `runtime_views.py` 读取实际主/source/error/nav/scope 双语言合成 arch 和继承。
  `runtime_components.py` 在新 RO/RR shell 中渲染原生 loaded QWeb 的 12 指标、
  空态及双向/末页共 15 个明确内存组件，逐控件族核标记/变体/图标/条件；不调用
  报表业务 query、不伪造真实身份、来源、权限或业务成功。
- `launcher.py` 管理阶段本人 owned 服务的正常 start/stop 与身份、时长、日志和
  退出；继承并保留既有安全 guard，不改 core、共享主服务或集群策略。
- `browser_checks.py/.cjs` 使用现有真实 Chromium/WebKit、正常 CSRF 认证和原表单。
  每个 client 固定 executed 源/依赖、参数、实际 wrapper/Node/native 退出、完整
  原始结果和唯一原 PNG。角色从正常私有来源读取，不在源码写凭据。
- `browser_contracts.py` 对真实 CSV 的 BOM/四头行/原 11 列、过滤、合计、源行与
  顺序/原序列化/防公式前缀完整比较；`browser_compare.py` 对完整原 JSON 只分类
  确切 `filters.query_at_utc`，保留前后原字段值。CSV、请求及完整投影不公开。
- `source_contracts.py` 只还原明确获准的呈现标记、span、SVG 调用及两个原生
  call 参数后比较完整 XML C14N；核 manifest 恰两直接依赖/末两资产、冻结文件
  原字节、原生术语提取全文顺序。PURE 不能代替实际 loaded/browser 验收。
- `viewing_package.py` 从显式选择清单复制实际原 PNG 字节及有限布局索引，按
  独占文件名构造私有只读 ZIP，不包含 CSV/PDF、原请求、DB 投影、配置、凭据、
  会话、程序或字体。必须另经未实现者逐成员/原源/解码/隐私核查。

真实读取仅原 GET 查询/分页/钻取/返回，及普通有源并有 export WRITE 的原 CSV
POST；不提交其它业务。测试层级分别列 SOURCE/PURE、loaded QWeb 内存、明确
浏览器组件、真实 HTTP/BROWSER、独立新物理 RO 事务。CSS/文本间距压力、缺样
分页和故障只属于明确组件，不注入修复 CSS 冒产品通过。

最终公开工具包含实施中普通修正。各真实 client 的实际 executed 源与私有定向
变体另逐 hash 固定，不把历史失败、旧候选、未运行模式或 UNKNOWN 改成 PASS。
不要用最终工具源码反签此前 client；本阶段窗口已收尾后复现必须形成新的真实
有效准入，不恢复旧时间、旧 scope 或 STOP，也不承诺 localhost 是远端用户入口。
