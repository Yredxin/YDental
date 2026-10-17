# R1.1 缺陷闭环（不将静态风险伪称运行复现）

## GPR-01 / 原生异常实际RPC身份

来源：GPT正式6232783106，用户直接并入R1.1。分类STATIC_INTERFACE_RISK；原R1.0拟以继承原异常保持兼容不足，固定serialize_exception使用真实module/class/name，web registry精确匹配。修正：原生实例factory附加白名单diagnostic_code，不使用context、不改core/registry。实际RPC name/arguments、公开消息/翻译/界面/403/409/303的运行证据待test候选，不以静态检查替代。

## LC2-STATIC-01 / 可选诊断context失败影响业务

独立acceptance预审：bind_context/update_context/reset_context的字段验证若直接抛错，可改变业务。developer将验证/存储故障隔离为固定stderr/失败marker，主控在下一派发前暂停相关写入；强制S01审计create失败仍原样传播。属于候选写作期静态修正，未派发业务，不是已观察业务事故。对应LOG06/09；离线与实际框架验证待补。

## LC2-STATIC-02 / 首异常与secondary顺序

acceptance预审发现可选stack序列化不能先于最简primary保存。developer改为最简ASCII primary→结构化事件→可选stack，secondary通过root_event_id关联，不使用失败serializer递归。对应LOG04/07；故障注入证据待补。

## LC2-STATIC-03 / 未可信客户端关联标签

root审查：regex合法不意味着header非秘密。developer改case固定白名单、operation hint不可逆重新绑定、trace/request服务端生成。未知case显式null。对应LOG02/09，合成秘密/注入和真实关联测试待补。

## LC2-STATIC-04 / 线程序号与落盘次序

root审查：序号分配后释放锁再emit，可能seq2先落盘seq1后落盘，严格校验器将误报序号缺口。已派developer修为仅单条日志分配与emit同序列锁，不跨业务操作。待交接及真实多线程helper+validator验证。对应LOG02/10；不是资金并发运行结果。

## LC2-OBSERVATION-01 / 原既有Odoo服务检查补充

START最初按comm筛未见名odoo，观察范围不足。后续仅查/proc前3路径参数发现原既有PID42433 python3.12/odoo-bin，cwd上级code；AGENTS历史同PID，必须保护，不是本包启动或新执行者。未向其发HTTP/未停止修改。最终交付更正初筛表述，不据此争用端口或环境。

## LC2-STATIC-05 / HTTP默认证据过量保存

acceptance在任何真实网络派发前发现初稿即便私有0600仍保存cookie/CSRF/token或整payload过量。developer改为秘密仅RAM，默认白名单摘要+原字节SHA；只有适用C二进制和D六项最小retry manifest显式封存。11 fake/privacy测试通过；此时真实HTTP0，不称观察到泄漏。

## LC2-STATIC-06 / CREATE身份与Odoo filestore格式

静态审查补源OID即时校验、源无活动连接、保存CREATE intent失败即禁止dispatch、维护总180s等guard。198旧文件包含99 content+99 checklist零字节marker，后者核合法目录/空文件及原有效SHA索引，非错误要求内容地址等于SHA1(empty)。冻结candidate2前修完；非CREATE运行失败。

## LC2-FIXTURE-01 / HTTP retry manifest断言层级

首次HTTP fake11测试有一项断言把wrapper.payload当顶层字段；修正测试读取层级后11项全过。保守计初次执行后的修复cycle1/2，剩1；静态预审修正不计实际失败循环。首失败tool output chunk511eb0保留，但当时没有本地raw字节文件，不能补造原始SHA。缺口由offline-http-fixture-defect.json明示；这不是实际RPC/浏览器PASS。

## LC2-PRECONDITION-D01 / 合法新来源触旧全局queue过期处理

详见d-admission-blocked.md。三旧active lease/execution servicing在新基线已存在；合法S05/S06新来源入口必全局expire，违本包旧临床保全。D六TC明确NOT_RUN/PRECONDITION_BLOCKED，未派发任何经济动作，不记普通repaircycle、不冒称产品bug已修。安全A/B/C/E继续。

## LC2-STATIC-07 / 原生RPC日志入口覆盖

tester在应用派发前发现B/C真实RPC通过既有YDentalDataSet.call_kw/call_button，不经过S10路由，因此初product32cb只能证明外部case/operation/time间接关联，不能宣称RPC端到端trace覆盖。主控派developer最小在这两个已有override加入observed_http并把已有binding revision传primitive context；不增路由、权限、参数/返回、序列化、审计或查询。独立acceptance审核后冻结新product再测，属于包内LOG02覆盖修正，不是已发生实际RPC失败。

## LC2-STATIC-08 / 诊断结束观测与固定core显式shutdown

真实app初实现没有自动run.start/end，而validator默认缺end=INVALID。独立验收核固定server.py::ThreadedServer.stop先logging.shutdown，故仅atexit的初稿不能完成尾事件，未准出未冻结。最小修正为专属PidFileHandler.lock与序列锁共享RLock，close封存前记录一次DIAGNOSTIC_CLOSING/NOT_OBSERVED，atexit仅fallback，PID集合防重复；不改core、root handler、factory或业务事务。实际exit/signals仍只看父证据。

## LC2-OFFLINE-02 / 新生命周期候选两项失败及最后修复循环

新离线tools30项出现2FAIL，原raw保存在.local/s10-lc2-exec-20261017/offline-candidate3-tools，parent exit1；尚无Odoo/HTTP/Firefox/资金动作。序号实际属于全PID，而完整性结束事件应属于(run_id,pid)，原校验键混淆；未绑定请求行也需继承已知launch白名单run标签，仍无case/trace/request且context_missing=True，不伪造请求身份。最后cycle2/2统一修正产品、validator及真实语义断言，并补显式shutdown/并发关闭/primary保存失败仍cleanup/action角色边界等静态闭环。最后回归前由主控先冻结product/test提交；若仍有普通失败无第三轮额度，具体结果另列，不预先写PASS。

## LC2-RUNTIME-03 / 首scratch实际缺既有依赖路径（未修复）

固定product b5d3039/test fe3a46e，Odoo1060827 exit255/signalNone。首链PackageNotFoundError→MissingDependency phonenumbers；launcher.environment将PYTHONPATH覆盖为scripts而漏已有.local/s04-deps（实际phonenumbers及9.0.16.dist-info均存在），是准入配置缺陷，不需新装包。5框架/真实RPC/UI均NOT_RUN，非GPR产品FAIL。两次修复循环已耗尽，不修改后重跑、不换main入口绕过、不安装/改venv、不重建scratch。scratch独立RO证实base已安装/702模块，不称全DB回滚；main全保全。后续推荐仅补受控既有path并以实际child环境metadata+import预检、确认同scratch部分安装的重入条件，再新明确有界授权/固定候选运行；不借本包未耗Odoo额度继续。

## 证据与未运行草稿缺口

首HTTP fixture失败无本地raw，第二次30项2fail无当时源SHA，均明确保留证据不足，不以事后SHA补造。最终51回归绑定真实b5d3039/fe3a46e源manifest。Browser草稿未准出、五类问题未修未跑，原字节保全unrun-browser-draft.json，不进入已提交执行candidate。
