# 交付验收申请｜YD-N1 R1｜S02｜空间基础配置

任务与用户启用来源：本会话用户明确启用 S02、禁止扩大到 S03。需求仅为 [#23](https://github.com/Yredxin/YDental/issues/23)、[#26](https://github.com/Yredxin/YDental/issues/26) 当前正文和有效评论；前置为 [#25 最终 S01 收口](https://github.com/Yredxin/YDental/issues/25#issuecomment-6108974493)。已先发布并完整读回 [开工条件检查](https://github.com/Yredxin/YDental/issues/26#issuecomment-6108999828)，再实施。来源正文修订时间/摘要见 [requirement-sources.json](evidence/s02/requirement-sources.json)。未用撤销计划或上一 Codex 聊天补需求。

基线 `37ccd3af4c6af390506eb9229e2f1cc145e951b9`；最终产品实现 `a128ff373836a35bf1462060ec9802dac0eb1953`；产品、测试与浏览器最终固定提交 **`0b87c1c587a3639793124314e75c3a01747cb1ef`**；分支 `codex/s02-space-r1-20261011`。后续文档/证据提交不改变实现。没有创建/合并 PR、修改 Issue/PR 状态、Project 字段或 workflow，没有生产发布。

S01 复用固定产品 `740c42bbf611baa8713758fba38c1411d6b966c9`、最终测试 `f1ce22df7002e40391ce16fd59093d60c4522b2e` 和上述基线文档；不重做 S00/S01。实际核心 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`、本地声明20.0的 fork；不宣称已核对同 SHA 官方上游。使用核心 `.venv/bin/python`。

实际环境：独立 Git 根 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`，origin Yredxin/YDental，初始干净；父根既有未跟踪 AGENTS.md 保留。只新建 S02 合成库；交付库 `ydental_s02_test_20261011131713_c4170b44`，OID182918，实际端点127.0.0.1:5432/odoo，集群7694897083368259627。独立配置/data_dir/日志、精确 dbfilter、127.0.0.1:18102、禁 cron、SMTP 黑洞和进程级外发限制均由 runner 核对。未改核心、旧服务、业务库、历史库或系统依赖。元数据/命令退出码/日志摘要见 [runtime-history.json](evidence/s02/runtime-history.json)；原始日志和访问凭据仅本机私有保存。

## 需求完成情况

|R或功能|完成/部分/未做|实现位置|边界|
|---|---|---|---|
|R06/R08/R10 楼层、嵌套区域、稳定四类工位|完成|ydental_space/models；原生 forms/lists|同店同层、稳定 id、归档保历史|
|矩形/多边形、拖放、移动、大小、方向、缩放、保存|完成|static/src/plan|基础编辑；高级多选、对齐、图层、撤销重做未做且明确后置|
|S01 能力字典、资源并集加增减、区域服务发现|完成|station/area/resource|各设备不反向获得区域并集；无医生指定或旧分配算法|
|公共/私有必要资源及安全上传|完成|resource、svg.py、鉴权 SVG GET|公共写需集团权；私有本店；只存安全结果|
|最近报到祖先、前缀/过号配置、变更保护|部分|area、_check_space_change、统一锁|空间归属/合成在用拒绝已测；真实任务迁移/租约/队列联调 NOT_RUN，归 S03/S06|
|只读状态、主题、中文与错误文案|完成|plan、zh_CN.po|明确尚未接入；没有模拟实时状态|
|S03/S05/S06 边界|完成接口文档；未实现其业务|[工程契约](s02-contracts.md)|不建人员排期、容量、预约、患者队列或未来空模块|

原生资源和开源候选核对见工程契约末节：原生 resource.resource 为带日历的 Human/Material 资源，未包含诊所几何/报到/图标控制；复用原生 ORM/web/Owl 与 S01。只读评估的 OCA resource_booking 和 WOOWTECH internal_booking 均非直接适配本锁定底座和范围的完整方案，未安装/复制，未引入 OCA。

## 流程实际回放

|示例|虚拟前提/操作|预期|实际及证据|
|---|---|---|---|
|S02-F1|A店二楼、诊疗父区/诊室甲、两椅、影像全景/CBCT、药房/收费；刷新|两椅能力分别洁牙和洁牙/补牙；两影像设备能力隔离；收费不叫号|模型 T03/T10 + 浏览器初始配置读回、截图01；另真实画矩形/多边形及拖放生成工位和关联图形，截图03|
|S02-F2|更名、改大小并移动既有椅；原生表单保存；只读直接 RPC；文件上传|原 ID/引用不变；只读拒绝；安全 SVG 存储，攻击输入拒绝|T02/T04/T05 + 浏览器布局保存/原生更名/文件上传/切店403；截图02/04/05|
|S02-F3|同构父子区域树：子区未独立报到→合成在用标记→开启独立报到→解除标记重试|最近祖先唯一；在用拒绝、回滚；解除后改为子区|T09 服务端合成保护通过并核对参数审计；没有建立真实患者队列，不声称真实影像任务或租约联调通过|

全部最终执行固定于上述 `0b87c1c...`；完整浏览器配置读回、稳定 ID/坐标前后、SVG结果摘要与截图哈希见 [browser-final.json](evidence/s02/browser-final.json)。

### 区域、工位、能力与资源归属

|区域ID/父区|用途/报到|工位稳定ID/名称|能力|最近报到区|资源摆放/归属|
|---|---|---|---|---|---|
|11 Treatment / 根|care / True|—|Cleaning, Filling|11|本店A / floor5|
|12 Imaging / 根|exam / True|9 Panorama|Panorama|12|item7→resource2；图形公共、摆放本店|
|12 Imaging / 根|exam / True|10 CBCT|CBCT|12|item8→resource2；图形公共、摆放本店|
|13 Pharmacy / 根|pharmacy / True|11 Pharmacy desk|—|13|item9→resource3；图形公共、摆放本店|
|14 Settlement / 根|settlement / False|12 Settlement desk|—|无|item10→resource4；图形公共、摆放本店|
|15 Waiting / 根|waiting / False|—|—|无|本店A / floor5|
|16 Room A / 11|care / False|7 Chair 1|Cleaning|11|item5→resource1；图形公共、摆放本店|
|16 Room A / 11|care / False|8 Chair 2|Cleaning, Filling|11|item6→resource1；图形公共、摆放本店|

公共内置资源：chair/imaging/pharmacy/settlement/door/wall/waiting，store为空，由集团维护；预览另有本店私有候诊标记，其他店无法读取。内置图形不默认授权任何能力；示例工位能力由合成字典手动配置。资源能力并集/增加/移除优先级另外由模型 T03 验证。

### ID 与坐标前后、SVG、版本

|对象/属性|操作前|操作后|
|---|---|---|
|工位身份|7|7；原引用不变|
|工位名称|Chair 1|S02 Stable Chair 985010|
|工位坐标/尺寸/方向|(70.000, 110.000)；90.000×70.000；0.000°|(78.000, 110.000)；95.000×70.000；0.000°|
|关联图形身份/工位|item5→station7|item5→station7|
|关联图形坐标/尺寸/方向|(80.000, 135.000)；65.000×55.000；0.000°|(88.556, 135.000)；68.611×55.000；0.000°|
|区域/最近报到区|16/11|16/11|
|工位内容版本|1|4|
|真实并发保存|同一楼层版本5|1 accepted / 1 version_conflict|
|安全SVG输出|本店private resource14|140 bytes；circle；SHA-256 `8ca40eab3ba22442a92f3ced95b002b3031135bda1758f20cf3c1cacb270bec8`|

SVG 攻击矩阵：script、foreignObject、image外链、url绘制属性、onload、畸形XML、外部实体DOCTYPE、无限尺寸、无viewBox、超限、use引用均拒绝；安全上传为本机生成的100×100/viewBox圆形，不存原上传。最终输出字节数与 SHA-256 见 browser-final。两个真实 HTTP 事务同时使用同一聚合版本，恰好一个 accepted、一个 version_conflict；批量非法几何另测整笔回滚，不覆盖已保存布局。

## 测试结果

命令统一从仓库根执行，Python 为 `../.venv/bin/python`。安装、升级、翻译导出、种子和预览均通过 `scripts/s02.py`，只接受新建并有创建记录/OID的S02库。最终每项实际退出码均记录在对应证据；没有将模型测试、浏览器检查、下游联调相互代替。

|TC|PASS/FAIL/BLOCKED/NOT_RUN|命令/角色与实测范围|测试数/退出码|证据|
|---|---|---|---|---|
|T01|PASS|test_t01 + polygon；writer 浏览器画图/保存/刷新|包含于15模型/HTTP和15浏览器检查；0|tests/test_space.py、browser-final|
|T02|PASS|test_t02；writer 原生更名/几何修改，关联图形跟随|同上；0|前后读回、配置审计、截图02|
|T03|PASS|test_t03；区域合并发现但设备保留自身集合|同上；0|模型断言 + 初始配置读回|
|T04|PASS|test_t04 + 两个 HTTP 方法；reader/其他店/伪造范围/public附件|同上；0|真实 HTTP + 浏览器403、只读RPC拒绝|
|T05|PASS|test_t05、binary_upload；11攻击类别及上传负例，writer 原生文件控件|同上；0|safe_svg_output + 截图04|
|T06|PASS|test_t06；旧版本、全回滚、两真实并发 HTTP 事务|同上；0|concurrent_saves + 模型断言|
|T07|PASS|test_t07；引用工位禁删可归档，错店/归属修改拒绝|同上；0|模型断言|
|T08|PASS|install、upgrade；只依赖已交付 ydental_access/web|安装汇总17、升级15；均0；实质S02测试各15|runtime-history最终库记录|
|T09 空间及合成钩子|PASS|test_t09；唯一最近祖先、合成在用拒绝、参数前后审计|包含于15；0|模型断言|
|T09 真实任务/租约/排期|NOT_RUN|S03/S06尚未实现、未获启用|未执行|下游接口契约；不静默算通过|
|T10|PASS|test_t10；公共集团正向/普通反向、私有隔离、未接入状态；原生导出核对133词|15模型/HTTP、15浏览器、133翻译条目；0|翻译摘要、截图01/05|
|隔离保护|PASS|scripts/test_s02_guard.py；无数据库写入|5；0|guard-final.json|
|安全自查|完成|odoo-security + 后端/前端适用规则|非独立测试数|[安全复核](s02-security-review.md)|

本机实际命令（下列 install 已在该名称不存在时完成；现已存在，runner 会拒绝再次 install，不重置或接管）：

```bash
../.venv/bin/python scripts/s02.py install --db ydental_s02_test_20261011131713_c4170b44 --port 18102
../.venv/bin/python scripts/s02.py upgrade --db ydental_s02_test_20261011131713_c4170b44 --port 18102
../.venv/bin/python scripts/s02.py export --db ydental_s02_test_20261011131713_c4170b44 --port 18102
../.venv/bin/python scripts/test_s02_guard.py
```

浏览器先用 runner 的 probe/serve，仅用记录的隔离库；不关闭默认安全控制，不导出 cookie/token：

```bash
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python scripts/s02_browser.py --db ydental_s02_test_20261011131713_c4170b44 --port 18102
```

路径中的 s00-b-deps 只是复用已存在的进程本地浏览器/字体二进制，没有执行 S00工具或接管其库。隔离工具缺少这些依赖时停止，不自动安装。

安装的 Odoo 汇总17包含13个本批模型方法、2个本批真实 HTTP 方法和2个原生跨模块 HOOT 入口；后者没有匹配本模块单测资源而直接返回，**不宣称完整原生 JS 测试套件已运行**。真实交互另由默认安全设置的 Firefox155执行15项浏览器检查。升级汇总15就是本批13+2。

### 保留失败与补交

已进入运行的所有早期 install/upgrade 退出及日志哈希保留在 runtime-history；另有一次本批预览尚未退出时的新安装尝试被占端口保护提前拒绝，未创建库或停止其他服务，等本批进程退出后才重新安装。浏览器每次结果和已生成的合成截图保留在 browser-attempts。早期失败包括实际20.0配置API差异、测试角色/范围绑定、BinaryValue文件语义、翻译引用行号、测试字典与预览冲突、Owl3 props/ref/表达式/输入事件、原生表单未发送未改版本、浏览器保存读回时机、draggable枚举属性、受保护 action 元数据读权限。

`a128ff3` 首次全新库浏览器14项业务检查通过，末尾发现 pageerror；当时结果仅存异常类型，不能判定具体原因，保留 FAIL。补交 `6bce7c1` 同库15项通过；最终工具补充安全的错误首行保存、登录原生导航初始化等待及配置前后读回，重新全新库执行。不会用补交抹除失败，不将时序调整宣称为已定位产品根因。最终证据见 browser-final；如果复现新的 pageerror，工具仍失败并保存脱敏诊断。

## 字段、动作与配置

[工程契约](s02-contracts.md) 逐模型列出字段、默认、关系、原子动作、权限、失败恢复及 S03/S05/S06 锁/扩展点。标准配置使用原生表单列表；局部表单模型提交显示版本，服务器持锁比较，避免刷新版本掩盖冲突。工位、摆放图形和资源定义为独立身份；删除只归档。

`ydental_space.svg_max_bytes=1048576` 为本批明确测试技术初值，允许配置1024–4194304；生产值未批准。`ydental_missed_limit` 初值0仅未发布配置；测试写入3只验证保存/审计，不构成生产N=3批准。队列日期、运行排序、有效任务、预约容量均未在本批实现。

## 用户效果验证

入口为本批隔离预览 `http://127.0.0.1:18102/odoo`，仅本机；合成集团、空间读写、空间只读三角色，随机访问凭据本机0600文件保存，仓库/Issue不附凭据。需要恢复预览时使用 runner serve，先核对同一创建记录和端口，不能接管旧服务。

1. 读写角色登录，在门店与员工工作区选择合成A店；顶部显示当前店。
2. 诊所空间→楼层→新建楼层并填写门店/尺寸；保存获得稳定 ID。
3. 进入平面图，选择矩形工具拖画区域；切多边形工具点三个以上角并完成；刷新仍在。
4. 选择区域，拖入公共牙椅/影像/药房/收费资源；形成工位与关联图形，收费不可叫号。
5. 选中工位，修改宽高/方向或拖动；进入“名称、区域和能力”原生表单，配置名字、类型、区域及能力增减；保存后 ID 不变。
6. 保存布局并刷新，核对坐标/能力；两个编辑页面并发保存旧版本应提示冲突，刷新后明确重试。
7. 资源库维护本店私有图形，使用文件控件上传简单安全 SVG；非法脚本/外链应拒绝且旧结果保留。
8. 只读角色查看同图，保存禁用；直接接口仍拒绝。切换其他店后，本店私有图形无法读取。
9. 运行提示应始终为尚未接入坐诊状态；不能把图形颜色当作已接入的患者或排期状态。

实测截图：[01-writer-floor.png](evidence/s02/browser-attempts/20261011T132204985010/01-writer-floor.png)、[02-saved-floor.png](evidence/s02/browser-attempts/20261011T132204985010/02-saved-floor.png)、[03-drawing-and-drop.png](evidence/s02/browser-attempts/20261011T132204985010/03-drawing-and-drop.png)、[04-private-resource-upload.png](evidence/s02/browser-attempts/20261011T132204985010/04-private-resource-upload.png)、[05-readonly-floor.png](evidence/s02/browser-attempts/20261011T132204985010/05-readonly-floor.png)。全部为合成数据；人工用户效果确认仍待用户执行/确认。

## 数据、审计与回滚

仅新增本批空间模块/测试模块及新合成库，没有迁移业务数据；没有费款、库存或资金副作用。稳定 ID/restrict/归档保引用；工位展示更名和几何不迁移任何任务。成功配置审计记录真实 actor、前后版本/关系/能力/用途/报到/前缀/过号/几何，SVG只记安全结果摘要，不记原输入；沿用 S01 不可改审计。

回滚本机预览时先核对本批独立配置与记录 PID，停止本批进程并保留库、创建记录与证据；代码可回到固定 S01基线，用另一独立环境运行。不能把缺少新模块的旧代码直接指向已安装该模块的库，也不使用 drop/reset 清理失败历史。没有生产部署，因此没有生产数据库回滚实测；此项 NOT_RUN。后续确需迁移、恢复或生产发布须由所属授权阶段定义和验证。

未做范围：高级编辑、真实排期/容量/预约/叫号/任务/租约、S13压力目标、生产参数发布、人工效果验收；仅基础配置和早期合成保护本批交付。

## 复核申请

申请 #26 当前 S02 范围的技术复核及用户效果验收，固定到 `0b87c1c587a3639793124314e75c3a01747cb1ef` 和本次文档证据提交。只报告实际执行通过范围；不替用户宣布 S02验收通过、不关闭Issue、不修改Project、不自动开始S03。
