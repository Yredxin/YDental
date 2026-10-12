# S08-A 终态操作竞态定向修正报告

**状态：BLOCKED，未完成新的固定test全量回归，不申请判技术PASS。** 前端定向修正完成，基线真实复现三类竞态；修正后的Firefox调试回放88项/21图/10个响应屏障、pageerror0通过。随后全新候选库两次因PostgreSQL无法分配32MiB共享内存安装失败。停止数据库重跑，完整保留代码、失败和调试证据。所有运行均Codex自测，不是GPT亲测或用户验收。

唯一返工依据为[#32 GPT-REVIEW6123972548](https://github.com/Yredxin/YDental/issues/32#issuecomment-6123972548)。开工及交付前完整读取#23/#32正文、全部有效评论；原正文和2/4条评论均无变化。本轮Project零mutation，#32保持S08/进行中/Todo/OPEN。原S07、原S08-A及全部历史证据保留。

|固定节点|完整SHA及含义|
|---|---|
|返工baseline|`f0f17e633a3421386d0a0bdf2b63a5f9709bde96`|
|rework product|`a28b364691791214becf4909e9ecf1bc0be3555c`|
|rework test|`e8b2247609e51d7fbe268b94082e8fd3259db9d3`；最终运行环境阻塞，非通过版本|
|rework final|仅AGENTS/文档/脱敏证据，完整SHA固定于#32本次交付评论|
|原分支|`codex/s08-a-clinical-doc-r1-20261012`，沿用原链，不强推/合并|

baseline→product产品增量仅document.js、原QWeb模板、zh_CN PO。product→test只验证脚本；test→final只文档/证据/AGENTS。中间提交未删除。无Python产品、模型字段、ACL、S06事务、文书版本/独占、D1/D2责任规则修改；原[字典](s08a-data-dictionary.md)和[契约](s08a-contracts.md)继续适用，新增[浏览器状态契约](s08a-rework-contracts.md)。

## 复现及最小修正

在修改产品之前，以baseline在本轮新库`ydental_s08a_test_20261012121209_305ee956`完成install30及真实Firefox复现。对confirm、correct、handover真实发送POST，取得服务器响应但暂不交给页面；期间仍能输入主诉、病史及37/M。放行后，服务器仅保存发送时A，本地B/37不存在于该版本。原代码有通用beforeunload警告；本轮明确接受该警告以核查结果，**不宣称完全没有浏览器提示**。原页没有临床提交范围/已交还状态说明和本地保留核对出口。[复现JSON及17张原图](evidence/s08a-rework/reproduction-attempts/20261012T121443344394/result.json)，其中六张终态前后图逐张核验。

修正为终态请求及必要release完成前同步冻结七个文本框、52牙位按钮、无对应牙位、牙面、牙位状态、更正原因及相关动作。普通save仍允许新输入，成功后按generation和完整内容快照继续追赶。

终态返回及release后双重比较generation/完整内容；发现程序输入或无input事件DOM修改，保留本地可复制文字、禁止重复提交、不自动离开，并在新标签页核对受权限保护的服务器文书。明确区分已提交和结果不明；交还成功提示“交还已提交，不能在本页撤销”。网络丢响应、未发出请求、409均不假成功、不自动重放。较早发出的心跳错误不能覆盖待核对说明。新增提示使用textContent、固定同源数值ID和noopener/noreferrer，无正文/token入URL或新增持久存储。

## Firefox实际延迟验证（调试通过，非最终全量通过）

实际提交`1bec52a970f497a1c01d5be98f1e4919bcd907d1`，本轮新建调试库`ydental_s08a_test_20261012123045_d399a600`，端口18162；完整产品树与固定product相同。该库安装/升级/16组probe在较早`a0014c5`执行，后续仅新增调试合成前提，未重置或删除原失败行，**不能把跨提交结果合成最终PASS**。

[实际Firefox结果88项/21图/pageerror0](evidence/s08a/browser-attempts/20261012T124510748577/result.json)，全部21图已逐张目视核对。用Playwright实际Firefox路由屏障控制真实POST响应；既有受保护原生RPC只读最新JSON/版本，GET新标签页实际验证核对出口，没有新增产品read接口或临床替身。

|实际屏障场景|实际结果|
|---|---|
|普通save请求期间继续文本、牙位输入|最终服务器追赶最新内容、版本3；[图12](evidence/s08a/browser-attempts/20261012T124510748577/12-ordinary-inflight-autosave-catchup.png)|
|confirm/correct/handover响应前物理键鼠尝试修改文本、FDI/状态/牙面|全部控件冻结，服务器完整JSON与提交快照相同；[图13](evidence/s08a/browser-attempts/20261012T124510748577/13-confirm-all-inputs-locked.png)、[图14](evidence/s08a/browser-attempts/20261012T124510748577/14-correct-all-inputs-locked.png)、[图16](evidence/s08a/browser-attempts/20261012T124510748577/16-handover-all-inputs-locked.png)|
|correct/confirm期间强制input及handover期间无事件DOM变化|A已提交，B原页保留、未同步提示、无导航；已交还明确不可撤销；[图15](evidence/s08a/browser-attempts/20261012T124510748577/15-correct-forced-input-retained.png)、[图17](evidence/s08a/browser-attempts/20261012T124510748577/17-confirm-forced-input-retained.png)、[图18](evidence/s08a/browser-attempts/20261012T124510748577/18-handover-committed-unsent-retained.png)|
|correct实际提交后丢响应/请求未发出/真实409|三个场景分别核对实际版本是否增长；保留本地、无重试/假成功；[图19](evidence/s08a/browser-attempts/20261012T124510748577/19-response-lost-reconcile.png)、[图20](evidence/s08a/browser-attempts/20261012T124510748577/20-request-not-sent-reconcile.png)、[图21](evidence/s08a/browser-attempts/20261012T124510748577/21-stale-version-reconcile.png)|
|真实D1待完善/责任转派/D2交还唯一续诊/D3合法新接诊|保留原作者及版本；D1确认不确认D2；B按附原因更正规则补记，不重新占椅、不伪撤销交还|

10个屏障的响应状态/真实发送/延迟秒数/是否丢响应/是否导航逐条记录在结果JSON。新增浏览器时序无需新增后端事务测试；原21模型和7HTTP测试原样保留。不同提交的运行详见[失败链](evidence/s08a-rework/failure-chain.md)和[执行历史](evidence/s08a-rework/execution-history.json)。

## 新固定test回归：BLOCKED

最终候选库`ydental_s08a_test_20261012125922_18e705b1`，端口18165、OID1130035；端点127.0.0.1:5432，cluster7694897083368259627。runner创建marker、config SHA/dbfilter/data_dir/PID及外发guard继续；命令`../.venv/bin/python scripts/s08a.py install --db ydental_s08a_test_20261012125922_18e705b1 --port 18165`，测试提交e8b2247，退出255，tests=null。

先前候选`ydental_s08a_test_20261012125331_e66dbaaf`在上游建表出现`psycopg2.errors.DiskFull: could not resize shared memory segment to 33554432 bytes: No space left on device`。仅尝试为本轮子进程libpq设置串行查询/维护和16MiB维护内存，无ALTER SYSTEM/DATABASE、服务重启或系统安装；最终候选仍在base建表失败。probe/audit中的实际SHOW设置断言尚未到达，不能称设置已验证或环境根因已解决。主机/dev/shm空闲不代表PostgreSQL端点namespace资源可用。两次均正常退出255，非SIGSEGV，无本轮原生崩溃记录。[脱敏错误及日志hash](evidence/s08a-rework/environment-blocker.json)。停止继续重跑，不改既有服务/核心/依赖来排除。

|适用验证|本轮中间实际证据|最终固定test e8b2247|
|---|---|---|
|全新安装、升级；21模型+7HTTP/RPC|d717/a001/1bec各install30/upgrade28通过；install额外2原生资产初始化|install FAIL255；模型/HTTP/upgrade NOT_RUN|
|原16组真实双连接|d717/a001各16通过；1bec候选仅7组后AssertionError退出1，deadlock0；原位置未保留，根因未确认|probe NOT_RUN；初始PID轨迹修正未获最终验证|
|Firefox延迟、普通自动保存、S06交还续诊|1bec调试88/21/pageerror0及10屏障通过|Firefox NOT_RUN|
|中文实际导出|3246877实际151项但missing1/metadata1失败；后修整块PO，1bec浏览器中文提示通过|export/151项全量翻译 NOT_RUN|
|权限、附件/RPC/导出、CAS及审计|中间模型/HTTP负向通过，浏览器医疗只读拒绝；d717/a001/1bec候选各单次8SQL全0|完整权限/审计回归 NOT_RUN|
|真实持久业务再升级、10组行签名|本轮未完成，不移用原交付签名|NOT_RUN|
|纯文书前后6组经济签名|中间模型含零经济副作用断言；未完成本轮浏览器前后比较|NOT_RUN|
|guard5|固定e8b2247五项通过|PASS5|
|安全|固定e8b2247完整clinical addon静态扫描、自审无新增发现|静态审查完成；运行时安全BLOCKED|

[最终逐项状态](evidence/s08a-rework/final-tests.json)、[S08-T01—T16适用矩阵](evidence/s08a-rework/tc-matrix.json)、[28项原测试索引](evidence/s08a-rework/test-methods.json)、[安全自审](s08a-rework-security-review.md)。矩阵内A适用项统一BLOCKED；B/C等未授权项NOT_RUN。没有引用原be5f28e的PASS代替本轮。

## 保护、回滚和未完成范围

Ubuntu/Odoo20核心SHA`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、核心tracked diff不变。仅本轮六个全新隔离合成库，未删/改历史或业务库、odoo-12、既有服务、系统依赖。预览均只SIGTERM本次config/PID精确匹配进程，runner退出0；无剩余本轮预览PID。仓库只合成截图、脱敏JSON和hash；原日志、凭据/config/access受本地run目录保护，不上传。

回滚说明仅供复核：产品增量没有数据库迁移；若另行授权撤回，正常revert上述三个产品文件的返工差异即可，保留所有服务器历史版本/交还/续诊事实和证据。当前未执行回滚，不能以源码回滚撤销已提交临床事务；不重置/删除数据库、不强推。

待完成的是新的固定test全新库完整安装升级、16组竞争、Firefox及翻译/权限/审计/10+6签名回归；需先处理PostgreSQL端点共享内存环境阻塞。本轮未擅自扩大到服务或系统排障。原探针失败根因和环境根因均未确认；本地未同步内容只在原页保留，用户明确关闭/丢弃或OS崩溃不保证恢复。

S08-B真实治疗执行/费用/耗材/药房4+2、S08-C PDF打印、S09—S13、生产参数/50会话/生产部署均NOT_RUN。S07历史SIGSEGV根因未知，正式生产部署继续BLOCKED。#32不关闭、不改Project/workflow、不合并；本次交付评论逐字读回后停止等待GPT再次独立复核及阻塞裁定。
