# [CODEX] S00-B浏览器截图补交

任务：YD-N1 R1 / [#24](https://github.com/Yredxin/YDental/issues/24)，依据[总计划 #23](https://github.com/Yredxin/YDental/issues/23)及用户本次明确授权，仅补真实浏览器 UI 自动验证与截图。当前正文及有效评论于2026-10-11读取；承接[GPT对49beda1的通过复核](https://github.com/Yredxin/YDental/issues/24#issuecomment-6106835823)，不重做已通过的安装、升级、HTTP、PDF内容或隔离测试。

**浏览器UI验证PASS（Firefox）；Chromium sandbox兼容性仍BLOCKED。**

## 固定版本与边界

- 分支：`codex/s00-b-r1-20261011`；接续基线：`49beda1afed3a81ce79fcee4ec83e46a758a031d`，开始时工作区干净。
- 本轮实际被测提交：`0787ec848579c70b0a44895e3d6a5586ec0f4d74`；最终交付为本报告、PNG及JSON所在的固定提交，完整SHA由#24同名补交评论提供。被测提交之后仅补文档与证据，没有修改addon或测试脚本。
- 原addon实现保持`f957313bf31f836965ea310ff6bcf0a18216e781`的内容；未改业务需求、核心、odoo-12、业务库/配置/服务、Project或用户安全配置。
- 沿用唯一当前隔离库`ydental_s00b_test_20261011073303_8137af81`、`http://127.0.0.1:18079`；不创建/重建数据库。运行器发现旧预览PID记录，首次serve拒绝退出2；确认`/proc/318644`不存在后仅归档本批PID文件，再通过原护栏恢复同库预览。
- 凭据只读本库运行目录中本机所有、非symlink、0600的`access.json`；浏览器profile和下载文件留本地私有目录。四个角色各有独立context，实际填写原生登录表单，登录页不截图；浏览器请求仅允许精确预览origin，service worker被阻止以维持拦截边界。

## 需求完成情况与实际回放

|本次范围|结果|实际回放与证据|
|---|---|---|
|A authorized_zh|PASS|真实登录→/ydental 200→h1牙科及中文欢迎语；无P00/基线就绪旧文案；原生应用菜单唯一牙科项，实际点击回入口；browser-authorized-zh.png、browser-menu-zh.png|
|B authorized_en|PASS|独立context真实登录→英文Dental/Welcome页面200；原生菜单唯一Dental项，实际点击回入口；browser-authorized-en.png、browser-menu-en.png|
|C unauthorized|PASS|独立context登录后/ydental 403；没有牙科页面main；保存真实Forbidden拒绝页browser-unauthorized.png|
|D portal|PASS|另一独立context同样403；保存真实拒绝页browser-portal.png|
|E A4按钮|PASS|中文页面实际点击→download事件→响应200→下载文件.pdf且以%PDF-开头，16500 bytes；PDF内容未重验|
|E 窄纸按钮|PASS|实际点击→download事件→响应200→PDF文件，16511 bytes；PDF内容未重验|

两个拒绝页哈希相同是同一错误模板的真实输出；它们由不同context、不同角色在各自记录时间重新截图，未复用文件。入口是当前最小模板的朴素页面，没有在本轮加美化或未来业务。

菜单验证使用原生`/odoo/action-base.action_res_users_my/<合成用户ID>`，关闭偏好对话框且不保存，再打开原生应用菜单。直接`/odoo`会自动执行首个牙科URL动作而跳回入口，因此不能用它等待菜单；本轮没有模拟/注入菜单或改核心。

## 测试结果与浏览器记录

最终运行：2026-10-11 08:03:21—08:03:34 UTC；**6项，6 PASS，0 FAIL，退出0**。Firefox155.0 / Playwright1.63.0 / viewport1280×900 / headless。每项URL、最终HTTP状态、title、console error、pageerror、截图SHA256、被测完整commit及UTC时间见[逐项运行记录](evidence/s00-b/browser-ui.json)。额外原生菜单截图及哈希同在其中。

授权页面title实际为`Dental | YDental`（中文角色的h1/正文/菜单为中文）；拒绝页title为`403 Forbidden`。所有pageerror为空。两个授权context记录`Service worker registration failed, error: JSHandle@object`，来自测试主动阻止service worker的隔离设置；页面、菜单及下载断言均通过，没有把该console error隐藏或写成无错误。

|浏览器路径|状态|实测证据|
|---|---|---|
|Chromium153.0.8010.12，build1243|BLOCKED|`chromium_sandbox=True`；No usable sandbox；TargetClosedError，子进程SIGTRAP，exitCode=null；本轮实际重试，私有日志SHA见JSON。版本来自Playwright安装元数据，不能声称完成Chromium页面验证|
|Firefox155.0，build1543|PASS|默认安全启动，没有sandbox禁用参数、环境变量或偏好；完成全部6项|
|WebKit|NOT_RUN|Firefox已启动并通过，无需继续fallback；脚本保留Firefox启动失败时尝试WebKit的路径|

|#24 TC|本轮结果/范围|既有结论|
|---|---|---|
|S00-T02|PASS：菜单唯一入口浏览器补证；安装升级NOT_RUN|49beda1的安装升级结果保留|
|S00-T03|PASS：授权中文/英文、无权内部、portal真实浏览器；匿名NOT_RUN|原HTTP及匿名结果保留|
|S00-T04|PASS：两个真实按钮下载；PDF内容/权限全矩阵NOT_RUN|原中文A4/窄纸及下载鉴权结果保留|
|S00-T08|PASS：中英文页面/原生菜单；时间和编号NOT_RUN|原探针结果保留|
|S00-T05|BLOCKED，独立项|未读取/修改Project，原专项三表和阻塞不变|
|S00-T01/T06/T07/T09|NOT_RUN：本轮不重做全量核查/隔离/契约测试|原报告与复核继续有效|

## 本地依赖与复现

只增补`.local/s00-b-deps`中的Playwright Firefox下载和四个Ubuntu包解包：libgtk-3-0t64、libgtk-3-common、libepoxy0、libwayland-cursor0。均为`apt-get download`后`dpkg-deb -x`，没有apt安装、install-deps或with-deps。沿用已有CJK字体，复制至本地Firefox的`firefox/fonts/`；最终浏览器使用默认fontconfig和该局部bundled字体。PDF进程字体配置不变。下载来源、包版本、SHA256、浏览器/字体哈希及恢复记录见[browser-environment.json](evidence/s00-b/browser-environment.json)。未使用no-sandbox，未修改AppArmor、user namespace或主机策略。

在原有本地验证依赖目录可用时：

```sh
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python -m playwright install firefox
cp .local/s00-b-deps/fonts/NotoSansCJKsc-Regular.otf \
  .local/s00-b-deps/browsers/firefox-1543/firefox/fonts/
# GTK等包按environment记录仅下载/局部解包，不运行系统安装命令。
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python scripts/s00_b_browser.py \
  --db ydental_s00b_test_20261011073303_8137af81
```

脚本先核对固定端点/cluster/创建记录/精确端口/config哈希/预览PID，再访问回环；不提供安装升级、删库或接管其他库的操作。先提交脚本才能运行；不会把测试后改码视为已测。

## 失败与补交链

- `8a00eb2`：首次6项中4 PASS、2 FAIL，退出1；菜单因默认跳转超时，字体在自定义fontconfig环境未正常显示。脱敏原JSON和四张失败截图长期保留在[browser-attempts/8a00eb2](evidence/s00-b/browser-attempts/8a00eb2/README.md)，路径归档映射及原哈希注明，不充作最终截图。
- `88abd4f`：改用原生偏好入口后，发布秘密检查把普通偏好cookie值也纳入匹配，安全停止退出2，没有发布运行JSON；[失败摘要](evidence/s00-b/browser-attempts/88abd4f.json)保留。修正为匹配会话/鉴权/token类cookie，并完整重跑。
- `0787ec8`：最终真实重跑6/6、退出0，六张当前PNG全部由该次运行产生；逐张视觉检查通过，结合DOM可见文本、密码字段及PNG字节检查，未见密码、cookie、token、登录凭据或患者资料。没有人工制作/后期编辑截图。原Chromium阻塞记录不删除。

## 用户查看效果

无需用户人工截图；直接查看本次四张页面和两张菜单截图即可评估当前效果。若需本机交互复现（非补证前提）：

1. 在Ubuntu本机打开`http://127.0.0.1:18079/ydental`。
2. 从本地0600的access.json读取authorized_zh凭据登录，应见牙科及中文正文。
3. 点击A4/窄纸入口，应下载PDF；内容仍对照原S00-B样张证据。
4. 用新独立会话登录authorized_en，应见Dental及英文正文。
5. 分别用unauthorized和portal独立会话访问入口，应403。

凭据不贴GitHub。预览仍仅本机回环；没有调整业务8069服务。测试代理已完成截图与检查，用户只需作效果确认，不承担截图搬运工作。

## 数据、动作、回滚及复核申请

本轮只改浏览器脚本与证据文档，无新增业务字段/动作/迁移。浏览器操作为合成账号登录、读入口、读原生偏好并关闭、读菜单及下载固定合成PDF；没有保存偏好、患者、费用、库存、资金或正式文书快照。会话及原生资源缓存是隔离库内正常运行产生的技术数据，不冒称S01审计实现。

回滚仅在当前分支revert浏览器脚本提交；证据与失败历史继续保留。局部浏览器及库文件可在本批进程结束后移除，无系统包卸载或核心回滚。仅在确需结束预览时核对本批serve.pid及精确config，再结束本批进程，不清库、不停止其他服务。

申请GPT复核本次固定截图补交与用户效果确认。没有需要系统安装/服务变更的新增授权事项；Chromium兼容性仍BLOCKED，Firefox成功不改变原HTTP/PDF结论。Project/T05继续独立BLOCKED，整个S00未完成。交付评论写回读回后停止，不关闭#24、不合并、不进S01、不生产发布。
