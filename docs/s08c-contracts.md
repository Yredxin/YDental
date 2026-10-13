# S08-C 中文演示 PDF 与受控打印契约

授权为 #32 的 GPT-ACTIVATE6137113212，基线 e95b77d1ebd2ff55331e777adedf32efe81fdfbc。仅新增 ydental_print；原 S01—S08-B 产品文件保持字节不变。实际结果与固定提交见 s08c-report.md；本合同不构成正式医学、法律、用药或生产发布批准。

本次工程交付 BLOCKED：固定 test 原生 Odoo signal11；候选 RX-2 长处方可视检查也有空白/正文缺失。以下是已实现的代码契约，不能解读为全量运行通过。最新 corrupt PDF/QWeb 错误处理未完成固定测试验证。

## 三类来源与动作

病历只选择一个明确的 ydental.clinical.document 和 ydental.clinical.version.number。历史文字来自不可变 version.content；当前责任人、当前状态和版本也明示。D1 与 D2 分别选择、分别生成，全部页面提示这不是完整正式病历。草稿、待完善、文字已确认（非正式医学签署）相互区分。空值不推断正常或医学结论。

处方从真实 prescription order/line 读取。所有取消的旧草稿行仍列示，取消原因保留；draft 和 cancelled 行没有当前待领资格，待领量为 0。issued/done 行的实际已发量来自真实 prescription event.quantity 合计，待领量为原开立量减去真实发生量。pending 事实仍是已发生的发药事实，核对状态单列，不能因为未补账而假装尚未发药。退药不重开领取量。SKU 规格、原生单位、用法、频次、疗程均来自真实字段，不自动填医学值。费用快照只列来源 ID，绝非实收、收据或发票。

同意书只关联可合法审阅的独立临床来源版本和患者/门店身份。医学内容、风险和替代方案、说明问答、患者决定、患者/医师/监护人签署及日期核验栏都保留空白，仅有“待补全和审核”占位。状态始终演示、待审核、未签署。不会从病历复制医学结论，也不承接其它门店的假签署。

GET /ydental/print 是选择入口。POST /ydental/print/action 使用原生 CSRF，支持 preview、generate、pdf_view、download、print_request，参数签名严格固定，拒绝任意 model/field/domain。预览生成静态 QWeb HTML；后三种交付操作返回真正 application/pdf。下载名固定 ydental-demonstration.pdf；响应 no-store/private/max-age=0、nosniff、no-referrer，不生成公开附件 URL。

## 权限与版本

每次预览、生成、查看、下载、打印请求均要求 S01 活跃内部用户、真实 session/revision、当前门店/公司和患者关系、source-read 加 export-write。这是首版演示文书的保守门槛，独立单份正式 print 权政策未发布；不扩大岗位权限。

医疗角色通过 A 原生读取接口检查。跨店病历必须有 S01 的真实用途（diagnosis/history_review）及本店患者关系，不能仅猜 ID。药房角色只可读取本店 issued/done 处方且该处方具有真实本店药房任务；投影只含处方和实发必要字段，不能读病历或同意书。price/billing/报表权限不授予医疗来源。

报告层要求 Python 冻结 RenderScope，绑定 actor/session/revision/type/source/version/purpose 和规范化内容摘要。JSON 假 context 不能构造该实例。原生 report HTML/PDF 路由、RPC、job read/export/CRUD 和 ir.attachment/public/access_token 均不能替代受控入口。临时 PDF 二进制使用 Odoo20 BinaryBytes 存在 job 数据库字段，attachment=False、NO_ACCESS、没有普通 ACL，不建立另一套病历或业务账本。

同一事务先完整物化来源 JSON、版本集合和 SHA256，再用原生报告栈渲染。PostgreSQL repeatable-read 保证渲染过程中另一医生已提交的改版不会混入半份内容。生成前摘要不符拒绝。下载/查看/打印再次取当前来源摘要；任何来源状态、版本、姓名/责任人或真实发药集合改变，旧临时副本拒绝，要求重新核对生成。旧不可变文字版本仍可重新选择生成，但不是正式原版重印。

S01 actor advisory lock、session 行锁与值保持的 session UPDATE 屏障使等待的重复请求在 PostgreSQL 检出旧快照后由 Odoo 原生事务重试；不改变 session.revision 的值。授权行使用 FOR NO KEY UPDATE，检测等待期间已提交的撤权，同时允许业务事实外键校验。没有自定义 HTTP 重试次数或修改核心隔离级别。相同 generation key 在同一登录版本只产生一个 job。

## 原生引擎与边界

锁定 Odoo20 的 ir.actions.report + base_report_wkhtmltox，qweb-pdf-wkhtmltopdf，A4 中文内联 QWeb。复用现有 patched Qt wkhtmltopdf 和 Noto Sans CJK SC 字体；运行前校验实际 fc-match。明确 UTF-8，禁止 JavaScript、外部资源模板和任意本地文件读取，不传登录 cookie 或 HTML header/footer URL。原生页脚带页码。单字段沿用 A 的 10,000 字符约束、规范化来源 400KB、最多 100 行/500 实发事件、PDF 10MB/80 页、引擎超时 30 秒（字体检查 5 秒）。所有输入文本 t-out 转义，不允许用户模板/表达式。

job 的对外交付有效期 15 分钟，记录与审计留存用于开发取证，没有正式长期原件保管或清理政策；内部保存不承诺永久正式归档。已合法交付到本地的字节无法远程收回；服务器后续交付仍重验，不能声称撤权可删除用户已下载文件。浏览器 PDF 查看器的本地打印行为不等于新的服务器请求；受控页面按钮每次重新授权并记录 print_requested。

## 审计和副作用

S01 print.view、print.generate/generate_repeat、print.pdf_view、print.download、print.print_requested 分别留痕：operator、store、source/type、version_set、template、摘要及 job。失败记 denied，failure_kind 区分权限与请求/引擎；不记录全文或凭据。纸张状态永远 unknown，不记 paper_printed。浏览器断网/响应丢失显示未确认，不自动重放，不标生成/出纸成功。

浏览器请求 45 秒 AbortController 超时；离线事件中止当前请求并清除旧生成资格，重新上线只恢复人工核对入口，不自动重放。服务端 30 秒引擎超时与浏览器超时分别约束两端，客户端中止不能证明服务端没有已提交 job，应人工重核对。原生异常包装和 corrupt binary 拒绝已提交，但新增真实 HTTP 故障测试因 SIGSEGV 未运行，不能称验证完成。

PDF 操作不确认病历、不保存新文书版本、不造医嘱、治疗、发药、fee、price snapshot、stock move/quant、queue/task、容量或款项。失败不能撤回已发生事实。只增加临时文件元数据和审计，以及值不变的登录事务屏障。

正式模板发布、医学/法律审核、可靠签章和证件/监护人核验、上传签署件、永久原件快照与原样重印、打印设备回执、S09/S10/S12/S13、生产迁移回滚与性能/稳定性批准均未在本批实施。
