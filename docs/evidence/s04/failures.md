# S04 尝试链与修正

全部使用本次新建S04隔离库及合成材料，保留原库、私有日志SHA及提交；不导出原始日志或浏览器凭据。完整实际退出码/测试数见runtime-history.json；tests数组依次为failed/errors/total。

|阶段/固定提交|结果与原因|修正/补交|
|---|---|---|
|fc524c75，库25fd1393初装|exit255，原生CSV model_id解析需要/id列，未执行测试|8088935改实际核心适用model_id/id，保留初装失败|
|8088935，库e6afadad初装|5 failed/2 errors/28；测试把空AbstractModel视为False，phone空值False预期、removed datas字段、空JSON required及HTTP状态预期不符|b03908d修测试真实API与前提，未掩盖权限缺口|
|b03908d，库e6afadad升级|1 failed/0 errors/26；sudo缓存后的attachment.read未重新鉴权|655437a增加附件read/fetch源检查；升级26/26 PASS|
|3f2dad9，库e6afadad探针|exit1；反向申请测试key与原申请key相撞|ffa6cb8使用独立reverse key；保留探针失败|
|a56a6c5，库e6afadad升级|1 failed/0 errors/26；probe已种共电话档案，重复提示测试错误假设候选首项|5591b0b断言候选包含，而非首项；随后26/26 PASS|
|Firefox首次启动|现有本地GTK动态库未在进程LD_LIBRARY_PATH，浏览器尚未启动|仅添加既有process-local library path；不安装系统依赖、不关sandbox|
|Firefox20261011T171550988308，5ba20bd|FAIL，完成18项后只读用户页面没有form/CSRF节点；测试JS读取null|5e4b309浏览器负向请求先到真实access页面取得CSRF；之后cf87068下20/20 PASS；原summary及5图保留|
|库939a7f4e初装后probe guard|产品尚有未提交调整，runner拒绝执行；没有绕过检查/接管库|提交cf87068，升级27/27、probe7/7、翻译222/222、Firefox20/20 PASS|
|最终库54a78616第一次install guard|刚SIGTERM本次preview，18106尚在退出；runner在创建库前拒绝占用端口|退出后同唯一未创建名字正常新建；未停止其他服务|
|b8fa410产品/246fbba测试，最终库54a78616|新增default context/附件改挂及允许HMAC下载审计保护；最终初装30/30，升级28/28，真实并发7/7，Firefox20/20|本次固定交付；真实未来业务仍NOT_RUN|

上表guard及浏览器启动前失败没有Odoo actions条目；如实单列。其余Odoo动作有时间/提交/退出码和日志SHA。早期测试26/27项与最终28项是代码逐步补充，不能相加为独立覆盖率。两个底座测试只在fresh install加入，不把30项都称作S04测试。浏览器PASS尝试与FAIL尝试分目录长期保留。

截图人工复核在54a78616库发现关系/到店两个动态按钮仍为英文：这些表达式字符串未被原生翻译导出收录，所以222/222只能证明已提取词条，不能证明全部可见文字。eb60775改为两个静态可提取按钮并补中文；890e1e5增加2项真实Firefox中文检查。本次最终固定版本更换为product eb607750a4b35885f37acfb07d504f758b877b73 / test 890e1e51000bb959e895426bf5b82a83028b3098，并重新新建fc410608库执行完整install/probe/upgrade/export/Firefox。此前54a78616的probe/隔离/翻译证据移入attempts子目录，浏览器原目录保留；最终结果以final文件为准。

最终Firefox在fc410608库/890e1e5完成21项功能检查（含中文2项）后，零pageerror检查失败；该次summary及5图保留在20261011T173610090501。原脚本仅收集错误字符串，失败日志未输出详情，因此不冒称已证实具体原生错误原因。a35af92改用原生支持的redirect=/ydental/access登录，避免启动原生webclient后立即导航离开，并将潜在错误详情仅输出私有日志、公开summary记录数量；未忽略pageerror或取消任何检查。在同库重放22/22 PASS、pageerror_count=0。为固定完整测试证据，最终再新建独立S04库按a35af92运行全部验证；产品仍为eb60775，测试变动只涉及Firefox入口/诊断。
