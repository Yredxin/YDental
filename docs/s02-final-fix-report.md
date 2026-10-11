# S02最终小修交付与复核申请

唯一修正依据为 [GPT-REVIEW 6110056678](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110056678) 与本会话用户授权。原四项修正在 `9e581b4` 已通过独立复核；本次仅修 FINAL-BLOCKER：归档资源的既有 placement 不应被几何约束冻结。没有重做公共权限、父级恢复、rect points、能力边界或平面编辑器。

沿用分支 `codex/s02-space-r1-20261011`，起点 `9e581b413833f356e8e868f388f04c5f9d65f5f4`，开始工作区干净；Git 根 `/home/redxin/code/odoo/odoo-sd/code/sd-addons`，origin Yredxin/YDental。产品修正固定 **`9653ca2d25fde16ac791dd499197703c18ef18ce`**，只改 `ydental_space/models/ydental_space_item.py`；测试固定 **`00c76b55f205ee032534b7a3b8cda27bd1d7764d`**，后续仅新增两个测试方法。所有最终执行均固定该测试提交；最终文档/证据提交不改变实现。

## 修正行为与实际回放

原 `_check_item` 每次几何/active/关系变化都要求 resource.active，导致 resource 已归档的旧 item 不能移动，station 的几何同步也被回滚。本次保留几何有界/尺寸正值、有效 floor 和兼容归属约束，把资源有效性限定在已有 `_check_space_change` 的新建、显式资源赋值、active=True入口。hook 在授权、版本和锁之后执行，create 后验证、write 前验证，无 context 豁免或前端依赖；失败同事务回滚。窄范围 sudo 只读取固定参照资源的 active，与原约束参照完整性检查同目的，不增加调用者权限。详细生命周期见 [补充契约](s02-final-fix-contracts.md)。

|流程/功能|预期|模型与真实HTTP实际结果|
|---|---|---|
|归档已有 resource|既有 item/station 及引用继续存在，历史可显示|PASS；item仍active；HTTP固定ID SVG读取200|
|旧 station 移动/缩放/旋转|成功同步原 item，稳定ID不变|PASS；station改到(80,100)、180×140、30°；原item变为(80,100)、120×100、30°；HTTP使用原平面 action_save_geometry|
|旧 item 直接几何写|成功，原资源引用保持|PASS；改为(95,115)、130×110、45°|
|创建新 item 使用 inactive resource|拒绝，包括active=False新记录|PASS；模型与真实RPC均拒绝，未留下新记录|
|旧 item 改绑另一 inactive resource|拒绝，原引用不变|PASS；两种测试均拒绝|
|先归档 item，再恢复|resource仍inactive时拒绝|PASS；action_unarchive及直接write(active=True)均拒绝，item仍inactive|
|先恢复 resource，再恢复 item|恢复成功，原ID/引用不变|PASS；最终item active，item/station集合与开始完全相同，无删除、无station副本|

新增方法：`TestSpace.test_final_archived_resource_keeps_historical_geometry_editable` 和 `TestSpaceHTTP.test_http_final_archived_resource_keeps_historical_geometry_editable`。测试使用原独立 writer/current-store 受控会话，HTTP真实登录并经CSRF选店、JSON RPC和SVG路由；没有在业务断言中使用超级用户绕过权限。测试root仅建立/观察合成夹具。

## 隔离运行和测试结果

全新库 **`ydental_s02_test_20261011143156_035ef345`**，OID **208233**，创建时不存在；端点127.0.0.1:5432/odoo，集群7694897083368259627。沿用原runner校验创建记录/OID、独立配置/data_dir/日志、精确dbfilter、127.0.0.1:18104、cron0、SMTP127.0.0.1:1及进程外发限制。没有接管/修改历史库、业务库、旧18102/18103预览、核心或依赖。

核心固定 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地声明20.0 fork；不冒称已核对同SHA官方上游。Python为核心 `.venv/bin/python`。本次创建记录、配置哈希、动作退出码及私有日志哈希见 [runtime-history](evidence/s02-final-fix-20261011/runtime-history.json)。原始日志、随机访问凭据只在本机私有文件，仓库与Issue仅合成/脱敏证据。

