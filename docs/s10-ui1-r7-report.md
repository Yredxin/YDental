# S10-UI1-R7：撤权后旧 HTML 日结表单限定验收

## 身份与门禁

唯一授权是 [#34 评论 6184612591](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184612591)；R6 独立复核是 [评论 6184556009](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184556009)。开工前 API GET #23/#29/#31/#34 当前正文及全部有效评论，#35 OPEN/0，未见并行 R7 执行。原分支本地及远端固定起点 `09cbcfea575bd488e617a5f597bab3c9d9286eae`，工作树干净；core、S10/S07 service、controller/QWeb 哈希符合授权。产品、历史 R4/R5/R6 脚本、固定适配器均未修改。

CREATE 前实际 R7 `run()` 与真实事件 writer 的 Fake Playwright 全流程为 **SIMULATED_PASS**。Fake HTML5 约束验证空日期不发 POST、填有效日期才发一次；整个流程覆盖双角色隔离登录、经理一次撤权、旧页保持、原生按钮、303反馈、资金不变与完成标记。事件写入失败、fill丢失、缺表单/日期DOM、无POST、错误状态、无反馈、资金变化均使完成标记不存在。实际 `create()`/CLI 通过非空文件复制与 Fake PG 成功及失败门禁，core venv准确导入/编译通过。[强制预检 6184663377](https://github.com/Yredxin/YDental/issues/34#issuecomment-6184663377)在任何CREATE/Odoo/Firefox前发表并API逐字读回。

## 唯一真实运行

唯一只读源 R4 合成库 `ydental_s10_test_20261015033000_a4c82d17` / OID2100265，核真实OID/cluster、config/marker、92模块、0源活跃连接、150个filestore文件及附件指针、合成财务基线。一次CREATE得独立 R7 库 `ydental_s10_test_20261015060000_c1d2e3f4` / OID2100268 / 端口18276，新marker/config/filestore/dbfilter及继承数据检验通过。唯一 Odoo HTTP PID3291138 正常停止 exit0，无signal11/超时；唯一Firefox执行 exit0。没有prepare、升级、正向资金、日结、退款或PDF导出。

两个隔离会话中，front在撤权前打开旧结算页，取已有close1的真实业务日 **2026-10-15**，填入原生 `input[type=date][name=business_date][required]` 并选cash。实际浏览器读回日期值、`required=true`、`type=date`、字段`valid=true`、`form.checkValidity()=true`、invalid列表空。经理用本人合法会话把front本店结算授权write→read一次；front旧页不刷新，原revision未变，日期和form validity仍有效。

front在旧页点击原生submit按钮。Firefox只捕获**一次** `POST /ydental/settlement/action`，Content-Type `application/x-www-form-urlencoded`，operation close、output html、真实业务日、cash、CSRF/key/revision均存在。HTTP返回**303**，Location为本站 `/ydental/settlement?notice=<32位令牌>`；浏览器落回同一工作台，实际可见“请求未完成”可信反馈。随后刷新只发GET，不重复提交。原HTTP日志有一次303 POST及相应GET。该单项标 **`R7_HTML_DENIAL_LIMITED_PASS`**，不是完整UI1或S10技术PASS。

## 业务不变量与审计

失败反馈后再用只读SQL逐行比较源/目标：原生account.move5、move.line10、account.payment2、partial2，S10 receipt8、payment1、refund1、close1完全相等；继承的资金事实未改变。PDF导出审计3→3、mail.mail0→0、Bus30→30。front A settlement实际write→read，为唯一授权变化。S01 audit234→247：authorization.change+1、login+2、login.scope+2、store.switch+2（两角色初始合法切店）、settlement.invoice_view+6，共13；拒绝安全日志未冒充持久S01业务成功审计。

脱敏机器索引：[verification.json](evidence/s10-ui1-r7/verification.json)。私有marker/config、HTTP日志、浏览器事件和完成标记按SHA保全，不把凭据、notice令牌或患者资料上传。R4/R5/R6及所有更早历史库、filestore、PDF/PNG、日志/core/备份均保留。R4/R6既有通过项未重跑；>50条真实分页因无合法资料仍 **NOT_RUN**。S10完整技术/生产继续 **BLOCKED**，旧Native SIGSEGV根因UNKNOWN，S11 NOT_STARTED；等待GPT独立复核，不改Project/Issue状态、不合并、不部署。
