# S08-C 安全复核与边界

依据 odoo-guidelines、odoo-web-guidelines、odoo-security 对新增 ydental_print 与 C 测试/runner 审阅。运行证据和最终 PASS/FAIL 以 s08c-report.md 及 evidence/s08c 为准；这是 Codex 自测和代码复核，不能称 GPT 亲测或用户验收。

## 入口和来源

HTTP 只提供登录 GET 入口与原生 CSRF POST 动作，严格 operation 和参数签名，限制请求体。真实 request.session.sid 只在服务器侧转成 S01 Binding，页面只有 revision 与 CSRF，不接受伪 session/model/field/domain。每次来源读取均 source-read + export-write + 当前门店/公司/患者关系；预览也采用同一保守门槛。临床调用 A 原生接口；跨店读取显式目的性授权。药房窄投影要求真实本店处方、issued/done 和真实药房 task，不能取临床文字。猜 ID 或只有价格/财务岗位权限不能读取。

私有方法以 _ 开头，原生 RPC 不允许调用。job 无普通 ACL，关键字段 NO_ACCESS；普通 search/read/export/CRUD 不提供接口。写入用模块内不可从 JSON 构造的 object 能力，报告使用冻结 Python RenderScope；两个能力都不是可伪造布尔 context。原生 report action/HTML/PDF 与缓存分支均先校验真实 scope 和来源；客户端 data 不能塞任意报告值。仅 native report_type/debug=False 元参数被允许。

## sudo 与 SQL

sudo 只在服务完成当前来源/关系/岗位验证后，读取明确 source ID 的模型字段、不可变版本、真实处方行/事件，或创建/读取当前 actor×session×revision 的临时 job。初始 existence 探测不会给无权响应返回敏感内容。药房模型本来不开放全医疗 order，因此有最小受控 projection，没有扩张原生医疗 read ACL。

SQL 仅固定字面表名和参数化 ID 的事务屏障/行锁：S01 actor advisory lock、原 S01 session FOR UPDATE、session revision 值保持 UPDATE、user/membership/grant FOR NO KEY UPDATE。没有客户端 SQL/domain；不修改 revision 值、用户字段或授权。该屏障用于 repeatable-read 的真实重试，不能仅靠 advisory lock 后假设快照变新。NO KEY UPDATE 避免不必要地阻塞治疗事实的用户外键。Odoo 原生 serialization retry 保留原边界；没有增加次数或改全局隔离级别。

## 二进制、附件与渲染

PDF 使用原生 Odoo20 BinaryBytes 存数据库字段，attachment=False。ir.attachment 阻断来源集合加入 job，公共 flag/access_token/_can_return_content 也不能绕过。下载只通过重新授权的 POST 返回，固定不含患者名文件名、no-store/private/nosniff/no-referrer，没有公开分享/患者门户/GET bearer URL。

QWeb 只接静态受控模板和完整服务器物化数据，用户文本 t-out 转义；不接受用户可执行模板。原生 wkhtmltopdf 使用 UTF-8、内联样式、Noto CJK，禁 JavaScript 和 local-file-access，去除 login cookie 与 header/footer URL。所有医学输入保留来源文字，没有外链资源加载。字体检查和渲染都有超时，字段/来源/行数/事件数/字节/页数有限制。引擎 stderr、文件路径和完整临床值不返回给用户。

临时来源快照、模板号、摘要和 PDF 元数据不包含 session、token、账号凭据或病历全文作为隐藏元数据；医学正文只在显式授权文件内容里。规范化内容摘要与版本集合足以核查取数一致性，不自称永久原件。15 分钟是服务器交付期限，不是正式资料留存/删除批准。

## 浏览器与失败

预览 iframe sandbox 无脚本权限。操作期间冻结源选择，切换立即清除旧生成资格；旧版本/摘要重验，失败/响应丢失不自动重放。PDF 查看器显示真实 binary；打印按钮在用户手势预留空白窗口，服务器重新授权成功才放入所选 PDF 字节，失败关闭空窗。浏览器自身打印按钮或 Ctrl+P 打开原生对话框；只审计 print_requested，纸张 unknown。弹窗被阻止明确提示，不假称打印成功。

已经合法下载的本地文件无法远程撤回。当前入口的任何后续请求会重验撤权与版本；不能宣称撤权能销毁用户已获副本。PDF 查看器对本地字节的工具栏动作也不冒称新的服务器审计事件。

原生业务错误留安全失败审计，不复制拒绝来源 ID、全文、cookie 或 stderr。CSRF/原生 RPC 框架拒绝保留框架安全行为。PDF 操作只增加 job、S01 审计及值不变会话屏障，不生成文书版本、临床/药房/费库/容量/队列或财务事实。已发生事件不因渲染失败被撤销。

## 验证范围与剩余风险

候选提交的模型、真实 HTTP、Firefox 和独立 PostgreSQL barrier 有来源/导出、药房、跨店用途、撤权/旧 revision/换公司、原生报告/RPC/附件、并发一致快照与重复请求、无字体/超时/引擎异常、网络响应丢失的运行证据。候选测试结果各有不同 SHA，不合并成固定 test PASS。固定 test 87b2c858 在 post-tests 原生资产初始化后 SIGSEGV，tests=null；新故障 HTTP 用例、完整 A/B 回归和全新库最终链均未完成。

实际人工核对候选 16 PDF/61 页，RX-2 最大长度处方第 7 页只有页脚，第 9/10/12/13/15/16 页严重缺正文，推翻自动检查 PASS。此前 RX-1 还有文字重叠。两个问题均不得忽略；停止条件生效后没有再改产品或重跑 Odoo。代码有资源上限与原生引擎超时，但未知 SIGSEGV 不是 Python 异常可拦截的已验证故障。服务器 SIGSEGV 和分页机制根因均 UNKNOWN，安全/运行验收 BLOCKED。

正式打印资格、医学/同意书法律正文、签名和证件/监护核验、上传签署件、S12 永久原始件/原样重印、设备回执、生产性能/迁移回滚均未授权或 NOT_RUN。S07 历史 SIGSEGV、此前 Firefox crash、原生 HTTP serialization 重试耗尽和本批新 SIGSEGV 根因继续 UNKNOWN；生产 BLOCKED。