|验证|结果|实测口径/证据|
|---|---|---|
|全新 install|PASS，exit0，0 failed/0 errors/27|18模型+7真实HTTP=25项；另2个原生HOOT入口因无匹配模块资源直接返回，不宣称完整原生JS套件运行|
|同库 upgrade|PASS，exit0，0/0/25|全部18模型+7真实HTTP再次执行|
|原四项修正回归|PASS|独立集团无选店/无space授权、父级active恢复、rect攻击/shape切换、inactive能力保留/清理/新关联拒绝，原方法完整保留|
|T01—T10当前适用范围|PASS|原树/稳定ID、几何、能力、SVG攻击/上传、只读/异店权限、版本回滚、归档/归属、依赖、最近报到祖先及合成in-use、未接入状态/公共私有资源|
|guard|PASS，5 tests，exit0|原隔离保护，无数据库写入；[guard-final](evidence/s02-final-fix-20261011/guard-final.json)|
|浏览器关键平面及原公共角色路径|PASS，21 checks，exit0|沿用未改的Firefox155工具、默认安全设置，真实并发恰好1成功/1冲突、保存/更名/画图/拖放/上传/只读/切店403及独立集团原生表单；[browser-final](evidence/s02-final-fix-20261011/browser-final.json)|
|翻译来源核对|PASS，135条完整|未新增文案，原生导出与中文词条/引用完整匹配；[translations-final](evidence/s02-final-fix-20261011/translations-final.json)|
|真实排期/患者任务/队列/租约联调|NOT_RUN|属于尚未启用S03/S06，合成保护不代替下游联调|
|生产发布/生产回滚/人工效果验收|NOT_RUN|未获本批启用，不代用户宣布验收|

实际命令（库现已存在，runner会拒绝再次install，不重置）：

```bash
../.venv/bin/python scripts/s02.py install --db ydental_s02_test_20261011143156_035ef345 --port 18104
../.venv/bin/python scripts/s02.py upgrade --db ydental_s02_test_20261011143156_035ef345 --port 18104
../.venv/bin/python scripts/test_s02_guard.py
../.venv/bin/python scripts/s02.py export --db ydental_s02_test_20261011143156_035ef345 --port 18104
../.venv/bin/python scripts/s02.py probe --db ydental_s02_test_20261011143156_035ef345 --port 18104
../.venv/bin/python scripts/s02.py serve --db ydental_s02_test_20261011143156_035ef345 --port 18104
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python scripts/s02_browser.py --db ydental_s02_test_20261011143156_035ef345 --port 18104 --evidence s02-final-fix-20261011
```

浏览器/字体仅复用既有进程本地二进制，没有安装系统依赖或执行S00工具。归档后的移动生命周期由新增模型和真实HTTP直接验证，浏览器回归原关键平面路径；不把正常资源浏览器路径冒称为归档资源浏览器专项实测。

最终合成截图：[01平面](evidence/s02-final-fix-20261011/browser-attempts/20261011T143514869875/01-writer-floor.png)、[02保存](evidence/s02-final-fix-20261011/browser-attempts/20261011T143514869875/02-saved-floor.png)、[03绘制/拖放](evidence/s02-final-fix-20261011/browser-attempts/20261011T143514869875/03-drawing-and-drop.png)、[04安全上传](evidence/s02-final-fix-20261011/browser-attempts/20261011T143514869875/04-private-resource-upload.png)、[05只读](evidence/s02-final-fix-20261011/browser-attempts/20261011T143514869875/05-readonly-floor.png)、[06独立集团公共资源表单](evidence/s02-final-fix-20261011/browser-attempts/20261011T143514869875/06-group-only-common-resource.png)。本批install/upgrade/browser首次执行均通过；所有动作哈希和浏览器attempt仍单独保留。

## 证据、安全和边界

`9e581b4`及此前通过证据/失败链全部保留。本次证据只新增 `docs/evidence/s02-final-fix-20261011/`，旧 `docs/evidence/s02/`、`s02-rework-20261011/`、旧报告/契约不改动。没有迁移、清理旧库、物理删除、复制station或重绑历史；不修改SVG、安全路由、static/、能力计算、公共/私有权限或S01。成功配置审计与版本仍由原抽象层处理，没有资金/库存等副作用。

依据已读 odoo-guidelines/odoo-security 做作者定向自查：唯一产品差异是固定资源active验证时机，公共RPC入口/ACL/公司/门店域/版本锁/参数白名单保持，未新增路由、SQL、任意模型sudo、context跳过或导出旁路。这不是独立复核结论；申请复核该固定产品及最终证据。

Project无写入，#26执行状态保持返工，原生Status保持Todo、Issue保持OPEN，未改workflow，未创建/合并PR。新预览仅本机18104；若停止，只能核对本批PID与独立配置后停止本批进程，并保留库和证据，不能把旧代码直接接管新库。不进入S03，不生产发布；发布本申请后完整读回并停止。
