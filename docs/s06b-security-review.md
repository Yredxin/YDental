# S06-B安全自查

这是Codex对固定S06-B产品及测试适配器的自查，不是GPT复核或生产批准。适用odoo-security、odoo-guidelines及static/的odoo-web-guidelines；A既有控制继续适用。本批未安装真实临床、库存、发药、结果或收费模块。

## 已逐项检查

|模式/边界|本批检查与结论|
|---|---|
|ACL/记录范围|新hold/append.permit只有YDental内部入口组的read，继承queue.record当前门店业务读范围；公共/portal/匿名无授权。普通create/write/unlink及RPC/导入不能绕过私有MUTATION。原生读取/导出仍经过S01源授权/审计及export写权限；不授予普通group写记录|
|人工追加双权限|本店frontdesk write加独立ydental_group_append，每请求重新检查。普通frontdesk、只有group但无本店write、撤掉group均拒绝；没有岗位默认追加。通过显式组复用原生授权治理，不扩成任意字段权限系统|
|sudo/身份切换|queue._model只接受服务器常量实体；所有输入ID经S05 _id及原actor/lease/current store/source关系检查。dashboard先业务读授权再读本店最小任务/工位信息。新增with_user只有固定base.user_root自动timeout审计；after仍记录真实holder。无客户端指定用户/任意模型sudo|
|SQL|新增SQL仅init的固定旧约束迁移、确定表的task/snapshot回填；不拼接用户输入。锁沿用参数化advisory和稳定mutex。实际源码确认init在BaseModel上@api.private且MRO RPC guard生效，不是公开迁移RPC。业务事实无手工commit；独立验证脚本仅提交自己创建的cursor|
|公开方法/RPC|新增业务动作全部下划线私有；唯一HTTP POST分派固定签名，额外/缺少参数拒绝。create/write是ORM保护点，unlink禁止历史删除。真实RPC测试覆盖execution/hold/permit/task、合成provider的伪造context、直接私有hook调用及客户端saved声明|
|可信保存/来源|产品external target默认False，save_before_handover默认拒绝。合成ReturnSource/ReturnPlan只能由guard下私有方法接收精确冻结类；JSON字典/context bool不能成立。save成功后才结束段/hold/文书，任何后续验证失败全部回滚，包括合成保存计数；失败不生成半后继|
|历史与患者互斥|未解决execution部分唯一、entry start终身unique、resume source唯一、hold源/患者/lease唯一、continuation source唯一、active/started permit唯一。所有历史禁止删除。restore和外检start共享患者锁；serving/verify拒绝恢复，不强撤执行。S04对未解决hold单独阻止merge，active permit只能随合法canonical任务迁移|
|会话/令牌/撤权|继承A冻结Connection、actor/session/revision/connection/tokenhash绑定和实时站点权限。新动作不能拿旧lease作跨店权限。token仍只回持有端、库只存hash；查询不需持椅，不为查询造资格；过期hold提示核实且保留actor/椅/店围栏|
|路由/CSRF|GET仅渲染页面；变更使用auth=user、POST、CSRF开启、16KiB限制和参数白名单。query_return不调用expire或写业务对象；固定锁技术版本更新不被冒充报到。失败业务savepoint回滚后由原S01 denial机制留拒绝事实|
|XSS/DOM|新增界面QWeb t-out和普通表单，JS结果textContent；无innerHTML/Markup/t-raw。原因输入不拼SQL/HTML，task ID转整数。未引入远程资源|
|附件/文件|hold和permit加入既有禁止附件来源清单；S01下载仍源鉴权，不用public/token绕过。产品无新增open、路径输入或文件下载入口；脚本仅操作受guard的本批记录目录和公开脱敏材料|
|其他危险模式|扫过with_company、动态domain、getattr/setattr、eval/exec/safe_eval、pickle、可变默认、secret ==及返回复杂对象。本批产品无相关新增风险；Connection和Admission仅服务器内部，不由公共模型方法返回。秘密比较仍A consteq|

## 真实并发与残留边界

锁序仍session→patient→supply/space→intake→queue，B没有独立反向锁序。restore撤旧position前已持有完整上游锁；许可撤销/start重验和状态同事务；共享RR锚点迫使等待旧快照有界重试。12组B及21组A真实双连接验证以backend PID/交错/提交顺序为证；模型或顺序调用不替代并发。

失效hold保留verify，不允许原token直接恢复、原actor换椅或另一人抢椅；真实现场接手/文书来源未启用时仍阻断。外检/药房只证明统一queue/actual execution互斥，不声称真实项目完成、结果、发药、医嘱或库存联调。生产心跳/超时/N未批准；C营业清队/跨日/推送/屏幕未实现。

仅全新S06-B库、合成数据。runner验证库名、端点/cluster/OID、创建记录、配置hash、独立data/log、精确dbfilter/端口及PID，cron=0、SMTP禁用、进程本地外发限制；不重配系统安全或既有服务。公开证据不含access/config/token/SID/cookie/原始日志；失败链以脱敏摘要和私有日志hash长期保留。结论限于当前实现和实测路径，不宣称穷尽未来组合。
